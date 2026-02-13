"""
send_ledger.py - v7 dedupe ledger
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import random
import re
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import keyring

UTC = dt.timezone.utc

STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_SENT = "SENT"
STATUS_FAILED_PRE_SEND = "FAILED_PRE_SEND"
STATUS_UNKNOWN_SENT = "UNKNOWN_SENT"
STATUS_SKIPPED_CONFIRM_REQUIRED = "SKIPPED_CONFIRM_REQUIRED"
STATUS_SKIPPED_AUTO = "SKIPPED_AUTO"
STATUS_SKIPPED_DUPLICATE_IN_RUN = "SKIPPED_DUPLICATE_IN_RUN"

OVERRIDE_KIND_REQUEST_KEY = "request_key"
OVERRIDE_KIND_RECIPIENT = "recipient"

DEFAULT_CREDENTIAL_SERVICE = "見積依頼スキル"
IDEMPOTENCY_SECRET_PREFIX = "idempotency_secret_"
RECIPIENT_SALT_PREFIX = "recipient_hash_salt_"
RECIPIENT_SALT_VERSION = "v1"


@dataclass
class ReservationResult:
    acquired: bool
    reason: str
    lock_row: Optional[Dict[str, Any]] = None


@dataclass
class OverrideDecision:
    allowed: bool
    source: str
    trace: List[str]


class SendLedger:
    def __init__(
        self,
        ledger_path: str,
        retention_days: int = 90,
        busy_timeout_ms: int = 15000,
        backoff_attempts: int = 5,
        credential_target_name: Optional[str] = None,
    ):
        self.input_path = Path(ledger_path)
        self.sqlite_path = (
            self.input_path.with_suffix(".sqlite3")
            if self.input_path.suffix.lower() == ".jsonl"
            else self.input_path
        )
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.retention_days = max(1, int(retention_days))
        self.busy_timeout_ms = max(1000, int(busy_timeout_ms))
        self.backoff_attempts = max(1, int(backoff_attempts))
        self.credential_service = credential_target_name or DEFAULT_CREDENTIAL_SERVICE

        self.conn_main = self._create_conn(full_sync=False)
        self.conn_sent = self._create_conn(full_sync=True)
        self._init_schema()

    def _create_conn(self, full_sync: bool) -> sqlite3.Connection:
        conn = sqlite3.connect(
            str(self.sqlite_path),
            timeout=max(1, self.busy_timeout_ms // 1000),
            isolation_level=None,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(f"PRAGMA synchronous={'FULL' if full_sync else 'NORMAL'};")
        conn.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms};")
        return conn

    def _init_schema(self) -> None:
        schema = [
            """
            CREATE TABLE IF NOT EXISTS send_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at_utc TEXT NOT NULL,
                request_key TEXT NOT NULL,
                v1_key TEXT,
                key_version TEXT NOT NULL,
                mail_key TEXT,
                run_id TEXT,
                status TEXT NOT NULL,
                recipient_hash TEXT,
                message_id TEXT,
                message_id_source TEXT,
                idempotency_token TEXT,
                idempotency_secret_version TEXT,
                sent_at_utc TEXT,
                subject_norm TEXT,
                decision_trace TEXT,
                error TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS send_locks (
                request_key TEXT PRIMARY KEY,
                key_version TEXT NOT NULL,
                run_id TEXT,
                status TEXT NOT NULL,
                expires_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL,
                recipient_hash TEXT,
                mail_key TEXT,
                v1_key TEXT,
                idempotency_token TEXT,
                idempotency_secret_version TEXT,
                subject_norm TEXT,
                last_message_id TEXT,
                last_message_id_source TEXT,
                last_error TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS url_alias (
                canonical_input_url TEXT PRIMARY KEY,
                last_final_url TEXT,
                final_host TEXT,
                redirect_hops INTEGER,
                final_url_fingerprint TEXT,
                resolve_status TEXT,
                resolved_at_utc TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS rerun_overrides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at_utc TEXT NOT NULL,
                expires_at_utc TEXT NOT NULL,
                kind TEXT NOT NULL,
                target_hash TEXT NOT NULL,
                reason TEXT NOT NULL,
                operator TEXT,
                host TEXT,
                command_summary_redacted TEXT
            );
            """,
            "CREATE INDEX IF NOT EXISTS idx_send_events_rt ON send_events(request_key, status, created_at_utc);",
            "CREATE INDEX IF NOT EXISTS idx_send_events_v1 ON send_events(v1_key);",
            "CREATE INDEX IF NOT EXISTS idx_send_locks_exp ON send_locks(status, expires_at_utc);",
            "CREATE INDEX IF NOT EXISTS idx_overrides ON rerun_overrides(kind, target_hash, expires_at_utc);",
        ]
        for conn in (self.conn_main, self.conn_sent):
            for sql in schema:
                conn.execute(sql)

    @staticmethod
    def _utcnow() -> dt.datetime:
        return dt.datetime.now(UTC)

    @staticmethod
    def _to_utc(ts: dt.datetime) -> dt.datetime:
        if ts.tzinfo is None:
            return ts.replace(tzinfo=UTC)
        return ts.astimezone(UTC)

    @staticmethod
    def _to_iso(ts: dt.datetime) -> str:
        return SendLedger._to_utc(ts).isoformat()

    @staticmethod
    def _parse_iso(value: str) -> Optional[dt.datetime]:
        if not value:
            return None
        try:
            return SendLedger._to_utc(dt.datetime.fromisoformat(value))
        except ValueError:
            return None

    def _with_retry(self, op, conn: sqlite3.Connection):
        for i in range(self.backoff_attempts):
            try:
                return op(conn)
            except sqlite3.OperationalError as exc:
                msg = str(exc).lower()
                if "locked" not in msg and "busy" not in msg:
                    raise
                if i >= self.backoff_attempts - 1:
                    raise
                time.sleep((0.05 * (2**i)) + random.uniform(0.0, 0.05))

    def _insert_event(
        self,
        conn: sqlite3.Connection,
        *,
        request_key: str,
        v1_key: str,
        key_version: str,
        mail_key: str,
        run_id: str,
        status: str,
        recipient_hash: str,
        message_id: str,
        message_id_source: str,
        idempotency_token: str,
        idempotency_secret_version: str,
        sent_at_utc: str,
        subject_norm: str,
        decision_trace: Sequence[str],
        error: str,
        created_at_utc: Optional[str] = None,
    ) -> None:
        conn.execute(
            """
            INSERT INTO send_events (
                created_at_utc, request_key, v1_key, key_version, mail_key, run_id, status,
                recipient_hash, message_id, message_id_source, idempotency_token,
                idempotency_secret_version, sent_at_utc, subject_norm, decision_trace, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                created_at_utc or self._to_iso(self._utcnow()),
                request_key,
                v1_key,
                key_version,
                mail_key,
                run_id,
                status,
                recipient_hash,
                message_id,
                message_id_source,
                idempotency_token,
                idempotency_secret_version,
                sent_at_utc,
                subject_norm,
                json.dumps(list(decision_trace), ensure_ascii=False),
                error or "",
            ),
        )

    def cleanup_on_batch_start(
        self,
        rerun_window_hours: int,
        unknown_sent_hold_sec: int,
        now: Optional[dt.datetime] = None,
    ) -> None:
        current = self._to_utc(now or self._utcnow())
        retention = current - dt.timedelta(days=self.retention_days)
        in_progress_cutoff = current - dt.timedelta(hours=max(24, int(rerun_window_hours)))
        unknown_cutoff = current - dt.timedelta(seconds=max(unknown_sent_hold_sec, 1800))

        def op(conn: sqlite3.Connection):
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("DELETE FROM send_events WHERE created_at_utc < ?;", (self._to_iso(retention),))
            conn.execute(
                "DELETE FROM send_locks WHERE status=? AND expires_at_utc < ?;",
                (STATUS_IN_PROGRESS, self._to_iso(in_progress_cutoff)),
            )
            conn.execute(
                "DELETE FROM send_locks WHERE status=? AND expires_at_utc < ?;",
                (STATUS_UNKNOWN_SENT, self._to_iso(unknown_cutoff)),
            )
            conn.execute("DELETE FROM rerun_overrides WHERE expires_at_utc < ?;", (self._to_iso(current),))
            conn.execute("COMMIT")

        self._with_retry(op, self.conn_main)

    def reserve_send(
        self,
        request_key: str,
        v1_key: str,
        key_version: str,
        run_id: str,
        mail_key: str,
        recipient_hash: str,
        idempotency_token: str,
        idempotency_secret_version: str,
        subject_norm: str,
        ttl_sec: int,
        decision_trace: Sequence[str],
        now: Optional[dt.datetime] = None,
    ) -> ReservationResult:
        current = self._to_utc(now or self._utcnow())
        expires = current + dt.timedelta(seconds=max(60, int(ttl_sec)))

        def op(conn: sqlite3.Connection) -> ReservationResult:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM send_locks WHERE request_key = ?;",
                (request_key,),
            ).fetchone()
            if row is not None:
                lock = dict(row)
                lock_status = str(lock.get("status", ""))
                lock_expire = self._parse_iso(str(lock.get("expires_at_utc", "")))
                conn.execute("ROLLBACK")
                if lock_status == STATUS_IN_PROGRESS:
                    if lock_expire and lock_expire > current:
                        return ReservationResult(False, "in_progress_active", lock)
                    return ReservationResult(False, "in_progress_expired", lock)
                if lock_status == STATUS_UNKNOWN_SENT:
                    if lock_expire and lock_expire > current:
                        return ReservationResult(False, "unknown_sent_hold_active", lock)
                    return ReservationResult(False, "unknown_sent_hold_expired", lock)
                return ReservationResult(False, "lock_conflict", lock)

            conn.execute(
                """
                INSERT INTO send_locks (
                    request_key, key_version, run_id, status, expires_at_utc, updated_at_utc,
                    recipient_hash, mail_key, v1_key, idempotency_token,
                    idempotency_secret_version, subject_norm
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    request_key,
                    key_version,
                    run_id,
                    STATUS_IN_PROGRESS,
                    self._to_iso(expires),
                    self._to_iso(current),
                    recipient_hash,
                    mail_key,
                    v1_key,
                    idempotency_token,
                    idempotency_secret_version,
                    subject_norm,
                ),
            )
            self._insert_event(
                conn=conn,
                request_key=request_key,
                v1_key=v1_key,
                key_version=key_version,
                mail_key=mail_key,
                run_id=run_id,
                status=STATUS_IN_PROGRESS,
                recipient_hash=recipient_hash,
                message_id="",
                message_id_source="",
                idempotency_token=idempotency_token,
                idempotency_secret_version=idempotency_secret_version,
                sent_at_utc="",
                subject_norm=subject_norm,
                decision_trace=decision_trace,
                error="",
                created_at_utc=self._to_iso(current),
            )
            conn.execute("COMMIT")
            return ReservationResult(True, "acquired", None)

        return self._with_retry(op, self.conn_main)

    def heartbeat(self, request_key: str, ttl_sec: int, now: Optional[dt.datetime] = None) -> None:
        current = self._to_utc(now or self._utcnow())
        expires = current + dt.timedelta(seconds=max(60, int(ttl_sec)))
        self.conn_main.execute(
            """
            UPDATE send_locks
               SET expires_at_utc = ?, updated_at_utc = ?
             WHERE request_key = ?
               AND status = ?;
            """,
            (
                self._to_iso(expires),
                self._to_iso(current),
                request_key,
                STATUS_IN_PROGRESS,
            ),
        )

    def clear_unknown_lock_for_manual_override(self, request_key: str) -> None:
        self.conn_main.execute(
            "DELETE FROM send_locks WHERE request_key = ? AND status = ?;",
            (request_key, STATUS_UNKNOWN_SENT),
        )

    def get_unknown_lock(self, request_key: str) -> Optional[Dict[str, Any]]:
        row = self.conn_main.execute(
            "SELECT * FROM send_locks WHERE request_key = ? AND status = ?;",
            (request_key, STATUS_UNKNOWN_SENT),
        ).fetchone()
        return dict(row) if row is not None else None

    def mark_sent(
        self,
        request_key: str,
        v1_key: str,
        key_version: str,
        run_id: str,
        mail_key: str,
        recipient_hash: str,
        message_id: str,
        message_id_source: str,
        idempotency_token: str,
        idempotency_secret_version: str,
        subject_norm: str,
        decision_trace: Sequence[str],
        sent_at: Optional[dt.datetime] = None,
    ) -> None:
        sent_ts = self._to_utc(sent_at or self._utcnow())

        def op(conn: sqlite3.Connection) -> None:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("DELETE FROM send_locks WHERE request_key = ?;", (request_key,))
            self._insert_event(
                conn=conn,
                request_key=request_key,
                v1_key=v1_key,
                key_version=key_version,
                mail_key=mail_key,
                run_id=run_id,
                status=STATUS_SENT,
                recipient_hash=recipient_hash,
                message_id=message_id,
                message_id_source=message_id_source,
                idempotency_token=idempotency_token,
                idempotency_secret_version=idempotency_secret_version,
                sent_at_utc=self._to_iso(sent_ts),
                subject_norm=subject_norm,
                decision_trace=decision_trace,
                error="",
                created_at_utc=self._to_iso(sent_ts),
            )
            conn.execute("COMMIT")

        self._with_retry(op, self.conn_sent)

    def mark_failed_pre_send(
        self,
        request_key: str,
        v1_key: str,
        key_version: str,
        run_id: str,
        mail_key: str,
        recipient_hash: str,
        idempotency_token: str,
        idempotency_secret_version: str,
        subject_norm: str,
        decision_trace: Sequence[str],
        error: str,
    ) -> None:
        current = self._utcnow()

        def op(conn: sqlite3.Connection) -> None:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("DELETE FROM send_locks WHERE request_key = ?;", (request_key,))
            self._insert_event(
                conn=conn,
                request_key=request_key,
                v1_key=v1_key,
                key_version=key_version,
                mail_key=mail_key,
                run_id=run_id,
                status=STATUS_FAILED_PRE_SEND,
                recipient_hash=recipient_hash,
                message_id="",
                message_id_source="",
                idempotency_token=idempotency_token,
                idempotency_secret_version=idempotency_secret_version,
                sent_at_utc="",
                subject_norm=subject_norm,
                decision_trace=decision_trace,
                error=error or "",
                created_at_utc=self._to_iso(current),
            )
            conn.execute("COMMIT")

        self._with_retry(op, self.conn_main)

    def mark_unknown_sent(
        self,
        request_key: str,
        v1_key: str,
        key_version: str,
        run_id: str,
        mail_key: str,
        recipient_hash: str,
        idempotency_token: str,
        idempotency_secret_version: str,
        subject_norm: str,
        decision_trace: Sequence[str],
        error: str,
        hold_sec: int,
        message_id: str = "",
        message_id_source: str = "",
    ) -> None:
        current = self._utcnow()
        expires = current + dt.timedelta(seconds=max(300, int(hold_sec)))

        def op(conn: sqlite3.Connection) -> None:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                INSERT INTO send_locks (
                    request_key, key_version, run_id, status, expires_at_utc, updated_at_utc,
                    recipient_hash, mail_key, v1_key, idempotency_token,
                    idempotency_secret_version, subject_norm,
                    last_message_id, last_message_id_source, last_error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_key) DO UPDATE SET
                    key_version = excluded.key_version,
                    run_id = excluded.run_id,
                    status = excluded.status,
                    expires_at_utc = excluded.expires_at_utc,
                    updated_at_utc = excluded.updated_at_utc,
                    recipient_hash = excluded.recipient_hash,
                    mail_key = excluded.mail_key,
                    v1_key = excluded.v1_key,
                    idempotency_token = excluded.idempotency_token,
                    idempotency_secret_version = excluded.idempotency_secret_version,
                    subject_norm = excluded.subject_norm,
                    last_message_id = excluded.last_message_id,
                    last_message_id_source = excluded.last_message_id_source,
                    last_error = excluded.last_error;
                """,
                (
                    request_key,
                    key_version,
                    run_id,
                    STATUS_UNKNOWN_SENT,
                    self._to_iso(expires),
                    self._to_iso(current),
                    recipient_hash,
                    mail_key,
                    v1_key,
                    idempotency_token,
                    idempotency_secret_version,
                    subject_norm,
                    message_id,
                    message_id_source,
                    error or "",
                ),
            )
            self._insert_event(
                conn=conn,
                request_key=request_key,
                v1_key=v1_key,
                key_version=key_version,
                mail_key=mail_key,
                run_id=run_id,
                status=STATUS_UNKNOWN_SENT,
                recipient_hash=recipient_hash,
                message_id=message_id,
                message_id_source=message_id_source,
                idempotency_token=idempotency_token,
                idempotency_secret_version=idempotency_secret_version,
                sent_at_utc="",
                subject_norm=subject_norm,
                decision_trace=decision_trace,
                error=error or "",
                created_at_utc=self._to_iso(current),
            )
            conn.execute("COMMIT")

        self._with_retry(op, self.conn_main)

    def mark_reconciled_sent(
        self,
        request_key: str,
        run_id: str,
        decision_trace: Sequence[str],
        reconciled_message_id: str,
        reconciled_source: str,
    ) -> None:
        row = self.conn_main.execute(
            "SELECT * FROM send_locks WHERE request_key = ? AND status = ?;",
            (request_key, STATUS_UNKNOWN_SENT),
        ).fetchone()
        if row is None:
            return
        lock = dict(row)
        self.mark_sent(
            request_key=request_key,
            v1_key=str(lock.get("v1_key", "")),
            key_version=str(lock.get("key_version", "v2")),
            run_id=run_id,
            mail_key=str(lock.get("mail_key", "")),
            recipient_hash=str(lock.get("recipient_hash", "")),
            message_id=reconciled_message_id,
            message_id_source=reconciled_source,
            idempotency_token=str(lock.get("idempotency_token", "")),
            idempotency_secret_version=str(lock.get("idempotency_secret_version", "")),
            subject_norm=str(lock.get("subject_norm", "")),
            decision_trace=decision_trace,
            sent_at=self._utcnow(),
        )

    def mark_skipped(
        self,
        request_key: str,
        v1_key: str,
        key_version: str,
        run_id: str,
        mail_key: str,
        recipient_hash: str,
        idempotency_token: str,
        idempotency_secret_version: str,
        subject_norm: str,
        status: str,
        decision_trace: Sequence[str],
        error: str = "",
    ) -> None:
        self._insert_event(
            conn=self.conn_main,
            request_key=request_key,
            v1_key=v1_key,
            key_version=key_version,
            mail_key=mail_key,
            run_id=run_id,
            status=status,
            recipient_hash=recipient_hash,
            message_id="",
            message_id_source="",
            idempotency_token=idempotency_token,
            idempotency_secret_version=idempotency_secret_version,
            sent_at_utc="",
            subject_norm=subject_norm,
            decision_trace=decision_trace,
            error=error or "",
            created_at_utc=self._to_iso(self._utcnow()),
        )

    def find_recent_sent(
        self,
        request_key: str,
        v1_key: str,
        window_hours: int,
        run_id: Optional[str] = None,
        now: Optional[dt.datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        current = self._to_utc(now or self._utcnow())
        window_start = current - dt.timedelta(hours=max(1, int(window_hours)))
        sql = """
            SELECT *
              FROM send_events
             WHERE created_at_utc >= ?
               AND status = ?
               AND (
                    request_key = ?
                 OR request_key = ?
                 OR v1_key = ?
               )
        """
        params: List[Any] = [
            self._to_iso(window_start),
            STATUS_SENT,
            request_key,
            request_key,
            v1_key,
        ]
        if run_id:
            sql += " AND run_id = ?"
            params.append(run_id)
        sql += " ORDER BY created_at_utc DESC LIMIT 1;"
        row = self.conn_main.execute(sql, tuple(params)).fetchone()
        return dict(row) if row is not None else None

    def is_send_blocked_precheck(
        self,
        *,
        request_key: str,
        v1_key: str,
        rerun_window_hours: int,
        run_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        送信実行前の安全判定（再評価向け）。

        Returns:
            (blocked, reason)
        """
        lock = self.get_unknown_lock(request_key)
        if lock:
            return True, "unknown_sent_hold_active"

        recent = self.find_recent_sent(
            request_key=request_key,
            v1_key=v1_key,
            window_hours=rerun_window_hours,
            run_id=run_id,
        )
        if recent:
            return True, "recent_sent_detected"
        return False, ""

    def find_recent(
        self,
        dedupe_key: str,
        window_hours: int = 24,
        run_id: Optional[str] = None,
        now: Optional[dt.datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        return self.find_recent_sent(
            request_key=dedupe_key,
            v1_key=dedupe_key,
            window_hours=window_hours,
            run_id=run_id,
            now=now,
        )

    def append_entry(
        self,
        dedupe_key: str,
        recipient: str,
        message_id: str,
        run_id: str,
        sent_at: Optional[dt.datetime] = None,
    ) -> Dict[str, Any]:
        sent_ts = self._to_utc(sent_at or self._utcnow())
        self.mark_sent(
            request_key=dedupe_key,
            v1_key=dedupe_key,
            key_version="v1",
            run_id=run_id,
            mail_key="",
            recipient_hash="",
            message_id=message_id,
            message_id_source="legacy_append_entry",
            idempotency_token="",
            idempotency_secret_version="",
            subject_norm="",
            decision_trace=["legacy_append_entry"],
            sent_at=sent_ts,
        )
        return {
            "timestamp": self._to_iso(sent_ts),
            "dedupe_key": dedupe_key,
            "recipient": recipient,
            "message_id": message_id,
            "run_id": run_id,
        }

    def load_recent_entries(self, now: Optional[dt.datetime] = None) -> List[Dict[str, Any]]:
        current = self._to_utc(now or self._utcnow())
        cutoff = current - dt.timedelta(days=self.retention_days)
        rows = self.conn_main.execute(
            """
            SELECT *
              FROM send_events
             WHERE created_at_utc >= ?
             ORDER BY created_at_utc ASC;
            """,
            (self._to_iso(cutoff),),
        ).fetchall()
        return [dict(row) for row in rows]

    def record_url_alias(
        self,
        canonical_input_url: str,
        last_final_url: str,
        final_host: str,
        redirect_hops: int,
        final_url_fingerprint: str,
        resolve_status: str,
        resolved_at: Optional[dt.datetime] = None,
    ) -> None:
        self.conn_main.execute(
            """
            INSERT INTO url_alias (
                canonical_input_url, last_final_url, final_host, redirect_hops,
                final_url_fingerprint, resolve_status, resolved_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(canonical_input_url) DO UPDATE SET
                last_final_url = excluded.last_final_url,
                final_host = excluded.final_host,
                redirect_hops = excluded.redirect_hops,
                final_url_fingerprint = excluded.final_url_fingerprint,
                resolve_status = excluded.resolve_status,
                resolved_at_utc = excluded.resolved_at_utc;
            """,
            (
                canonical_input_url,
                last_final_url,
                final_host,
                int(redirect_hops),
                final_url_fingerprint,
                resolve_status,
                self._to_iso(resolved_at or self._utcnow()),
            ),
        )

    def _get_or_create_secret(self, key_name: str, byte_length: int = 32) -> str:
        value = keyring.get_password(self.credential_service, key_name)
        if value:
            return value
        generated = secrets.token_hex(byte_length)
        keyring.set_password(self.credential_service, key_name, generated)
        return generated

    @staticmethod
    def _previous_version(version: str) -> Optional[str]:
        match = re.fullmatch(r"v(\d+)", str(version).strip().lower())
        if not match:
            return None
        number = int(match.group(1))
        if number <= 1:
            return None
        return f"v{number - 1}"

    def get_secret_versions_for_verify(self, current_version: str) -> List[str]:
        versions = [str(current_version)]
        previous = self._previous_version(current_version)
        if previous:
            versions.append(previous)
        return versions

    def build_idempotency_token(self, request_key: str, secret_version: str) -> str:
        secret = self._get_or_create_secret(
            f"{IDEMPOTENCY_SECRET_PREFIX}{secret_version}",
            byte_length=32,
        )
        return hmac.new(
            secret.encode("utf-8"),
            request_key.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def verify_idempotency_token(
        self,
        request_key: str,
        token: str,
        current_secret_version: str,
    ) -> bool:
        for version in self.get_secret_versions_for_verify(current_secret_version):
            expected = self.build_idempotency_token(request_key, version)
            if hmac.compare_digest(expected, token):
                return True
        return False

    def hash_recipient(self, recipient_email_norm: str) -> str:
        salt = self._get_or_create_secret(
            f"{RECIPIENT_SALT_PREFIX}{RECIPIENT_SALT_VERSION}",
            byte_length=32,
        )
        payload = f"{salt}:{recipient_email_norm}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def add_override(
        self,
        kind: str,
        target_hash: str,
        ttl_min: int,
        reason: str,
        operator: str,
        host: str,
        command_summary_redacted: str,
        now: Optional[dt.datetime] = None,
    ) -> int:
        if kind not in {OVERRIDE_KIND_REQUEST_KEY, OVERRIDE_KIND_RECIPIENT}:
            raise ValueError(f"Unsupported override kind: {kind}")
        ttl = max(1, min(30, int(ttl_min)))
        current = self._to_utc(now or self._utcnow())
        expires = current + dt.timedelta(minutes=ttl)
        cursor = self.conn_main.execute(
            """
            INSERT INTO rerun_overrides (
                created_at_utc, expires_at_utc, kind, target_hash, reason,
                operator, host, command_summary_redacted
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                self._to_iso(current),
                self._to_iso(expires),
                kind,
                target_hash,
                reason,
                operator,
                host,
                command_summary_redacted,
            ),
        )
        return int(cursor.lastrowid)

    def clear_overrides(self) -> int:
        cursor = self.conn_main.execute("DELETE FROM rerun_overrides;")
        return int(cursor.rowcount or 0)

    def get_override_status(self, now: Optional[dt.datetime] = None) -> List[Dict[str, Any]]:
        current = self._to_utc(now or self._utcnow())
        rows = self.conn_main.execute(
            """
            SELECT *
              FROM rerun_overrides
             WHERE expires_at_utc >= ?
             ORDER BY created_at_utc DESC;
            """,
            (self._to_iso(current),),
        ).fetchall()
        return [dict(row) for row in rows]

    def _lookup_override(
        self,
        kind: str,
        target_hash: str,
        now: dt.datetime,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        active = self.conn_main.execute(
            """
            SELECT *
              FROM rerun_overrides
             WHERE kind = ?
               AND target_hash = ?
               AND expires_at_utc >= ?
             ORDER BY created_at_utc DESC
             LIMIT 1;
            """,
            (kind, target_hash, self._to_iso(now)),
        ).fetchone()
        latest = self.conn_main.execute(
            """
            SELECT *
              FROM rerun_overrides
             WHERE kind = ?
               AND target_hash = ?
             ORDER BY created_at_utc DESC
             LIMIT 1;
            """,
            (kind, target_hash),
        ).fetchone()
        return (
            dict(active) if active is not None else None,
            dict(latest) if latest is not None else None,
        )

    def evaluate_override(
        self,
        request_key: str,
        recipient_hash: str,
        now: Optional[dt.datetime] = None,
    ) -> OverrideDecision:
        current = self._to_utc(now or self._utcnow())
        trace: List[str] = []

        key_active, key_latest = self._lookup_override(
            OVERRIDE_KIND_REQUEST_KEY,
            request_key,
            current,
        )
        if key_active:
            trace.append("override_check:request_key=matched_active")
            trace.append("override_applied:request_key")
            return OverrideDecision(True, OVERRIDE_KIND_REQUEST_KEY, trace)
        trace.append(
            "override_check:request_key=expired_or_inactive" if key_latest
            else "override_check:request_key=not_found"
        )

        rec_active, rec_latest = self._lookup_override(
            OVERRIDE_KIND_RECIPIENT,
            recipient_hash,
            current,
        )
        if rec_active:
            trace.append("override_check:recipient=matched_active")
            trace.append("override_applied:recipient")
            return OverrideDecision(True, OVERRIDE_KIND_RECIPIENT, trace)
        trace.append(
            "override_check:recipient=expired_or_inactive" if rec_latest
            else "override_check:recipient=not_found"
        )

        trace.append("override_applied:none")
        return OverrideDecision(False, "default", trace)

    def close(self) -> None:
        try:
            self.conn_main.close()
        finally:
            self.conn_sent.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

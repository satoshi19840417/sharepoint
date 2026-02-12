import datetime as dt
from pathlib import Path
import sys
import unittest
from unittest import mock


SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from scripts.mail_sender import OutlookMailSender


class MailSenderMessageIdTests(unittest.TestCase):
    def test_message_id_source_direct(self):
        sender = OutlookMailSender(dry_run=False)
        now = dt.datetime.now()

        with mock.patch.object(
            sender,
            "_poll_message_id_from_mail_item",
            return_value="<direct-id@example.com>",
        ), mock.patch.object(
            sender,
            "_get_message_id_from_sent_items",
            return_value="",
        ):
            message_id, is_fallback, source = sender._get_message_id_with_source(
                object(),
                "subject",
                "user@example.com",
                now,
            )

        self.assertEqual(message_id, "<direct-id@example.com>")
        self.assertFalse(is_fallback)
        self.assertEqual(source, "direct")

    def test_message_id_source_sent_items(self):
        sender = OutlookMailSender(dry_run=False)
        now = dt.datetime.now()

        with mock.patch.object(
            sender,
            "_poll_message_id_from_mail_item",
            return_value="",
        ), mock.patch.object(
            sender,
            "_get_message_id_from_sent_items",
            return_value="<sent-id@example.com>",
        ):
            message_id, is_fallback, source = sender._get_message_id_with_source(
                object(),
                "subject",
                "user@example.com",
                now,
            )

        self.assertEqual(message_id, "<sent-id@example.com>")
        self.assertFalse(is_fallback)
        self.assertEqual(source, "sent_items")

    def test_message_id_source_fallback(self):
        sender = OutlookMailSender(dry_run=False)
        now = dt.datetime.now()

        with mock.patch.object(
            sender,
            "_poll_message_id_from_mail_item",
            return_value="",
        ), mock.patch.object(
            sender,
            "_get_message_id_from_sent_items",
            return_value="",
        ), mock.patch.object(
            sender,
            "_generate_fallback_id",
            return_value="FALLBACK:test",
        ):
            message_id, is_fallback, source = sender._get_message_id_with_source(
                object(),
                "subject",
                "user@example.com",
                now,
            )

        self.assertEqual(message_id, "FALLBACK:test")
        self.assertTrue(is_fallback)
        self.assertEqual(source, "fallback")


if __name__ == "__main__":
    unittest.main()

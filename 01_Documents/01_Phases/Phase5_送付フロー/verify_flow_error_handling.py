import json
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class OrderLine:
    order_id: str
    vendor_id: str
    delivery_address: str
    item_name: str


def validate_order_consistency(lines: List[OrderLine]) -> Tuple[bool, str]:
    if not lines:
        return False, "データ不整合: 明細が0件"

    vendor_ids = {line.vendor_id for line in lines}
    if len(vendor_ids) != 1:
        return False, "データ不整合: VendorIDが混在"

    delivery_addresses = {line.delivery_address for line in lines}
    if len(delivery_addresses) != 1:
        return False, "データ不整合: DeliveryAddressが混在"

    return True, ""


def resolve_vendor(vendor_id: str, vendor_master: Dict[str, Dict[str, str]]) -> Tuple[bool, str]:
    if vendor_id not in vendor_master:
        return False, f"業者マスタ不一致: VendorID={vendor_id}"
    return True, ""


def simulate_send_flow(lines: List[OrderLine], vendor_master: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    ok, message = validate_order_consistency(lines)
    if not ok:
        return {"SendStatus": "エラー", "ErrorLog": message}

    ok, message = resolve_vendor(lines[0].vendor_id, vendor_master)
    if not ok:
        return {"SendStatus": "エラー", "ErrorLog": message}

    return {"SendStatus": "送付準備完了", "ErrorLog": ""}


def run_tests() -> Dict[str, Dict[str, str]]:
    vendor_master = {
        "V001": {"VendorName": "テストサプライヤー株式会社", "VendorEmail": "vendor@example.com"}
    }

    normal_case = [
        OrderLine("PO-20260206-001", "V001", "千葉県千葉市中央区亥鼻1-8-15", "DNA抽出キット"),
        OrderLine("PO-20260206-001", "V001", "千葉県千葉市中央区亥鼻1-8-15", "NGS解析サービス"),
    ]

    vendor_not_found_case = [
        OrderLine("PO-20260206-002", "V999", "千葉県千葉市中央区亥鼻1-8-15", "試薬A"),
        OrderLine("PO-20260206-002", "V999", "千葉県千葉市中央区亥鼻1-8-15", "試薬B"),
    ]

    mixed_vendor_case = [
        OrderLine("PO-20260206-003", "V001", "千葉県千葉市中央区亥鼻1-8-15", "試薬A"),
        OrderLine("PO-20260206-003", "V002", "千葉県千葉市中央区亥鼻1-8-15", "試薬B"),
    ]

    return {
        "normal_case": simulate_send_flow(normal_case, vendor_master),
        "vendor_not_found_case": simulate_send_flow(vendor_not_found_case, vendor_master),
        "mixed_vendor_case": simulate_send_flow(mixed_vendor_case, vendor_master),
    }


def main() -> None:
    result = run_tests()
    print(json.dumps(result, ensure_ascii=False, indent=2))

    assert result["normal_case"]["SendStatus"] == "送付準備完了"
    assert result["vendor_not_found_case"]["SendStatus"] == "エラー"
    assert "業者マスタ不一致" in result["vendor_not_found_case"]["ErrorLog"]
    assert result["mixed_vendor_case"]["SendStatus"] == "エラー"
    assert "VendorIDが混在" in result["mixed_vendor_case"]["ErrorLog"]


if __name__ == "__main__":
    main()

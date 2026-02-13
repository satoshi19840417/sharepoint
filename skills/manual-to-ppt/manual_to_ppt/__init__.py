"""Manual-to-PPT conversion package."""

from manual_to_ppt.converter import convert_excel_to_ppt
from manual_to_ppt.generate_ppt import PowerPointGenerator
from manual_to_ppt.parse_manual import ExcelManualParser

__all__ = ["ExcelManualParser", "PowerPointGenerator", "convert_excel_to_ppt"]


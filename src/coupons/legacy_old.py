from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from threading import Lock
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from django.conf import settings
from django.utils import timezone

_XML_NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
_PKG_REL_NS = {
    "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
}

_CACHE_LOCK = Lock()
_CACHE_STAMP: tuple[tuple[str, int, int], ...] | None = None
_CACHE_RECORDS: dict[str, "LegacyOldCouponRecord"] = {}


@dataclass(frozen=True)
class LegacyOldCouponRecord:
    code: str
    raw_code: str
    amount: int
    expires_at: datetime
    issued_at: datetime | None
    used: bool
    group_name: str
    branch_name: str
    source_file: str
    row_number: int


def legacy_old_coupon_dir() -> Path:
    raw = str(getattr(settings, "LEGACY_OLD_COUPON_DIR", "") or "").strip()
    if raw:
        return Path(raw)
    return Path(settings.BASE_DIR).parent / "OLDVERSIONCOUPON"


def load_legacy_old_coupon_records(*, force: bool = False) -> dict[str, LegacyOldCouponRecord]:
    global _CACHE_RECORDS, _CACHE_STAMP

    directory = legacy_old_coupon_dir()
    workbooks = sorted(directory.glob("*.xlsx")) if directory.is_dir() else []
    stamp = tuple(
        (path.name, int(path.stat().st_mtime_ns), int(path.stat().st_size))
        for path in workbooks
    )

    with _CACHE_LOCK:
        if (not force) and (_CACHE_STAMP == stamp):
            return dict(_CACHE_RECORDS)

        records: dict[str, LegacyOldCouponRecord] = {}
        for workbook in workbooks:
            for record in _load_workbook_records(workbook):
                records[record.code] = record

        _CACHE_STAMP = stamp
        _CACHE_RECORDS = records
        return dict(_CACHE_RECORDS)


def get_legacy_old_coupon_record(code: str) -> LegacyOldCouponRecord | None:
    digits = "".join(ch for ch in str(code or "") if ch.isdigit())
    if len(digits) != 8:
        return None
    return load_legacy_old_coupon_records().get(digits)


def _load_workbook_records(path: Path) -> list[LegacyOldCouponRecord]:
    records: list[LegacyOldCouponRecord] = []
    with ZipFile(path) as archive:
        shared_strings = _read_shared_strings(archive)
        sheet_path = _resolve_first_sheet_path(archive)
        if not sheet_path:
            return records
        root = ET.fromstring(archive.read(sheet_path))
        header_map: dict[str, str] = {}
        for row in root.findall("main:sheetData/main:row", _XML_NS):
            row_number = int(row.attrib.get("r", "0") or 0)
            values = _row_values(row, shared_strings)
            if row_number == 2:
                header_map = {
                    str(value).strip(): column
                    for column, value in values.items()
                    if str(value).strip()
                }
                continue
            if row_number < 3 or not header_map:
                continue
            record = _build_record(values, header_map, source_file=path.name, row_number=row_number)
            if record is not None:
                records.append(record)
    return records


def _build_record(
    row_values: dict[str, str],
    header_map: dict[str, str],
    *,
    source_file: str,
    row_number: int,
) -> LegacyOldCouponRecord | None:
    code_column = header_map.get("쿠폰코드")
    amount_column = header_map.get("금액")
    expires_column = header_map.get("유효기간")
    issued_column = header_map.get("발행일")
    used_column = header_map.get("사용여부")
    group_column = header_map.get("그룹")
    branch_column = header_map.get("지점")

    raw_code = str(row_values.get(code_column or "", "")).strip()
    code = "".join(ch for ch in raw_code if ch.isdigit())
    if len(code) != 8:
        return None

    amount = _parse_amount(row_values.get(amount_column or "", ""))
    expires_at = _parse_datetime(row_values.get(expires_column or "", ""), end_of_day=True)
    if expires_at is None:
        return None

    issued_at = _parse_datetime(row_values.get(issued_column or "", ""), end_of_day=False)
    used_text = str(row_values.get(used_column or "", "")).strip().upper()
    used = used_text not in {"", "N", "NO", "FALSE", "0"}

    return LegacyOldCouponRecord(
        code=code,
        raw_code=raw_code,
        amount=amount,
        expires_at=expires_at,
        issued_at=issued_at,
        used=used,
        group_name=str(row_values.get(group_column or "", "")).strip(),
        branch_name=str(row_values.get(branch_column or "", "")).strip(),
        source_file=source_file,
        row_number=row_number,
    )


def _read_shared_strings(archive: ZipFile) -> list[str]:
    try:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    values: list[str] = []
    for item in root.findall("main:si", _XML_NS):
        text = "".join(node.text or "" for node in item.iterfind(".//main:t", _XML_NS))
        values.append(text)
    return values


def _resolve_first_sheet_path(archive: ZipFile) -> str:
    try:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    except KeyError:
        return ""

    relationship_map = {
        rel.attrib.get("Id", ""): rel.attrib.get("Target", "")
        for rel in relationships.findall("pkg:Relationship", _PKG_REL_NS)
    }
    first_sheet = workbook.find("main:sheets/main:sheet", _XML_NS)
    if first_sheet is None:
        return ""
    relation_id = first_sheet.attrib.get(f"{{{_XML_NS['rel']}}}id", "")
    target = relationship_map.get(relation_id, "")
    if not target:
        return ""
    return "xl/" + target.lstrip("/")


def _row_values(row: ET.Element, shared_strings: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for cell in row.findall("main:c", _XML_NS):
        ref = cell.attrib.get("r", "")
        column = "".join(ch for ch in ref if ch.isalpha())
        if not column:
            continue
        values[column] = _cell_value(cell, shared_strings)
    return values


def _cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    value_node = cell.find("main:v", _XML_NS)
    if value_node is None:
        return "".join(node.text or "" for node in cell.iterfind(".//main:t", _XML_NS))

    raw = value_node.text or ""
    if cell.attrib.get("t") == "s":
        try:
            return shared_strings[int(raw)]
        except Exception:
            return raw
    return raw


def _parse_amount(raw: str) -> int:
    digits = "".join(ch for ch in str(raw or "") if ch.isdigit())
    if not digits:
        return 0
    try:
        return max(0, int(digits))
    except Exception:
        return 0


def _parse_datetime(raw: str, *, end_of_day: bool) -> datetime | None:
    text = str(raw or "").strip()
    if not text:
        return None

    parsed: datetime | None = None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(text, fmt)
            break
        except ValueError:
            continue
    if parsed is None:
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None

    if end_of_day and parsed.hour == 0 and parsed.minute == 0 and parsed.second == 0:
        parsed = datetime.combine(parsed.date(), time(23, 59, 59))

    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    return timezone.localtime(parsed)

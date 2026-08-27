# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import csv
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from io import StringIO
from typing import Any

from pydantic import ValidationError

from mod.ipr_asic.data import MinerData

_QT_TEXT_DATE_FORMAT = "%a %b %d %H:%M:%S %Y"


class MinerCSVError(ValueError):
    pass


def normalize_recv_at(value: Any) -> int | None:
    """Convert supported table timestamp values to epoch seconds."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return int(value.timestamp())
    if isinstance(value, int):
        return value

    text = str(value).strip()
    if not text or text == "N/A":
        return None
    try:
        return int(text)
    except ValueError:
        pass

    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.strptime(text, _QT_TEXT_DATE_FORMAT).astimezone()
        except ValueError:
            return None
    return int(parsed.timestamp())


def miner_from_mapping(data: Mapping[str, Any]) -> MinerData:
    """Build typed miner data from API or CSV-style string values."""
    cleaned: dict[str, Any] = {}
    for key in MinerData.model_fields:
        if key not in data:
            continue
        value = data[key]
        cleaned[key] = None if value in ("N/A", "") else value
    cleaned["recv_at"] = normalize_recv_at(data.get("recv_at"))
    return MinerData(**cleaned)


def _field_name(header: str) -> str:
    return "_".join(header.lstrip("\ufeff").strip().lower().split())


def parse_miner_csv(text: str) -> list[MinerData]:
    """Parse CSV text into typed miners, accepting partial or reordered columns."""
    try:
        reader = csv.DictReader(StringIO(text))
        if reader.fieldnames is None:
            return []
        fields = {_field_name(header) for header in reader.fieldnames}
        if not fields.intersection(MinerData.model_fields):
            raise MinerCSVError("CSV does not contain any supported miner columns")

        miners: list[MinerData] = []
        for row in reader:
            normalized = {
                _field_name(header): value
                for header, value in row.items()
                if header is not None
            }
            if not any(value not in (None, "") for value in normalized.values()):
                continue
            miners.append(miner_from_mapping(normalized))
        return miners
    except (csv.Error, TypeError, ValidationError) as error:
        raise MinerCSVError(f"Invalid miner CSV: {error}") from error


def serialize_csv(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    """Serialize tabular values with standard CSV quoting and newlines."""
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(rows)
    return output.getvalue()

"""Parse metadata out of a plain-format PostgreSQL SQL dump.

v1 supports `pg_dump -Fp --no-owner --no-privileges` text dumps (optionally
gzip-compressed by the caller).  Custom-format dumps are rejected by verify.py.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class TableMeta:
    columns: list[str] = field(default_factory=list)
    rows: int = 0


@dataclass
class DumpMeta:
    tables: dict[str, TableMeta] = field(default_factory=dict)


_CREATE_RE = re.compile(r"^CREATE TABLE (?:IF NOT EXISTS )?([A-Za-z0-9_.\"]+) \(", re.I)
_COPY_RE = re.compile(
    r"^COPY\s+([A-Za-z0-9_.\"]+)\s+\(([^)]*)\)\s+FROM stdin;\s*$", re.I
)
_INSERT_RE = re.compile(r"^INSERT INTO\s+([A-Za-z0-9_.\"]+)\s+\(([^)]*)\)\s+VALUES\s*", re.I)
_SKIP_COLUMN_PREFIXES = (
    "constraint ",
    "primary key",
    "unique ",
    "check ",
    "foreign key",
)


def _clean_identifier(value: str) -> str:
    return value.strip().strip('"')


def _split_columns(raw: str) -> list[str]:
    return [_clean_identifier(part) for part in raw.split(",") if part.strip()]


def parse_dump(text: str) -> DumpMeta:
    """Return table/column names and expected row counts from a plain SQL dump."""
    meta = DumpMeta()
    in_create: str | None = None
    copy_table: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if in_create is not None:
            if line == ");" or line.startswith("\\."):
                in_create = None
                continue
            lowered = line.lower()
            if not line or lowered.startswith(_SKIP_COLUMN_PREFIXES):
                continue
            column = _clean_identifier(line.split()[0])
            if column and column not in meta.tables[in_create].columns:
                meta.tables[in_create].columns.append(column)
            continue

        if copy_table is not None:
            if line == r"\.":
                copy_table = None
            elif line:
                meta.tables[copy_table].rows += 1
            continue

        create_match = _CREATE_RE.match(line)
        if create_match:
            name = _clean_identifier(create_match.group(1))
            if name not in meta.tables:
                meta.tables[name] = TableMeta()
            in_create = name
            continue

        copy_match = _COPY_RE.match(line)
        if copy_match:
            name = _clean_identifier(copy_match.group(1))
            table = meta.tables.setdefault(name, TableMeta())
            columns = _split_columns(copy_match.group(2))
            if columns:
                table.columns = columns
            copy_table = name
            continue

        insert_match = _INSERT_RE.match(line)
        if insert_match:
            name = _clean_identifier(insert_match.group(1))
            table = meta.tables.setdefault(name, TableMeta())
            columns = _split_columns(insert_match.group(2))
            if columns and not table.columns:
                table.columns = columns
            table.rows += max(1, line.count("),(") + 1)

    return meta

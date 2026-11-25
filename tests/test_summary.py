import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from parse_dump import parse_dump  # noqa: E402
from verify import format_table_report  # noqa: E402


def test_table_report_shows_expected_and_actual_counts():
    meta = parse_dump(
        "CREATE TABLE public.users (\n"
        "    id integer NOT NULL,\n"
        "    name text NOT NULL\n"
        ");\n"
        "COPY public.users (id, name) FROM stdin;\n"
        "1\talice\n"
        "2\tbob\n"
        "\\.\n"
    )

    report = format_table_report(
        meta,
        actual_rows={"public.users": 2},
        actual_columns={"public.users": ["id", "name"]},
    )

    assert "| public.users | 2 | 2 | id, name | id, name |" in report


def test_table_report_shows_missing_actual_values():
    meta = parse_dump(
        "CREATE TABLE public.events (\n"
        "    id integer NOT NULL\n"
        ");\n"
        "COPY public.events (id) FROM stdin;\n"
        "1\n"
        "\\.\n"
    )

    report = format_table_report(meta, actual_rows={}, actual_columns={})

    assert "| public.events | 1 | - | id | - |" in report

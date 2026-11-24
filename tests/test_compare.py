import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from parse_dump import parse_dump  # noqa: E402
from verify import compare_results  # noqa: E402


def test_compare_flags_missing_rows_and_columns():
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

    issues = compare_results(
        meta,
        actual_rows={"public.users": 1},
        actual_columns={"public.users": ["id"]},
    )

    assert any("row count" in issue and "2" in issue and "1" in issue for issue in issues)
    assert any("column" in issue and "name" in issue for issue in issues)

"""Pin the Action contract in both directions.

1. Every declared input is forwarded as an env var and a --flag.
2. Every --flag the entrypoint builds is accepted by verify.py --help.
"""

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ACTION = ROOT / "action.yml"
VERIFY = ROOT / "src" / "verify.py"


def declared_inputs() -> list[str]:
    lines = ACTION.read_text(encoding="utf-8").splitlines()
    start = lines.index("inputs:")
    end = lines.index("runs:")
    return [
        match.group(1)
        for line in lines[start + 1 : end]
        if (match := re.match(r"^  ([a-z][a-z-]*):\s*$", line))
    ]


def test_action_is_composite():
    assert "  using: composite" in ACTION.read_text(encoding="utf-8")


def test_every_declared_input_is_forwarded_and_accepted():
    text = ACTION.read_text(encoding="utf-8")
    help_text = subprocess.run(
        [sys.executable, str(VERIFY), "--help"],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    ).stdout
    inputs = declared_inputs()

    assert inputs == [
        "dump-path",
        "postgres-image",
        "min-tables",
        "expected-tables",
        "fail-on-stderr",
    ]

    for name in inputs:
        env_name = "INPUT_" + name.upper().replace("-", "_")
        flag = "--" + name
        assert env_name + ":" in text, f"{name} has no env mapping"
        assert flag in text, f"{name} is not forwarded by action.yml"
        assert flag in help_text, f"{name} is not accepted by verify.py"


def test_empty_expected_tables_is_not_forwarded_as_a_literal_value():
    # Composite shell passes "$INPUT_EXPECTED_TABLES" (empty string), which
    # verify.py accepts and treats as "no assertion". Prove that parsing.
    sys.path.insert(0, str(ROOT / "src"))
    from verify import parse_args

    args = parse_args(
        [
            "--dump-path", "x.sql",
            "--postgres-image", "postgres:17",
            "--min-tables", "1",
            "--expected-tables", "",
            "--fail-on-stderr", "true",
        ]
    )
    assert args.expected_tables == ""
    assert args.fail_on_stderr == "true"

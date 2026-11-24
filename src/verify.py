#!/usr/bin/env python3
"""Restore a Postgres logical dump into a throwaway container and fail loudly.

v1 contract:
  exit 0 = verified restorable
  exit 1 = corruption / restore failure
  exit 2 = configuration or input error
"""

from __future__ import annotations

import argparse
import gzip
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_dump import parse_dump  # noqa: E402

_ERROR_RE = re.compile(r"\b(ERROR|FATAL|PSError)\b", re.I)


def compare_results(meta, actual_rows: dict[str, int], actual_columns: dict[str, list[str]]) -> list[str]:
    """Compare dump metadata to what actually landed in the restored database."""
    issues: list[str] = []
    for name, table in meta.tables.items():
        restored_rows = actual_rows.get(name)
        if restored_rows is None:
            issues.append(f"table {name} missing after restore")
        elif restored_rows != table.rows:
            issues.append(
                f"row count mismatch for {name}: dump={table.rows} restored={restored_rows}"
            )

        restored_columns = actual_columns.get(name)
        if restored_columns is None:
            issues.append(f"columns unavailable for {name} after restore")
            continue
        missing = [column for column in table.columns if column not in restored_columns]
        extra = [column for column in restored_columns if column not in table.columns]
        if missing:
            issues.append(f"column mismatch for {name}: missing {', '.join(missing)}")
        if extra:
            issues.append(f"column mismatch for {name}: unexpected {', '.join(extra)}")
    return issues


class GateError(Exception):
    def __init__(self, message: str, code: int = 2):
        super().__init__(message)
        self.code = code


def read_dump(path: Path) -> str:
    try:
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
                return fh.read()
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise GateError(f"cannot read dump {path}: {exc}") from exc


def run(cmd: list[str], *, stdin=None, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        stdin=stdin,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


def start_container(image: str) -> str:
    name = f"restore-verify-{uuid.uuid4().hex[:12]}"
    result = run(
        [
            "docker",
            "run",
            "--rm",
            "-d",
            "--name",
            name,
            "-e",
            "POSTGRES_PASSWORD=restore_verify",
            "-e",
            "POSTGRES_DB=restore_verify",
            image,
        ]
    )
    if result.returncode != 0:
        raise GateError(f"docker run failed: {result.stderr.strip()}")
    return name


def wait_ready(container: str, seconds: int = 90) -> None:
    """Wait for the *final* server, not the temporary initdb server.

    pg_isready on the default unix socket answers during initialization and can
    hand us a window where the temporary server is shutting down.  The real
    server listens on TCP; require two consecutive TCP SELECT 1 successes.
    """
    deadline = time.monotonic() + seconds
    last = ""
    consecutive = 0
    while time.monotonic() < deadline:
        probe = run(
            [
                "docker",
                "exec",
                container,
                "psql",
                "-h",
                "127.0.0.1",
                "-At",
                "-U",
                "postgres",
                "-d",
                "restore_verify",
                "-c",
                "SELECT 1",
            ]
        )
        if probe.returncode == 0 and probe.stdout.strip() == "1":
            consecutive += 1
            if consecutive >= 2:
                return
        else:
            consecutive = 0
            last = (probe.stdout + probe.stderr).strip()
        time.sleep(0.5)
    raise GateError(f"postgres never became ready: {last}")


def error_lines(output: str) -> list[str]:
    return [line.strip() for line in output.splitlines() if _ERROR_RE.search(line)]


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _split_qualified(name: str) -> tuple[str, str]:
    schema, separator, table = name.rpartition(".")
    return (schema or "public"), table


def query_restored(container: str, meta) -> tuple[dict[str, int], dict[str, list[str]]]:
    statements: list[str] = []
    for name in meta.tables:
        statements.append(
            f"SELECT 'COUNT|{name}|' || count(*) FROM "
            + ".".join(_quote_ident(part) for part in name.split("."))
            + ";"
        )
    for name in meta.tables:
        schema, table = _split_qualified(name)
        statements.append(
            "SELECT 'COL|"
            + name
            + "|' || column_name FROM information_schema.columns "
            + f"WHERE table_schema='{schema}' AND table_name='{table}' ORDER BY ordinal_position;"
        )
    probe = run(
        [
            "docker",
            "exec",
            "-i",
            container,
            "psql",
            "-X",
            "-h",
            "127.0.0.1",
            "-At",
            "-U",
            "postgres",
            "-d",
            "restore_verify",
            "-f",
            "-",
        ],
        input_text="\n".join(statements) + "\n",
    )
    rows: dict[str, int] = {}
    columns: dict[str, list[str]] = {}
    for line in (probe.stdout + "\n" + probe.stderr).splitlines():
        if line.startswith("COUNT|"):
            _, name, value = line.split("|", 2)
            if value.isdigit():
                rows[name] = int(value)
        elif line.startswith("COL|"):
            _, name, column = line.split("|", 2)
            columns.setdefault(name, []).append(column)
    return rows, columns


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump-path", required=True)
    parser.add_argument("--postgres-image", default="postgres:17")
    parser.add_argument("--min-tables", type=int, default=1)
    parser.add_argument("--expected-tables", default="")
    parser.add_argument("--fail-on-stderr", choices=["true", "false"], default="true")
    return parser.parse_args(argv)


def write_summary(text: str) -> None:
    print(text)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        try:
            with open(summary_path, "a", encoding="utf-8") as fh:
                fh.write(text + "\n")
        except OSError:
            pass


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    dump_path = Path(args.dump_path)
    if not dump_path.exists():
        write_summary(f"::error::dump not found: {dump_path}")
        return 2

    raw = read_dump(dump_path)
    if raw.startswith("PGDMP"):
        write_summary("::error::custom-format dumps are not supported; use pg_dump -Fp")
        return 2

    meta = parse_dump(raw)
    if len(meta.tables) < args.min_tables:
        write_summary(
            f"::error::expected at least {args.min_tables} tables, parsed {len(meta.tables)}"
        )
        return 1

    container = None
    try:
        container = start_container(args.postgres_image)
        wait_ready(container)
        with dump_path.open("rb") as fh:
            restore = run(
                [
                    "docker",
                    "exec",
                    "-i",
                    container,
                    "psql",
                    "-X",
                    "-h",
                    "127.0.0.1",
                    "-v",
                    "ON_ERROR_STOP=1",
                    "-q",
                    "-U",
                    "postgres",
                    "-d",
                    "restore_verify",
                    "-f",
                    "-",
                ],
                stdin=fh,
            )
        restore_output = restore.stdout + restore.stderr
        errors = error_lines(restore_output) if args.fail_on_stderr == "true" else []
        actual_rows, actual_columns = query_restored(container, meta)
        issues = compare_results(meta, actual_rows, actual_columns)
        if args.expected_tables:
            expected = [name.strip() for name in args.expected_tables.split(",") if name.strip()]
            issues.extend(
                f"expected table {name} not present in dump" for name in expected if name not in meta.tables
            )
        details = "\n".join(
            f"- {line}" for line in (errors + issues)
        ) or "- none"
        summary = (
            "## restore-verify: FAIL\n\n"
            f"- image: `{args.postgres_image}`\n"
            f"- tables parsed: {len(meta.tables)}\n"
            f"- restore exit code: {restore.returncode}\n"
            f"- ERROR/FATAL lines and mismatches:\n{details}\n"
        )
        if restore.returncode != 0 or errors or issues:
            write_summary(summary)
            return 1
        write_summary(
            "## restore-verify: PASS\n\n"
            f"restore completed with no ERROR/FATAL lines; {len(meta.tables)} table(s) "
            "matched parsed row counts and columns."
        )
        return 0
    except GateError as exc:
        write_summary(f"::error::{exc}")
        return exc.code
    finally:
        if container:
            run(["docker", "rm", "-f", container])


if __name__ == "__main__":
    sys.exit(main())

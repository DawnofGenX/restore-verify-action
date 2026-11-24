#!/usr/bin/env python3
"""Ad-hoc proof for restore-verify-action.

Run: python3 tests/adhoc-verify.py

Real invocations against real throwaway Postgres containers, in a tempdir that
is always removed. Exits 0 only if every assertion holds and no container leaks.
This is deliberately separate from pytest: a green unit suite is not the proof.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERIFY = ROOT / "src" / "verify.py"
FIXTURES = ROOT / "tests" / "fixtures"


def gate(dump: pathlib.Path, image: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable, str(VERIFY),
            "--dump-path", str(dump),
            "--postgres-image", image,
            "--min-tables", "1",
        ],
        capture_output=True, text=True, timeout=240,
    )


def leaked_containers() -> list[str]:
    result = subprocess.run(
        ["docker", "ps", "-a", "--filter", "name=restore-verify", "--format", "{{.Names}}"],
        capture_output=True, text=True, timeout=30,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="restore-verify-proof-") as temp:
        work = pathlib.Path(temp)
        for name in ("version-skew", "partial-restore", "healthy"):
            shutil.copytree(FIXTURES / name, work / name)

        skew = gate(work / "version-skew" / "dump.sql", "postgres:16-alpine")
        skew_out = (skew.stdout + skew.stderr).lower()
        if skew.returncode != 1 or "unrecognized configuration parameter" not in skew_out:
            failures.append(f"skew: rc={skew.returncode} output={skew_out[:300]!r}")

        partial = gate(work / "partial-restore" / "dump.sql", "postgres:17")
        partial_out = (partial.stdout + partial.stderr).lower()
        if partial.returncode != 1:
            failures.append(f"partial: rc={partial.returncode}")
        if "duplicate key" not in partial_out:
            failures.append("partial: missing duplicate-key evidence")
        if "row count mismatch" not in partial_out:
            failures.append("partial: missing row-count mismatch evidence")

        healthy = gate(work / "healthy" / "dump.sql", "postgres:17")
        healthy_out = healthy.stdout + healthy.stderr
        if healthy.returncode != 0 or "restore-verify: PASS" not in healthy_out:
            failures.append(f"healthy: rc={healthy.returncode} output={healthy_out[:300]!r}")
        if "2 table" not in healthy_out:
            failures.append("healthy: did not report 2 verified tables")

        leaks = leaked_containers()
        if leaks:
            failures.append(f"leaked containers: {leaks}")

    print(f"RESULT: skew_fail={skew.returncode == 1} partial_fail={partial.returncode == 1} "
          f"row_mismatch_seen={'row count mismatch' in partial_out} "
          f"healthy_pass={healthy.returncode == 0} container_leaks={len(leaks)}")
    if failures:
        for failure in failures:
            print("FAIL:", failure)
        return 1
    print("ADHOC VERIFY: PASS (tempdir removed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

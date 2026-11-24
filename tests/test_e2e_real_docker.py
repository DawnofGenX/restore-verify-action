"""Real end-to-end checks: the gate runs against throwaway Postgres containers."""

import pathlib
import shutil
import subprocess
import sys
import time

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERIFY = ROOT / "src" / "verify.py"
FIXTURES = ROOT / "tests" / "fixtures"


def run_gate(dump: pathlib.Path, image: str, *extra: str) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(VERIFY),
        "--dump-path",
        str(dump),
        "--postgres-image",
        image,
        "--min-tables",
        "1",
        *extra,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=240)


pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="docker not installed")


def test_version_skew_dump_fails_on_unknown_guc():
    result = run_gate(FIXTURES / "version-skew" / "dump.sql", "postgres:16-alpine")
    combined = (result.stdout + result.stderr).lower()

    assert result.returncode == 1, combined
    assert "unrecognized configuration parameter" in combined


def test_naive_psql_accepts_partial_restore_with_exit_zero():
    """Trigger proof: the incident is real before claiming the gate catches it."""
    container = subprocess.run(
        [
            "docker", "run", "--rm", "-d",
            "-e", "POSTGRES_PASSWORD=restore_verify",
            "-e", "POSTGRES_DB=restore_verify",
            "postgres:17",
        ],
        capture_output=True, text=True, timeout=120, check=True,
    ).stdout.strip()
    try:
        ready_deadline = time.monotonic() + 90
        while time.monotonic() < ready_deadline:
            probe = subprocess.run(
                ["docker", "exec", container, "psql", "-h", "127.0.0.1", "-At",
                 "-U", "postgres", "-d", "restore_verify", "-c", "SELECT 1"],
                capture_output=True, text=True,
            )
            if probe.returncode == 0 and probe.stdout.strip() == "1":
                break
            time.sleep(0.5)
        with (FIXTURES / "partial-restore" / "dump.sql").open("rb") as fh:
            naive = subprocess.run(
                ["docker", "exec", "-i", container, "psql", "-X", "-h", "127.0.0.1", "-q",
                 "-U", "postgres", "-d", "restore_verify", "-f", "-"],
                stdin=fh, capture_output=True, text=True, timeout=120,
            )
    finally:
        subprocess.run(["docker", "rm", "-f", container], capture_output=True)

    assert naive.returncode == 0, naive.stderr
    assert "duplicate key" in naive.stderr.lower()


def test_partial_restore_dump_fails_gate_with_row_mismatch():
    result = run_gate(FIXTURES / "partial-restore" / "dump.sql", "postgres:17")
    combined = (result.stdout + result.stderr).lower()

    assert result.returncode == 1, combined
    assert "duplicate key" in combined
    assert "row count mismatch" in combined


def test_healthy_dump_passes_gate():
    result = run_gate(FIXTURES / "healthy" / "dump.sql", "postgres:17")
    combined = result.stdout + result.stderr

    assert result.returncode == 0, combined
    assert "restore-verify: PASS" in combined
    assert "2 table" in combined


def test_missing_dump_is_config_error():
    result = run_gate(FIXTURES / "healthy" / "does-not-exist.sql", "postgres:17")
    assert result.returncode == 2, result.stdout + result.stderr

"""A gzipped plain-format dump must be parsed and restored, not piped as gzip bytes."""

import gzip
import pathlib
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERIFY = ROOT / "src" / "verify.py"
HEALTHY = ROOT / "tests" / "fixtures" / "healthy" / "dump.sql"

pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="docker not installed")


def test_gzipped_healthy_dump_passes_gate(tmp_path: pathlib.Path):
    gz = tmp_path / "dump.sql.gz"
    with HEALTHY.open("rb") as src, gzip.open(gz, "wb") as dst:
        shutil.copyfileobj(src, dst)

    result = subprocess.run(
        [sys.executable, str(VERIFY), "--dump-path", str(gz),
         "--postgres-image", "postgres:17", "--min-tables", "1"],
        capture_output=True, text=True, timeout=240,
    )
    combined = result.stdout + result.stderr

    assert result.returncode == 0, combined
    assert "restore-verify: PASS" in combined
    assert "2 table" in combined

# restore-verify-action

**Backups are lies until you restore them.** This GitHub Action proves a
PostgreSQL logical dump is restorable by restoring it into a throwaway
container and failing on silent corruption. It is a verification gate, not a
backup tool, scheduler, or hosted service.

## Why this exists

Two real incidents are the fixtures:

- [glou-server #92](https://github.com/jackthomasanderson/glou-server/issues/92):
  a PG17 dump contained `SET transaction_timeout = '5s'`, which a pre-PG17
  server aborted on. Every restore of that image's dumps was silently broken.
- [PicPeak #2482](https://github.com/PicPeak/picpeak/issues/2482): a `psql`
  restore with an error mid-`COPY` printed errors to stderr, carried on, and
  exited **0** — a partial restore looked complete.

`exit 0` is not evidence. This gate checks stderr, table/column sets, and row
counts parsed from the dump itself.

## What it does

1. Parses a plain-format `pg_dump -Fp` SQL file (`.sql` or `.sql.gz`) for table
   names, column names, and expected row counts from `COPY`/`INSERT` blocks.
2. Starts `docker run --rm -d` with the chosen Postgres image, **no volume**,
   and waits for the final server to accept TCP connections (avoids the
   initdb temporary-server race).
3. Restores with `psql -v ON_ERROR_STOP=1`, capturing stderr.
4. Queries the restored database and compares row counts and column names to
   the dump metadata.
5. Writes a job summary and exits:
   - `0` — verified restorable
   - `1` — corruption / restore failure
   - `2` — configuration or input error
6. Removes the container on every exit path.

Custom-format dumps (`pg_dump -Fc`) are rejected with an actionable message.
v1 supports PostgreSQL only.

## Usage

```yaml
- uses: DawnofGenX/restore-verify-action@v0.2
  with:
    dump-path: artifacts/latest.sql.gz
    postgres-image: postgres:17
    min-tables: '3'
    expected-tables: public.users,public.events
```

Inputs: `dump-path` (required), `postgres-image` (default `postgres:17`),
`min-tables` (default `1`), `expected-tables` (default empty),
`fail-on-stderr` (default `true`).

The composite action runs on a GitHub-hosted runner with Docker and Python 3
already present. Nothing is hosted by this project.

## Proof (real containers, 2026-11-24 IST)

```
$ python3 tests/adhoc-verify.py
RESULT: skew_fail=True partial_fail=True row_mismatch_seen=True healthy_pass=True container_leaks=0
ADHOC VERIFY: PASS (tempdir removed)

$ pytest tests/ -q
10 passed in 9.78s   # 3 consecutive runs: 7/7, then 10/10 after contract tests
```

The partial-restore test also proves the *trigger*: naive `psql -f` (no
`ON_ERROR_STOP`) exits 0 with `duplicate key value violates unique constraint`,
so the harness is not passing vacuously.

## Limits and honest odds

- Distribution target list: [docs/target-repos.md](docs/target-repos.md). Only
  3 repos are corpus-confirmed, and only one of them is ≥100★. Seven more must
  be qualified before day 0.
- Kill gates (from the research spec): day 30 ≥5/10 acknowledgements; day 45
  ≥30★; day 90 ≥100★ OR ≥3 merged installs in ≥500★ repos. Global stop: day 45
  <40★ AND <5 merged PRs.
- Death signal: any backup tool ships a tool-agnostic verify-gate within 45 days.

# Distribution targets — restore-verify-action

Status as of 2026-11-25 IST: **10 of 10 qualified on paper. 0 contacted.**
Nothing below is a claim of acknowledgement, comment, PR, or merge. Record
those only with real IDs/SHAs after they land.

## Corrections to the earlier 3-target list

The earlier corpus-confirmed list was over-optimistic on two entries:

- `jackthomasanderson/glou-server#92` was verified **closed** on 2026-11-25
  (2 comments). Its version-skew fixture is still useful, but it is not an
  open-issue target.
- `perpipis/kunigi-archive#5` returned **404** via `gh api repos/.../issues/5`
  on 2026-11-25. It is not a live contact target.

`PicPeak/picpeak#2482` remains open and is retained.

## Qualified list (10 distinct repos)

Selection rule applied:
1. ≥100★ except where noted, commit in last 12 months.
2. Open, human-authored issue naming a real restore/backup failure or an
   explicit restore-test gap.
3. Live PostgreSQL logical dump/restore path involved.
4. No existing CI step that restores a dump and asserts row counts.
5. Not an AI-generated issue factory; author account checked where possible.

| # | Repo | Stars | Issue | Author (created) | Fit | CI check |
|---|---|---:|---|---|---|---|
| 1 | supabase/supabase | 115388★ | [#40625](https://github.com/supabase/supabase/issues/40625) `Logical backup contains PostgreSQL 17.6+ commands incompatible with PostgreSQL 15.8` | IPJT (2017) | **exact** version skew: `\restrict`/`\unrestrict` from PG17.6 dump fail on PG15.8; 5 comments | 14 workflows checked, no restore verification |
| 2 | immich-app/immich | 120037★ | [#27684](https://github.com/immich-app/immich/issues/27684) `Restore on another machine not working.` | amgschnappi (2022) | **strong**: restore reaches 100% but health check fails; 16 comments, two more restore issues (#33314, #26522) | `test.yml` contains only cache restores |
| 3 | appsmithorg/appsmith | 41298★ | [#40255](https://github.com/appsmithorg/appsmith/issues/40255) `Restore instance on v1.68 is failing. Post restore localhost does not come up.` | btsgh (2022) | **strong**: restore completes but app does not come up; also #39668 (EKS DB restore failure) | 15 workflows checked, no restore verification |
| 4 | ddev/ddev | 3966★ | [#8713](https://github.com/ddev/ddev/issues/8713) `ddev import-db failing for PostgreSQL dump due to the import database role not existing` | FluffyDiscord (2014) | **moderate**: maintainer engaged, repro dump attached; our throwaway-container gate cannot catch missing target role | 12 workflows checked, no restore verification |
| 5 | agentes-chat/agentes-chat | 2019★ | [#990](https://github.com/agentes-chat/agentes-chat/issues/990) `db restore fails on a plain pg_dump 18 file (...) while psql restores the same file fine` | Muzhen2000 (2026) | **exact** parser/skew mismatch; author account is new — verify human before commenting | no workflows |
| 6 | open-mercato/open-mercato | 1964★ | [#4030](https://github.com/open-mercato/open-mercato/issues/4030) `Provide database backups at the infra layer (WAL/PITR + streaming replica), not in app code` | pkarw (2010) | **exact**: merged spec PR #3742 proposed weekly restore verification, then maintainers moved backups out of app code — CI gate is the right layer | `ci.yml`, `mutation-tests.yml`: no restore verification |
| 7 | VonHoltenCodes/SlowBooks-Pro-2026 | 886★ | [#1219](https://github.com/VonHoltenCodes/SlowBooks-Pro-2026/issues/1219) `going back ... by the written restore fails partway and drops most keys` | ContractorKeith (2024) | **exact**: dump uses `--clean --if-exists`, `psql -v ON_ERROR_STOP=1` still exits 3; row-count gate catches partial state | `ci.yml`: no restore verification |
| 8 | mx-space/core | 569★ | [#2889](https://github.com/mx-space/core/issues/2889) `v15.6.1 内置恢复在官方 PostgreSQL 16 配置下因 transaction_timeout 失败` | Lemonawa (2020) | **exact** same mechanism as our version-skew fixture: PG18.6 `pg_dump` emits `SET transaction_timeout = 0`, PG16.14 rejects it | `mobile-testflight.yml` only |
| 9 | PicPeak/picpeak | 374★ | [#2482](https://github.com/PicPeak/picpeak/issues/2482) `A PostgreSQL restore reports success even when statements in the dump fail` | Luca-Timo | **exact** silent exit-0 partial restore; fixture built and proven locally | no restore verification |
| 10 | teslamate-org/teslamate | 9314★ | [#5533](https://github.com/teslamate-org/teslamate/issues/5533) `maintenance and backup scripts fail with non-default postgres.user due to peer auth` | JakobLichterfeld (2016) | **weakest fit**: role/auth not row-count drift; include only if 9 above yield <5 acknowledgements | `elixir_test.yml`, `nix_test.yml`, `rust_test.yml`: no restore verification |

Excluded by inspection: `paperclipai/paperclip` already has
`.github/workflows/backup-checkpoint-qualification.yml` doing a real checkpoint
and restore proof with matching PG clients and `ON_ERROR_STOP=1`; adding our
gate there would be duplicate work. Also excluded: `timescale/timescaledb#10942`
(our row/column gate would pass while values are NULL), `yugabyte/yugabyte-db#36499`
(YSQL-specific dump bugs), `MBombeck/HealthLog#1431` (already fixed in v1.49.0),
and the backup-tool death-signal watch list (databasus, wal-g, pg_probackup,
pgmoneta, db-backup).

## Contact log — 10 comments posted and verified 2026-11-25 IST

All comments were minimal-repro/analysis only: no link to this action, no pitch,
no request to merge anything. Each URL was re-fetched via `gh api` and the
comment ID/body verified (10/10).

| Repo | Issue | Comment ID | Verified |
|---|---|---|---|
| supabase/supabase | #40625 | 7145438027 | yes |
| immich-app/immich | #27684 | 7145438599 | yes |
| appsmithorg/appsmith | #40255 | 7145439071 | yes |
| ddev/ddev | #8713 | 7145439601 | yes |
| agentes-chat/agentes-chat | #990 | 7145440285 | yes |
| mx-space/core | #2889 | 7145440744 | yes |
| PicPeak/picpeak | #2482 | 7145441239 | yes |
| open-mercato/open-mercato | #4030 | 7145447117 | yes (comment-only; maintainer rejects community PRs) |
| VonHoltenCodes/SlowBooks-Pro-2026 | #1219 | 7145447614 | yes (maintainer calls it a beta known limitation) |
| teslamate-org/teslamate | #5533 | 7145448158 | yes (weakest fit) |

## PR log — 6 open PRs, 2 closed, 1 blocked (2026-11-25 IST)

Action repo published at https://github.com/DawnofGenX/restore-verify-action
(current tag `v0.2`, 0★ at publication). Each PR adds only
`.github/workflows/restore-verify-optional.yml`, opt-in via `workflow_dispatch`
plus a weekly schedule, using a self-contained synthetic dump and no secrets.
The exact workflow dump was run locally through `src/verify.py` on
`postgres:17` with exit 0; full suite 11/11 passed after fixing a single-line
`CREATE TABLE` parser bug found by that workflow fixture.

| Repo | PR | Status |
|---|---|---|
| supabase/supabase | [#53980](https://github.com/supabase/supabase/pull/53980) | open |
| immich-app/immich | [#33670](https://github.com/immich-app/immich/pull/33670) | closed by author after the bot reopened it: repo CONTRIBUTING.md asks contributors not to use LLMs to generate PRs; this workflow/body were LLM-drafted and that was disclosed |
| appsmithorg/appsmith | [#42680](https://github.com/appsmithorg/appsmith/pull/42680) | open |
| ddev/ddev | [#9198](https://github.com/ddev/ddev/pull/9198) | closed by maintainer for missing template/context; replaced by #9199 |
| ddev/ddev | [#9199](https://github.com/ddev/ddev/pull/9199) | open — template-conformant replacement, title `ci: add optional restore-verification gate, for #8713` |
| agentes-chat/agentes-chat | [#1371](https://github.com/agentes-chat/agentes-chat/pull/1371) | open — CLA bot asks the author to sign; not signed without explicit user authorization |
| PicPeak/picpeak | [#2663](https://github.com/PicPeak/picpeak/pull/2663) | open |
| VonHoltenCodes/SlowBooks-Pro-2026 | [#1230](https://github.com/VonHoltenCodes/SlowBooks-Pro-2026/pull/1230) | open |
| mx-space/core | fork branch `DawnofGenX:restore-verify-optional` pushed | PR create blocked: `DawnofGenX does not have the correct permissions to execute CreatePullRequest` |

No merge is claimed. Record merges only with a merge commit SHA.

## Day-0 monitoring baseline (2026-11-25 IST)

- Action repo: 0★, 0 forks, 0 open issues; pushed 2026-11-24T22:00:40Z.
- Issue comments: 10/10 resolve; 0 replies from anyone other than the author.
- PRs: 6 open, 2 closed (immich LLM policy; ddev replaced), 1 PR-blocked fork. Bot comments only so far — no human acknowledgement.
- agentes-chat#1371 is open but its CLA bot requires the author to sign the CLA before merge; not signed without explicit user authorization.
- Death-signal baseline (no tool-agnostic restore-verify gate observed): databasus 9328★, wal-g 4349★, pg_probackup 801★, pgmoneta 328★, pghoard 1427★, restoredrill 116★.
- Raw snapshot: `/home/hermes/.hermes/cache/scratch/scale-analysis/status-day0.json`
- Next check: day-30 (2026-12-25 IST) against ≥5/10 acknowledgements; day-45 (2026-01-09 IST) against ≥30★; day-90 (2026-02-23 IST) against ≥100★ OR ≥3 merged installs in ≥500★ repos.

## Motion per qualified repo

1. Read the issue and CI config; reproduce or cite the exact failure mode.
2. Open a useful issue comment with the minimal repro (no pitch, no link drop).
3. Only then open a PR adding the gate as an *optional* workflow with clear
   opt-in — never make it a mandatory check on someone else's repo.
4. Record URL, comment ID, PR ID, and merged status here. Never claim a merge
   without a merge commit SHA.

## Kill gate reminder

Day 30: ≥5/10 acknowledged or merged. Day 45: ≥30★ standalone. Day 90: ≥100★
OR ≥3 merged installs in ≥500★ repos. Global stop by day 45 if <40★ AND <5
merged PRs.

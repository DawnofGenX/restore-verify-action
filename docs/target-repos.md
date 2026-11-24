# Distribution targets — restore-verify-action

Status as of 2026-11-24 IST: **3 of 10 qualify**. Do not count any star,
comment, or merge that has not actually landed. These are research leads, not
contacts yet.

## Corpus-confirmed (3)

| Repo | Stars (verified 2026-11-24) | Issue | Evidence | Status |
|---|---|---|---|---|
| PicPeak/picpeak | 374★ | [#2482](https://github.com/PicPeak/picpeak/issues/2482) | "Partial restores look complete." `psql` without `ON_ERROR_STOP` exits 0 mid-`COPY`. | confirmed; fixture built |
| jackthomasanderson/glou-server | 0★ | [#92](https://github.com/jackthomasanderson/glou-server/issues/92) | "Every restore of a dump taken by this image's current pg_dump was silently broken." `SET transaction_timeout` unknown to pre-PG17. | confirmed; fixture built |
| perpipis/kunigi-archive | 0★ | [#5](https://github.com/perpiris/kunigi-archive/issues/5) | "No restore has ever been tested." | confirmed; owner spelling verified via gh api; low-star |

Only one confirmed target is ≥100★. The day-30 acknowledgement gate (≥5/10)
is not credible until 7 more repos are qualified.

## Seven to qualify before day 0

Selection rule (all must hold):
1. ≥100★, actively maintained (commit in last 12 months).
2. Human-authored open issue stating a DB backup exists but restore was never
   tested, restore silently broke, or no periodic restore test exists.
3. Live PostgreSQL involved (dump/restore, logical backup, migration, or
   disaster-recovery path), not just "backups" as a generic word.
4. No existing CI step that restores and asserts row counts.
5. Issue is not from an AI-generated issue factory — exclude search results
   dominated by templated bot issues.

Search starting points (candidate queries, not qualified targets):
- `gh search issues "restore never tested" language:markdown`
- `gh search issues "no restore has ever been tested"`
- `gh search issues "partial restore" postgres`
- `gh search issues "pg_dump" "ON_ERROR_STOP"`
- `gh search issues "restore test" "postgres" stars:>100`

Disqualified by inspection so far: restoredrill/Databasus/BackupDrill are backup
tools with their own runtime; they are the W1 death-signal watch list, not
install targets.

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

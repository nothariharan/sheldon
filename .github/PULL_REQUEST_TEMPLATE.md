## What

<!-- Which TASKS.md row? Which folder? -->

## Decisions the team should confirm

<!-- Delete the line if this PR makes none. Schema, status words, edge names, and the image pin belong here. -->

## Verification

- [ ] I read the `AGENTS.md` in the folder I edited
- [ ] `ruff check sheldon tests`, `pytest`, and `pytest tests/test_smoke.py` against `falkordb/falkordb:v4.22.1`. Paste the output in this PR (`TESTING.md`)
- [ ] `pytest` (FalkorDB up). If a race is still an expected failure, say so
- [ ] New Cypher is a new file under `queries/`, one statement, no second query
- [ ] Status strings and edge names still come from `sheldon/schema.py`
- [ ] If this lands `claim_task` or `refute_hypothesis`, the stub flag is `False` and the race is not xfailed
- [ ] README, pitch text, and comments do not contain a forbidden claim (`AGENTS.md`)
- [ ] Stub docstrings say to build or roadmap. W1, W2, and R1 are the only stations described as ran, and their functions are still to build
- [ ] No other team's name, handle, repo, or file path
- [ ] Image tag is unchanged, or `sheldon/schema.py`, `docker-compose.yml`, and CI were updated together

## Notes

<!-- What you spiked, and what you did not run. -->

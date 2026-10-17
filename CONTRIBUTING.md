# Contributing

Four people, mostly through agents, on one repo. The way to stay out of each other's way is one branch per task and one owner per folder.

## Branch model

- `main` stays green. Do not push feature work to it.
- Branch name: `area/short-name`, lowercase. Areas: `memory`, `retrieval`, `answers`, `coord`, `belief`, `eval`, `spikes`, `docs`.
- One branch per row in [`TASKS.md`](TASKS.md). Put your name on the row before you branch.
- One PR per branch. Fill in the template, including the verification checklist.
- Rebase on `main` when you need to. Don't merge `main` into a long-lived shared branch, because there should not be a shared branch.
- Commits: imperative, and name the area (`belief: gate refute on cited evidence ids`).

`sheldon/schema.py` is shared. Change it only when the team has confirmed the decision, and say so in the PR. Prefer adding a new file under `queries/` to editing a query someone else owns.

## Checks

```bash
ruff check sheldon tests
pytest
```

`pytest` includes the smoke test, so FalkorDB has to be up (`./scripts/setup.sh`). The claim race and the missing-evidence refute race are expected failures until `CLAIM_IS_STUB` and `REFUTE_IS_STUB` are set to `False`. The PR that implements either write flips that flag and deletes the `NotImplementedError`. CI then fails if the race is wrong.

## Do not

The cut list, the image pin, and the claims you must not write are in [`AGENTS.md`](AGENTS.md). Competitive notes about other teams stay out of the repo.

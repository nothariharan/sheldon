# Testing

Sheldon blocks coding agents from retrying fixes that already failed, and from calling work done without a real test run, from the first edit to the merge, on one shared FalkorDB graph per repo.

The same rule applies to this repo. A task is done when a test ran and the output is in the PR. A claim with no executed run behind it does not land.

Owners and the file each row must add or turn green are in [`TASKS.md`](TASKS.md). The owner of a unit owns its tests.

## Before you say a row is done

FalkorDB is up from `./scripts/setup.sh` (Windows: `powershell -File scripts/setup.ps1`). The image is `falkordb/falkordb:v4.22.1`. Do not change the tag.

Linux, from the repo root, with the venv active:

```bash
ruff check sheldon tests
pytest
pytest tests/test_smoke.py
```

Windows:

```powershell
.\.venv\Scripts\python.exe -m ruff check sheldon tests
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pytest tests/test_smoke.py
```

`pytest` already includes the smoke test. Run the smoke file on its own as well, against that pinned image. Paste the output of all three commands in the PR body.

The claim race and the refute race are expected failures while `CLAIM_IS_STUB` and `REFUTE_IS_STUB` are true. Say that in the PR. Do not treat an xfail as a pass.

## Rules

- Do not mark a `TASKS.md` row done without a test run.
- Write the failing test first for that unit, then make it pass.
- Tests live next to the unit's directory under `tests/`. `sheldon/gate/` is tested from `tests/gate/`. A module that sits directly in `sheldon/`, such as `provenance.py`, is tested from `tests/test_provenance.py`. `tests/test_smoke.py`, `tests/test_races.py`, and `tests/test_contracts.py` stay where they are.
- Do not delete a test. Do not weaken an assertion. Do not flip an xfail, skip a test, or mark it passed to get a green run. An xfail comes off only in the change that makes the assertion true, with the stub flag set to `False` and the `NotImplementedError` gone.
- A flaky test means stop and report. Do not retry it until it goes green.
- `tests/test_contracts.py` is a repo guard. Do not edit it to make a unit pass.

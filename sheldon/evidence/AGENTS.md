# evidence

Hariharan. Status: built. `tests/evidence/test_run.py` shows `record_run` produces `executed: true` evidence through the producer API. `sheldon run -- <cmd>` in `sheldon/cli.py` runs the command and calls `record_run` with the real exit code, sha, and output digest (`tests/evidence/test_sheldon_run.py`). Raw writes are not blocked. The gates' `e.executed = true` checks are what stop an unexecuted node.

This is the trusted producer. The gate modules must not invent Evidence nodes.

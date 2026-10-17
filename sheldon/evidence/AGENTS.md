# evidence

Hariharan. Status: built. `tests/evidence/test_run.py` shows only `record_run` produces `executed: true` evidence through the producer API. Raw writes are not blocked. The gates' `e.executed = true` checks are what stop an unexecuted node.

This is the trusted producer. The gate modules must not invent Evidence nodes.

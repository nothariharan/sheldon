# evidence

Hariharan. Status: built. `tests/evidence/test_run.py` shows `record_run` writes an executed Evidence node from a process exit. A node a model inserts on its own stays unexecuted. The gate does not write Evidence.

This is the trusted producer. The gate modules must not invent Evidence nodes.

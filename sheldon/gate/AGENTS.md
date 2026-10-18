# gate

Hariharan. W1 is `approve.py`. W3 is `done.py`.

`approve` is built. `tests/gate/test_approve.py` shows the graph refusing a bad citation and writing one `FOR` and two `CITES`. A cited claim that is refuted, or that reaches a refuted claim in 1..3 `RELIES_ON` or `DEPENDS_ON` hops, refuses that same write. The refusal reason is the path: claim ids, edge types, and the refuting evidence id. `python -m sheldon.gate.approve` prints it, and `--json` includes it. `claim_done` is built. `tests/gate/test_done.py` shows a done claim returning no approval without a passing executed test run on that sha, and refusing the same hop check.

Do not edit `sheldon/belief/` from this folder. The cascade is W2 and lives there.

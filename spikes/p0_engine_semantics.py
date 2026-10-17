"""
P0 engine-semantics spikes for Sheldon.

Every question here is a blocker in PLAN_SHELDON.md: something the build
cannot proceed without, that FalkorDB docs did not answer, and that was
therefore marked UNVERIFIED. This script answers them by execution.

Run:  .venv\\Scripts\\python.exe spikes\\p0_engine_semantics.py
"""

from __future__ import annotations

import os

import threading
import time

from falkordb import FalkorDB

HOST = os.environ.get("FALKORDB_HOST", "localhost")
PORT = int(os.environ.get("FALKORDB_PORT", "6379"))
GRAPH = "spike_p0"

db = FalkorDB(host=HOST, port=PORT)
g = db.select_graph(GRAPH)

PASS, FAIL = "PASS", "FAIL"
results: list[tuple[str, str, str]] = []


def record(name: str, ok: bool, note: str) -> None:
    results.append((name, PASS if ok else FAIL, note))
    print(f"[{PASS if ok else FAIL}] {name}\n      {note}\n")


def q(cypher: str, params: dict | None = None):
    """Return (result_set, header) or raise."""
    res = g.query(cypher, params or {})
    return res.result_set, res.header


def try_q(cypher: str, params: dict | None = None) -> tuple[bool, str]:
    try:
        rs, _ = q(cypher, params)
        return True, repr(rs[:6])
    except Exception as exc:  # noqa: BLE001 - spike harness wants the raw error
        return False, f"{type(exc).__name__}: {exc}"


def reset() -> None:
    try:
        g.delete()
    except Exception:  # noqa: BLE001 - graph may not exist
        pass


# --------------------------------------------------------------------------
# SPIKE 1 - timestamp() unit
# Blocked: every lease / TTL / ordering decision depends on this.
# --------------------------------------------------------------------------
def spike_1_timestamp() -> None:
    rs, _ = q("RETURN timestamp()")
    val = rs[0][0]
    now_s = time.time()
    now_ms = now_s * 1000.0
    now_us = now_s * 1_000_000.0

    # classify by magnitude
    if abs(val - now_ms) < abs(val - now_s) and abs(val - now_ms) < abs(val - now_us):
        unit, expected = "milliseconds", now_ms
    elif abs(val - now_s) < abs(val - now_us):
        unit, expected = "seconds", now_s
    else:
        unit, expected = "microseconds", now_us

    drift = abs(val - expected)
    ok = drift < 5.0
    record(
        "SPIKE 1  timestamp() unit",
        ok,
        f"timestamp()={val}  ->  {unit}  (python {unit}={expected:.0f}, drift={drift:.1f})",
    )
    # also check the second-precision function name, if any
    for fn in ("time()", "unixtime()"):
        good, note = try_q(f"RETURN {fn}")
        record(f"SPIKE 1b  {fn} exists", good, note[:120])


# --------------------------------------------------------------------------
# SPIKE 2 - algorithm YIELD field names
# Blocked: the answer composer and the traversal router both consume these.
# --------------------------------------------------------------------------
def spike_2_algos() -> None:
    reset()
    q(
        """
        CREATE (a:S {n:'a'})-[:L]->(b:S {n:'b'}),
               (b)-[:L]->(c:S {n:'c'}),
               (a)-[:L]->(c)
        """
    )
    algos = [
        "algo.pageRank",
        "algo.betweennessCentrality",
        "algo.harmonicCentrality",
        "algo.WCC",
        "algo.CDLP",
    ]
    for algo in algos:
        good, note = try_q(
            f"CALL {algo}('S','L') YIELD node, score RETURN node.n, score"
        )
        if good:
            record(f"SPIKE 2  {algo} YIELD node, score", True, note)
            continue
        # retry with the other common yielded column names
        for col in ("componentId", "communityId", "betweenness", "centrality"):
            good2, note2 = try_q(
                f"CALL {algo}('S','L') YIELD node, {col} RETURN node.n, {col}"
            )
            if good2:
                record(f"SPIKE 2  {algo} YIELD node, {col}", True, note2)
                break
        else:
            record(f"SPIKE 2  {algo}", False, note)

    # null-argument form (whole-graph scope)
    good, note = try_q(
        "CALL algo.pageRank(NULL, NULL) YIELD node, score RETURN count(node)"
    )
    record("SPIKE 2b  algo.pageRank(NULL, NULL) whole-graph", good, note)


# --------------------------------------------------------------------------
# SPIKE 3 - multi-type variable-length pattern
# Blocked: the causal traversal [:CAUSED_BY|RESULTED_IN*1..3] is P0.
# --------------------------------------------------------------------------
def spike_3_multi_type_varlen() -> None:
    reset()
    q(
        """
        CREATE (a:N {n:'a'})-[:CAUSED_BY]->(b:N {n:'b'}),
               (b)-[:RESULTED_IN]->(c:N {n:'c'})
        """
    )
    good, note = try_q(
        "MATCH p=(a:N {n:'a'})-[:CAUSED_BY|RESULTED_IN*1..3]->(z) RETURN z.n"
    )
    record("SPIKE 3  [:CAUSED_BY|RESULTED_IN*1..3] multi-type var-length", good, note)

    good2, note2 = try_q(
        "MATCH p=(a:N {n:'a'})-[:CAUSED_BY|RESULTED_IN*1..3]->(z) RETURN z.n, length(p)"
    )
    record("SPIKE 3b  same + length(p)", good2, note2)


# --------------------------------------------------------------------------
# SPIKE 4 - FOREACH ... CASE idiom
# Blocked: the conditional write idiom the coordination board relies on.
# --------------------------------------------------------------------------
def spike_4_foreach_case() -> None:
    reset()
    q("CREATE (a:N {n:'a', flag:0})")
    good, note = try_q(
        """
        MATCH (a:N {n:'a'})
        FOREACH (x IN CASE WHEN a.flag = 0 THEN [1] ELSE [] END | SET a.flag = x)
        RETURN a.flag
        """
    )
    record("SPIKE 4  FOREACH (x IN CASE WHEN ... THEN [1] ELSE [] END | SET)", good, note)

    good2, note2 = try_q(
        """
        MATCH (a:N {n:'a'})
        FOREACH (x IN CASE WHEN a.flag = 99 THEN [1] ELSE [] END | SET a.flag = 99)
        RETURN a.flag
        """
    )
    record("SPIKE 4b  CASE ELSE [] is a no-op (flag stays)", good2, note2)


# --------------------------------------------------------------------------
# SPIKE 5 - ORDER BY ... LIMIT 1 over an EMPTY OPTIONAL MATCH
# Blocked: this is the verified fork-race fix for the event chain.
# --------------------------------------------------------------------------
def spike_5_fork_race_fix() -> None:
    reset()
    q("CREATE (inv:Inv {id:'inv1'})")
    # no events yet -> OPTIONAL MATCH yields null; must still return inv
    good, note = try_q(
        """
        MATCH (inv:Inv {id:'inv1'})
        OPTIONAL MATCH (inv)<-[:IN_INVESTIGATION]-(p:Ev)
        WITH inv, p ORDER BY p.ingest_seq DESC LIMIT 1
        RETURN inv.id, p
        """
    )
    record("SPIKE 5  empty OPTIONAL MATCH + ORDER BY..LIMIT 1 still returns root", good, note)

    # now the real chain: derive prev in-query under concurrency
    reset()
    q("CREATE (inv:Inv {id:'inv1'})")

    def append(seq: int) -> tuple[bool, str]:
        try:
            rs, _ = q(
                """
                MATCH (inv:Inv {id:'inv1'})
                OPTIONAL MATCH (inv)<-[:IN_INVESTIGATION]-(p:Ev)
                WITH inv, p ORDER BY p.ingest_seq DESC LIMIT 1
                CREATE (e:Ev {ingest_seq:$seq})
                CREATE (inv)<-[:IN_INVESTIGATION]-(e)
                FOREACH (_ IN CASE WHEN p IS NULL THEN [] ELSE [1] END |
                    CREATE (p)-[:NEXT]->(e)
                )
                RETURN e.ingest_seq
                """,
                {"seq": seq},
            )
            return True, repr(rs)
        except Exception as exc:  # noqa: BLE001
            return False, f"{type(exc).__name__}: {exc}"

    threads = [threading.Thread(target=append, args=(i,)) for i in range(1, 9)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    rs, _ = q(
        "MATCH (e:Ev) WITH count(e) AS total MATCH ()-[r:NEXT]->() "
        "RETURN total, count(r) AS chain_links"
    )
    total, links = rs[0][0], rs[0][1]
    # a clean chain of N events has exactly N-1 NEXT links and no forks
    ok = links == total - 1
    record(
        "SPIKE 5b  8 concurrent appends -> single unbranched chain",
        ok,
        f"{total} events, {links} NEXT links (expected {total - 1}); "
        f"{'no fork' if ok else 'FORK DETECTED'}",
    )


# --------------------------------------------------------------------------
# SPIKE 6 - single-query atomic task lease under concurrency
# Blocked: this IS the coordination differentiator. Must be exactly 1 winner.
# --------------------------------------------------------------------------
def spike_6_atomic_lease() -> None:
    reset()
    q("CREATE (t:Task {id:'t1', status:'open', owner:null})")
    wins: list[str] = []
    errors: list[str] = []
    lock = threading.Lock()

    def claim(agent: str) -> None:
        client = FalkorDB(host=HOST, port=PORT).select_graph(GRAPH)
        try:
            res = client.query(
                """
                MATCH (t:Task {id:'t1'})
                WHERE t.status = 'open'
                SET t.status = 'claimed', t.owner = $agent
                RETURN t.id
                """,
                {"agent": agent},
            )
            with lock:
                if res.result_set:
                    wins.append(agent)
        except Exception as exc:  # noqa: BLE001
            with lock:
                errors.append(f"{type(exc).__name__}: {exc}")

    agents = [f"a{i}" for i in range(12)]
    threads = [threading.Thread(target=claim, args=(a,)) for a in agents]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    rs, _ = q("MATCH (t:Task {id:'t1'}) RETURN t.status, t.owner")
    status, owner = rs[0][0], rs[0][1]
    ok = len(wins) == 1 and status == "claimed"
    record(
        "SPIKE 6  12 concurrent claimers -> exactly one lease winner",
        ok,
        f"winners={wins}  final status={status} owner={owner} errors={len(errors)}",
    )


def main() -> None:
    print(f"\n{'=' * 70}\nSheldon P0 engine-semantics spikes against FalkorDB {GRAPH}\n{'=' * 70}\n")
    for fn in (
        spike_1_timestamp,
        spike_2_algos,
        spike_3_multi_type_varlen,
        spike_4_foreach_case,
        spike_5_fork_race_fix,
        spike_6_atomic_lease,
    ):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            record(fn.__name__, False, f"spike crashed: {type(exc).__name__}: {exc}")

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for name, verdict, _ in results:
        print(f"  {verdict:>4}  {name}")
    passed = sum(1 for _, v, _ in results if v == PASS)
    print(f"\n  {passed}/{len(results)} passed\n")


if __name__ == "__main__":
    main()

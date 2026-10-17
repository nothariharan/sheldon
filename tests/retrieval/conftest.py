"""One fixture graph for the R1 recall and S0 tests, in the seed's vocabulary.

The fixture is not the seed. Ids follow the plan's demo (INC-12, C-7, E-41)
so the S0-vs-R1 comparison reads the same way it will on the real seed.
"""

import pytest

from sheldon.db import connect
from sheldon.retrieval.s0 import create_s0_indexes

GRAPH = "test_retrieval"

# checkout/cache.py co-changes with checkout/session.py, which INC-12 touched.
# billing/invoice.py is two hops out, so R1 must not reach INC-20.
FIXTURE = """
CREATE (cache:File {path: 'checkout/cache.py'}),
       (session:File {path: 'checkout/session.py'}),
       (invoice:File {path: 'billing/invoice.py'}),
       (readme:File {path: 'docs/readme.md'}),
       (cache)-[:CO_CHANGED_WITH {frequency: 4}]->(session),
       (session)-[:CO_CHANGED_WITH {frequency: 2}]->(invoice),
       (:PR {number: 101, head_sha: 'abc'})-[:CHANGES]->(cache),
       (:PR {number: 102, head_sha: 'def'})-[:CHANGES]->(readme),
       (inc12:Incident {id: 'INC-12', title: 'Checkout times out under cache TTL stampede'}),
       (inc20:Incident {id: 'INC-20', title: 'Invoice totals off by one cent'}),
       (inc12)-[:TOUCHED]->(session),
       (inc20)-[:TOUCHED]->(invoice),
       (c7:Claim {id: 'C-7', kind: 'fix', status: 'refuted',
                  text: 'Raising the cache TTL fixes the checkout timeout'}),
       (c8:Claim {id: 'C-8', kind: 'root_cause', status: 'open',
                  text: 'Session lock contention causes the checkout timeout'}),
       (c9:Claim {id: 'C-9', kind: 'root_cause', status: 'open',
                  text: 'Rounding in invoice totals'}),
       (inc12)-[:HAS_CAUSE]->(c7),
       (inc12)-[:HAS_CAUSE]->(c8),
       (inc20)-[:HAS_CAUSE]->(c9),
       (c7)-[:REFUTED_BY]->(:Evidence {id: 'E-41', kind: 'ci_run', executed: true, exit_code: 1})
"""


@pytest.fixture(scope="module")
def graph() -> str:
    db = connect()
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001 - graph may not exist yet
        pass
    db.select_graph(GRAPH).query(FIXTURE)
    create_s0_indexes(GRAPH)
    create_s0_indexes(GRAPH)  # second call must not raise
    yield GRAPH
    db.select_graph(GRAPH).delete()


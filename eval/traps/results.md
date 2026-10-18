# Trap suite

Date: 2026-10-18
Main sha: ec328d9fab80c95df611a366b3a8efb2f031e2f7
Image: falkordb/falkordb:v4.22.1
Command: `python -m eval.traps`

| Arm | Bad blocked | Good wrongly blocked | Median ms |
| --- | --- | --- | --- |
| no-memory | 0/14 | 0/7 | 0.00 |
| search-only baseline | 8/14 | 1/7 | 5.20 |
| sheldon | 7/14 | 0/7 | 3.82 |

Sheldon wrongly blocked good actions: none.

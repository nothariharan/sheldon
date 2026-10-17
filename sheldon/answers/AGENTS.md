# answers (p3)

Status: built. Satyansh owns this folder. The comment is built from traversal rows. It does not decide the gate.

Owns the prose, the citations, and abstention.

## Contract

`compose` takes a question and an evidence bundle and returns `answer`, `citations`, `path`, and `abstained`. Every citation is an event id that was in the bundle. If the bundle is not enough, abstain. Do not invent ids or paths.

This function does not change hypothesis status. The refute decision is `sheldon.belief`.

## Gotchas

- Paper numbers are not Sheldon results. Do not put them in a return value or a comment as if we measured them.
- Show the Cypher the retrieval step ran. Don't paraphrase it into a claim about speed.
- Unanswerable questions are part of the demo, not an error.

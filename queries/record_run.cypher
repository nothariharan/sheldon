// Trusted Evidence producer. One statement.
// executed is a literal, not a parameter, so a caller cannot mint a pass.

CREATE (e:Evidence {
  id: $id,
  kind: $kind,
  command: $command,
  sha: $sha,
  executed: true,
  exit_code: $exit_code,
  output_digest: $output_digest,
  model: $model,
  session: $session
})
RETURN e.id AS id

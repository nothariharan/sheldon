// Do not run this until EMBEDDING_DIM is set in sheldon/schema.py.
// Re-embedding means rebuilding the index. Lock the model and the dimension first.
//
// CREATE VECTOR INDEX FOR (e:Event) ON (e.embedding)
// OPTIONS {dimension: <EMBEDDING_DIM>, similarityFunction: 'cosine'}

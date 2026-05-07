# Embedding Models are provider configurations

An Embedding Model is a LawSearch configuration used to build and query a Vector Store, not just an opaque provider model string. Its `id` is the stable LawSearch config id persisted on Vector Stores and in `.embedding_model`; its `name` is the provider model name; its `provider` selects the embedding implementation; and its `dimensions` records vector dimensionality. This lets incompatible configurations such as `voyage-4-large-2048` stay distinct while still calling Voyage with `model="voyage-4-large"`.

## Why

Vector Store compatibility depends on provider, provider model, dimensions, and provider-specific options such as Voyage query/document input types. We considered inferring behavior from model-name prefixes, but that would hide retrieval-critical configuration inside scattered conditionals. The chosen shape keeps the persisted identity explicit while avoiding a database migration for provider-specific options; those options live in a code registry until they need to become editable data.

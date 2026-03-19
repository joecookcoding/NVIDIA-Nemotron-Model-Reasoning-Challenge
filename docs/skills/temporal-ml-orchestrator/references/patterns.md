# Temporal Patterns

- Workflows should accept ids and compact config only.
- Activities should load full records from storage.
- Retries belong on side-effecting activities, not on workflow logic that mutates selection state.
- Persist every promotion decision before launching the next cycle.


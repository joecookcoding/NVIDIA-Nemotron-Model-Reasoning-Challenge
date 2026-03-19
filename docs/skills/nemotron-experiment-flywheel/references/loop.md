# Experiment Loop

1. Pick one benchmark subset and one seed.
2. Lock a baseline prompt and provider.
3. Sweep one axis.
4. Compare score, latency, and candidate behavior.
5. Rerank if candidate quality diverges from raw score.
6. Promote exactly one winner into the next cycle.


# Compliance Matrix

| Area | Current Assumption | Source Status | Action |
| --- | --- | --- | --- |
| Submission schema | Default to `id,answer` CSV | Unconfirmed | Replace once Kaggle sample submission is captured |
| External API usage | Assume hosted APIs are allowed only for local experimentation | Unconfirmed | Verify whether inference must run entirely inside Kaggle |
| Internet access in final submission | Assume restricted | Unconfirmed | Verify notebook/network rules |
| Model weights | Hosted Nemotron-compatible endpoints for local loops | Unconfirmed | Verify whether local weights or fine-tuned checkpoints are allowed |
| Runtime budget | Keep submission builder decoupled from live APIs | Unconfirmed | Reconcile with Kaggle notebook/runtime limits |
| Eval metric | Internal exact-match only for the local sample benchmark | Unconfirmed | Replace once official metric is frozen |

## Exit Criteria

- Every row above references a direct quote or screenshot from Kaggle.
- `docs/competition/source_capture.md` has complete content.
- `artifacts/submissions/` output matches the official sample format.


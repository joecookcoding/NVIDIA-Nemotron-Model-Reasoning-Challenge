# Compliance Matrix

| Area | Current Assumption | Source Status | Action |
| --- | --- | --- | --- |
| Submission schema | `submission.zip` containing a compatible rank `<= 32` LoRA adapter for `NVIDIA Nemotron-3-Nano-30B` | Confirmed from competition and data page captures | Remove local CSV assumptions from submission flows |
| External API usage | External data, models, and tools are allowed unless prohibited, but must be reasonably accessible to all and of minimal cost | Partial | Document any external dependency against the rules' reasonableness standard |
| Internet access in final submission | Still not officially captured from the rules/runtime pages | Unconfirmed | Verify notebook/network rules |
| Model weights | Final evaluation loads `NVIDIA Nemotron-3-Nano-30B` with the submitted LoRA adapter via `vLLM` | Confirmed from evaluation capture | Align notebook outputs and local assumptions to the base-model-plus-LoRA path |
| Runtime budget | Kaggle evaluation parameters are explicitly listed on the competition page | Confirmed | Match local experimentation to listed evaluation parameters where relevant |
| Eval metric | Accuracy with boxed-answer extraction and heuristic fallback is confirmed, but the pasted tolerance value is incomplete | Partial | Capture the clean tolerance value and metric source page |

## Additional Captured Constraints

- Prize eligibility requires a public Kaggle notebook and solution write-up.
- Competition data use is governed by `CC BY 4.0` and requires acknowledgement and attribution to the `NVIDIA Research team`.
- Private code sharing outside an official Kaggle team is not allowed.
- The repo should preserve reproducibility because winners may need to provide training code, inference code, and environment details.

## Exit Criteria

- Every row above references a direct quote or screenshot from Kaggle.
- `docs/competition/source_capture.md` has complete content.
- `artifacts/submissions/` output matches the official sample format.

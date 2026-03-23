# PRD JSON Shape

Use a compact Ralph-style task list at repo root as `prd.json`.

## Recommended Shape

```json
{
  "branchName": "submission-demo-hardening",
  "objective": "Produce a stable first submission.zip and document the next upgrade path.",
  "userStories": [
    {
      "id": "S1",
      "title": "Capture the official evaluation and rules constraints in repo docs",
      "priority": 1,
      "passes": false,
      "acceptanceCriteria": [
        "Competition docs in docs/competition reflect the pasted Kaggle pages",
        "Submission contract no longer assumes CSV output",
        "Remaining unknowns are listed explicitly"
      ],
      "checks": [
        "Read docs/competition/source_capture.md",
        "Read docs/competition/submission_contract.md"
      ],
      "notes": "Do this before changing packaging logic."
    },
    {
      "id": "S2",
      "title": "Run the submission demo notebook path and verify submission.zip packaging assumptions",
      "priority": 2,
      "passes": false,
      "acceptanceCriteria": [
        "The notebook path produces submission.zip",
        "The adapter package includes adapter_config.json",
        "Any unresolved packaging details are recorded"
      ],
      "checks": [
        "Inspect notebook packaging cells",
        "Verify docs/competition/evaluation.md alignment"
      ],
      "notes": "Keep this focused on packaging, not score optimization."
    }
  ]
}
```

## Sizing Guidance

Good story sizes:

- capture one official rules page
- patch one notebook stability issue
- add one deterministic training control
- verify one packaging assumption
- add one evaluation or build check

Bad story sizes:

- win the competition
- redesign the whole training pipeline
- refactor the whole repo
- build the entire submission system

## Priority Guidance

- `1` means blocker or highest-value next step.
- Lower numbers should usually unblock higher-risk work.
- Reorder priorities instead of stuffing multiple goals into one story.

# Competition Data

Source URL: `https://www.kaggle.com/competitions/nvidia-nemotron-model-reasoning-challenge/data`

Capture date: `2026-03-22`

Capture method: user-pasted content from the authenticated Kaggle data page.

## Dataset Description

`This dataset comprises a collection of logical reasoning puzzles requiring the identification and application of underlying transformation rules. The puzzles cover various domains, such as bit manipulation and algebraic equations.`

## Files

### `train.csv`

The page describes `train.csv` as:

`The training set containing puzzles and their corresponding solutions.`

Fields:

- `id` - A unique identifier for each puzzle
- `prompt` - The puzzle description, including input-output examples and the specific instance to be solved
- `answer` - The ground truth solution for the puzzle

### `test.csv`

The page describes `test.csv` as:

`A sample test set to help you author your submissions. When your submission is scored, this will be replaced by a test set of several hundred problems.`

Fields:

- `id` - A unique identifier for each puzzle
- `prompt` - As in `train.csv`

## Submission Signal Repeated On The Data Page

Exact line captured from the page:

`Note that your submission must be a file submission.zip containing a LoRA adapter. See the Evaluation page for details.`

## Dataset Metadata

- `Files`: `2`
- `Size`: `3.07 MB`
- `Type`: `csv`
- `License`: `Attribution 4.0 International (CC BY 4.0)`

## Download Commands Captured

### Kaggle CLI

`kaggle competitions download -c nvidia-nemotron-model-reasoning-challenge`

### KaggleHub

`kagglehub.competition_download('nvidia-nemotron-model-reasoning-challenge')`

# Competition Rules

Source: user-pasted content from the Kaggle Rules page for `NVIDIA Nemotron Model Reasoning Challenge`

Capture date: `2026-03-22`

## Competition-Specific Terms

- Competition title: `NVIDIA Nemotron 3 Reasoning Challenge`
- Competition sponsor: `NVIDIA`
- Sponsor address: `2788 San Tomas Expressway, Santa Clara, California 95051`
- Competition website: `https://www.kaggle.com/competitions/nvidia-nemotron-model-reasoning-challenge`
- Total prizes available: `$106,388`
- Winner license type: `CC BY 4.0`
- Data access and use: `CC BY 4.0`

## Competition-Specific Rules

### Team Limits

- Maximum team size: `5`
- Team mergers are allowed.
- To merge, the combined team must have a total submission count less than or equal to the maximum allowed as of the Team Merger Deadline.
- The maximum allowed is the number of submissions per day multiplied by the number of days the competition has been running.

### Submission Limits

- Maximum submissions per day: `5`
- Final submissions selectable for judging: up to `2`

### Competition Timeline

- Timeline dates are reflected on the competition `Overview > Timeline` page.

### Competition Data

#### Data Access And Use

- You may access and use the Competition Data for any purpose, whether commercial or non-commercial, including participating in the competition, Kaggle forums, academic research, and education.
- Competition Data is subject to `CC BY 4.0`.
- Any use of the data must include acknowledgement and attribution to the `NVIDIA Research team`.

#### Data Security

- Use reasonable and suitable measures to prevent access by persons who have not formally agreed to the Rules.
- Do not transmit, duplicate, publish, redistribute, or otherwise make Competition Data available to any party not participating in the competition.
- Notify Kaggle immediately upon learning of possible unauthorized transmission or access.

### Winner License

If you are a competition winner:

- You grant the Competition Sponsor an open-source license to the winning Submission and the source code used to generate it under `CC BY 4.0`.
- That license may not limit commercial use of the code or model containing or depending on such code.
- Commercially available third-party software that the Sponsor can procure without undue expense does not need to be re-licensed by you.
- Input data or pre-trained models with an incompatible license do not need to be re-licensed by you under the winning open-source requirement.

### Winner Documentation

The rules state that winners may be required to provide:

- a detailed description of how the winning Submission was generated,
- methodology detailed enough to reproduce the approach,
- architecture, preprocessing, loss function, training details, and hyperparameters,
- a code repository link with complete and detailed reproduction instructions.

### External Data And Tools

- External data may be used to develop and test submissions.
- External data must either be publicly available and equally accessible to all participants at no cost, or satisfy the `Reasonableness` criteria.
- Use of external data and models is acceptable unless specifically prohibited by the Host.
- External LLMs, datasets, and tools must be reasonably accessible to all and of minimal cost.
- The rules give an example that a small subscription charge may be acceptable, while a proprietary dataset costing more than a competition prize would not be considered reasonable.

### Automated Machine Learning Tools

- AML tools may be used if the participant or team has an appropriate license and can still comply with the competition rules.

### Eligibility Note

- Employees, interns, contractors, officers, and directors of Competition Entities may not enter or participate unless otherwise stated or allowed.

### Winner's Obligations

As a condition of receiving a prize, a winner must:

- deliver the final model software code used to generate the winning Submission,
- include associated documentation,
- provide code capable of generating the winning Submission,
- include training code, inference code, and a description of the required computational environment,
- identify commercially available software used if that software is not owned by the participant,
- publish a public Kaggle notebook and solution write-up documenting the methods used to generate the submission.

The rules explicitly state:

- `To be eligible for any prize, teams must publish a public Kaggle notebook and solution Writeup documenting the methods used to generate their submission.`

## High-Signal General Rules

### Accounts And Teams

- You may make submissions only under one unique Kaggle account.
- You may not sign up or submit from multiple accounts.
- You may join or form only one team.
- Private sharing outside of teams is not permitted.
- Public code sharing is allowed if shared on Kaggle for the benefit of all competitors and if it does not violate third-party rights.

### Submission Requirements

- Submissions must follow the manner, format, and other requirements stated on the Competition Website.
- Submissions may not use hand labeling or human prediction of validation or test data, except where explicitly allowed.
- Late, incomplete, damaged, altered, counterfeit, fraudulent, or non-compliant submissions may be disqualified.

### Competition Code

- During the competition period, private sharing of Competition Code is not allowed unless specifically permitted or a team merger occurs.
- Publicly shared Competition Code is deemed licensed under an Open Source Initiative-approved license that does not limit commercial use.
- Unless otherwise stated, open source code used in a submission must be under an OSI-approved license that does not limit commercial use.

### Leaderboards And Winners

- Public leaderboard uses a public test sample.
- Private leaderboard determines final standing.
- Ties are broken by earliest submission.

## Practical Implications For This Repo

- We should assume `5` submissions per day and `2` final submissions.
- Team workflows must avoid any private code sharing outside the official Kaggle team.
- External tools and data are allowed, but we should document accessibility and cost.
- Prize eligibility requires a public Kaggle notebook plus a write-up.
- If we want prize eligibility, the final workflow must be reproducible enough to hand over training code, inference code, environment description, and methodology.

SHELL := /bin/bash

.PHONY: backend-dev backend-worker backend-compile frontend-install frontend-dev frontend-build skill-validate kaggle-import

backend-dev:
	cd apps/backend && python3 -m uvicorn nemotron_platform.main:app --reload --app-dir src

backend-worker:
	cd apps/backend && python3 -m nemotron_platform.temporal.worker

backend-compile:
	python3 -m compileall apps/backend/src

frontend-install:
	bash -lc "source $$HOME/.nvm/nvm.sh && npm install"

frontend-dev:
	bash -lc "source $$HOME/.nvm/nvm.sh && npm run frontend:dev"

frontend-build:
	bash -lc "source $$HOME/.nvm/nvm.sh && npm run frontend:build"

skill-validate:
	python3 /home/code/.codex/skills/.system/skill-creator/scripts/quick_validate.py docs/skills/nemotron-competition-ops
	python3 /home/code/.codex/skills/.system/skill-creator/scripts/quick_validate.py docs/skills/nemotron-experiment-flywheel
	python3 /home/code/.codex/skills/.system/skill-creator/scripts/quick_validate.py docs/skills/synthetic-data-curator
	python3 /home/code/.codex/skills/.system/skill-creator/scripts/quick_validate.py docs/skills/temporal-ml-orchestrator

kaggle-import:
ifndef SOURCE
	$(error SOURCE is required, for example: make kaggle-import SOURCE=/path/to/kaggle_run_<id>.zip)
endif
	python3 scripts/import_kaggle_run.py "$(SOURCE)"

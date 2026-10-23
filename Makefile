# Loads .env if present
ifneq (,$(wildcard .env))
include .env
export
endif

.PHONY: test baseline eval eval-judge smoke

test:
	python -m pytest -q

baseline:
	python -m evals.run_evals --agent baseline --no-gate

eval:
	python -m evals.run_evals --agent claude

eval-judge:
	python -m evals.run_evals --agent claude --judge

smoke:
	python -m evals.run_evals --agent claude --limit 20 --no-gate

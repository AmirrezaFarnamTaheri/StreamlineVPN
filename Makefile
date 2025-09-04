PY      ?= python
NOX     ?= nox

.PHONY: test smoke deps-report

test:
	SKIP_NETWORK=true $(NOX) -s tests

smoke:
	PYTHONPATH=src $(NOX) -s smoke

deps-report:
	PYTHONPATH=src $(NOX) -s deps_report


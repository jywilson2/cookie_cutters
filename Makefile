PYTHON ?= python3
export PYTHONPATH := src

.PHONY: generate test

generate:
	$(PYTHON) -m cookie_cutter.generate

test:
	$(PYTHON) -m pytest

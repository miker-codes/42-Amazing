PYTHON := python3
VENV   := .venv
BIN    := $(VENV)/bin

.PHONY: install run debug clean lint lint-strict package test

## Create the venv and install dev tools + the reusable mazegen package
## in editable mode (PEP 668 blocks `pip install` outside a venv on Arch).
install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements-dev.txt
	$(BIN)/pip install -e ./mazegen

## Execute the main script (reads config.txt by default).
run:
	$(BIN)/python a_maze_ing.py config.txt

## Same, but dropping into pdb.
debug:
	$(BIN)/python -m pdb a_maze_ing.py config.txt

## Remove caches and build intermediates (keeps the committed .whl at root).
clean:
	find . -type d -name '__pycache__' -not -path './.venv/*' -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache mazegen/build mazegen/dist mazegen/*.egg-info

## Mandatory lint flags from the subject.
lint:
	$(BIN)/flake8 .
	$(BIN)/mypy . --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

## Optional, stricter lint pass.
lint-strict:
	$(BIN)/flake8 .
	$(BIN)/mypy . --strict

## Rebuild the mazegen-*.whl / .tar.gz deliverable straight into the repo root.
package:
	$(BIN)/python -m build --outdir . ./mazegen

## Not graded, but useful during development.
test:
	$(BIN)/pytest -q

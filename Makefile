PYTHON = python3
MAP ?= maps/easy/01_linear_path.txt
ARGS ?= --gui
MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

install:
	$(PYTHON) -m pip install flake8 mypy pygame

run:
	$(PYTHON) main.py $(MAP)

run-visual:
	$(PYTHON) main.py $(MAP) $(ARGS)

debug:
	$(PYTHON) -m pdb main.py $(MAP) $(ARGS)

clean:
	find . -path ./.venv -prune -o -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache

lint:
	flake8 .
	mypy . $(MYPY_FLAGS)

lint-strict:
	flake8 .
	mypy . --strict

.PHONY: install run debug clean lint lint-strict

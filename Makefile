PYTHON = python3
MAP ?= maps/easy/01_linear_path.txt
ARGS ?= --gui
LEVEL ?= easy
MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

.PHONY: level install run debug clean lint lint-strict test

install:
	$(PYTHON) -m pip install flake8 mypy pytest pygame

run:
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

test:
	$(PYTHON) -m pytest -q

level:
	$(PYTHON) main.py --level=$(LEVEL) $(ARGS)

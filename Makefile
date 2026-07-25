PYTHON := $(CURDIR)/.venv/bin/python

.PHONY: help install metadata metadata-check test run build package clean

help:
	@printf '%s\n' \
		'install         Install locked runtime and development dependencies' \
		'metadata        Regenerate src/app_metadata.py from pyproject.toml' \
		'metadata-check  Verify generated application metadata is current' \
		'test            Run the unit test suite' \
		'run             Run BitCap IPReporter from source' \
		'build           Build a portable binary for the current platform' \
		'package         Build portable and installer/package artifacts' \
		'clean           Remove generated build artifacts'

install:
	poetry install --with dev --no-interaction

metadata:
	$(PYTHON) tools/project_metadata.py

metadata-check:
	$(PYTHON) tools/project_metadata.py --check

test: metadata-check
	cd src && $(PYTHON) -m unittest discover tests/

run: metadata-check
	$(PYTHON) src/main.py

build: metadata-check
	$(PYTHON) tools/build_app.py --portable-only

package: metadata-check
	$(PYTHON) tools/build_app.py

clean:
	rm -rf dist build

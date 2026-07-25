PYTHON := $(CURDIR)/.venv/bin/python
PYSIDE_UIC := $(CURDIR)/.venv/bin/pyside6-uic
PYSIDE_RCC := $(CURDIR)/.venv/bin/pyside6-rcc

.PHONY: help install metadata metadata-check test run build package clean gen-uic gen-rcc

help:
	@printf '%s\n' \
		'install         Install locked runtime and development dependencies' \
		'metadata        Regenerate src/app_metadata.py from pyproject.toml' \
		'metadata-check  Verify generated application metadata is current' \
		'test            Run the unit test suite' \
		'run             Run BitCap IPReporter from source' \
		'build           Build a portable binary for the current platform' \
		'package         Build portable and installer/package artifacts' \
		'clean           Remove generated build artifacts' \
		'gen-uic         Generate UI Python files from .ui forms' \
		'gen-rcc         Generate resource Python file from .qrc resources'

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

gen-uic:
	cd src/ui && $(PYSIDE_UIC) forms/mainwindow.ui -o MainWindow.py && \
	$(PYSIDE_UIC) forms/about.ui -o About.py && \
	$(PYSIDE_UIC) forms/confirmation.ui -o Confirmation.py

gen-rcc:
	cd src/ui && $(PYSIDE_RCC) ipr.qrc -o resources.py

clean:
	rm -rf dist build

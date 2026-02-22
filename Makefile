# ========= CONFIG =========
VENV=.venv
PYTHON=python3
PIP=$(VENV)/bin/pip
PY=$(VENV)/bin/python
SCRIPT=azan_service.py
# ==========================

.PHONY: build run clean

build:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "Upgrading pip..."
	$(PIP) install --upgrade pip
	@echo "Installing dependencies..."
	$(PIP) install -r requirements.txt
	@echo "Build complete."

run:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Virtualenv not found. Run 'make build' first."; \
		exit 1; \
	fi
	@echo "Running azan service..."
	$(PY) $(SCRIPT)

clean:
	@echo "Removing virtual environment..."
	rm -rf $(VENV)
	@echo "Clean complete."

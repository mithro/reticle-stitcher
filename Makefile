.PHONY: help install install-pdf install-reticle install-all clean clean-venv test-pdf

# Default Python version
PYTHON := python3
VENV := .venv
UV := uv

# Detect if uv is installed
UV_EXISTS := $(shell command -v uv 2> /dev/null)

help: ## Show this help message
	@echo "Reticle Stitcher - Available targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick start:"
	@echo "  make install-pdf     # Install PDF generation dependencies only"
	@echo "  make install-all     # Install all dependencies (PDF + OASIS generation)"

$(VENV)/bin/activate:
	@echo "Creating Python virtual environment..."
ifndef UV_EXISTS
	@echo "⚠️  uv not found, falling back to standard venv + pip"
	@echo "   Install uv for faster package installation: curl -LsSf https://astral.sh/uv/install.sh | sh"
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
else
	@echo "✓ Using uv for fast package installation"
	$(UV) venv $(VENV)
endif

install-pdf: $(VENV)/bin/activate ## Install PDF generation dependencies only
	@echo "Installing PDF generation dependencies..."
ifndef UV_EXISTS
	$(VENV)/bin/pip install -r requirements.txt
else
	$(UV) pip install -r requirements.txt --python $(VENV)/bin/python
endif
	@echo "✓ PDF generation dependencies installed"
	@echo ""
	@echo "Activate the virtualenv with:"
	@echo "  source $(VENV)/bin/activate"
	@echo ""
	@echo "Generate PDF documentation:"
	@echo "  $(VENV)/bin/python generate_reticle_pdf.py tilemap.csv -o output.pdf"

install-reticle: $(VENV)/bin/activate ## Install OASIS generation dependencies only
	@echo "Installing OASIS generation dependencies..."
ifndef UV_EXISTS
	$(VENV)/bin/pip install -r requirements-reticle.txt
else
	$(UV) pip install -r requirements-reticle.txt --python $(VENV)/bin/python
endif
	@echo "✓ OASIS generation dependencies installed"

install-all: install-pdf install-reticle ## Install all dependencies (PDF + OASIS)
	@echo ""
	@echo "✓ All dependencies installed"
	@echo ""
	@echo "Usage:"
	@echo "  source $(VENV)/bin/activate"
	@echo "  python reticle_stitcher.py manifest.csv tilemap.csv"
	@echo "  python generate_reticle_pdf.py tilemap.csv -o docs.pdf"

install: install-pdf ## Alias for install-pdf (default)

test-pdf: install-pdf ## Generate a test PDF with sample data
	@echo "Generating test PDF..."
	@if [ ! -f test_tilemap.csv ]; then \
		echo "Creating test tilemap..."; \
		printf "1,2,3,4,5,6,7,8\n9,10,11,12,13,14,15,16\n17,18,19,20,21,22,23,24\n25,26,27,28,29,30,31,32\n33,34,35,36,37,38,39,40\n" > test_tilemap.csv; \
	fi
	$(VENV)/bin/python generate_reticle_pdf.py test_tilemap.csv -o test_reticle.pdf
	@echo "✓ Test PDF generated: test_reticle.pdf"
	@rm -f test_tilemap.csv

clean: ## Remove generated files (keeps virtualenv)
	@echo "Cleaning generated files..."
	rm -f test_tilemap.csv test_reticle.pdf
	rm -f reticle.pdf
	rm -rf __pycache__
	@echo "✓ Cleaned"

clean-venv: clean ## Remove virtualenv and all generated files
	@echo "Removing virtual environment..."
	rm -rf $(VENV)
	@echo "✓ Virtual environment removed"

# Check if uv is installed
check-uv: ## Check if uv is installed
ifndef UV_EXISTS
	@echo "❌ uv is not installed"
	@echo ""
	@echo "Install uv for faster package installation:"
	@echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
	@echo ""
	@echo "Or use pip (slower):"
	@echo "  make install-pdf"
	@exit 1
else
	@echo "✓ uv is installed at: $(shell which uv)"
	@$(UV) --version
endif

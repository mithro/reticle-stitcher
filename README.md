# Reticle Stitcher

Tool for stitching a full MPW reticle using gf180mcu for delivery to a foundry.

> [!WARNING]
> This tool is WIP.

## Installation

### Quick Start with Makefile

The easiest way to set up dependencies is using the provided Makefile with [uv](https://github.com/astral-sh/uv) (recommended for faster installation):

```bash
# Install uv (optional, but recommended for speed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install PDF generation dependencies only
make install-pdf

# Or install all dependencies (PDF + OASIS generation)
make install-all

# Activate the virtual environment
source .venv/bin/activate
```

The Makefile will automatically fall back to standard `pip` if `uv` is not available.

### Manual Installation

If you prefer not to use the Makefile:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install PDF generation dependencies
pip install -r requirements.txt

# Install OASIS generation dependencies (optional)
pip install -r requirements-reticle.txt
```

### Available Make Targets

```bash
make help            # Show all available targets
make install-pdf     # Install PDF generation dependencies only
make install-reticle # Install OASIS generation dependencies only
make install-all     # Install all dependencies
make test-pdf        # Generate a test PDF
make test-png        # Generate a test PDF and PNG preview (requires poppler-utils)
make clean           # Remove generated files
make clean-venv      # Remove virtualenv and generated files
```

**Note:** The `test-png` target requires `poppler-utils` to be installed for PDF to PNG conversion:
- Ubuntu/Debian: `sudo apt-get install poppler-utils`
- MacOS: `brew install poppler`
- Fedora/RHEL: `sudo dnf install poppler-utils`

## Usage

### Generating the Reticle OASIS File

To run the stitcher, supply the manifest and tile map:

```bash
python3 reticle_stitcher.py manifest-wsmpw1.csv tilemap-wsmpw1.csv
```

You can specify a custom output file:

```bash
python3 reticle_stitcher.py manifest.csv tilemap.csv --output my_reticle.oas
```

### Generating PDF Documentation

To generate a PDF documentation diagram of the reticle layout (similar to [caravel-gf180mcu/docs/reticle.pdf](https://github.com/efabless/caravel-gf180mcu/blob/main/docs/reticle.pdf)), use the separate `generate_reticle_pdf.py` script:

```bash
python3 generate_reticle_pdf.py tilemap-wsmpw1.csv -o reticle_docs.pdf
```

The PDF will include:
- Overall reticle dimensions (32mm × 26mm)
- Grid layout showing all tiles with seal rings
- GF180MCU specifications and calculations
- Dimension annotations
- Project die dimensions

Note: The PDF generation only requires the tilemap CSV file, not the manifest or GDS files.

## Manifest

The manifest contains a list of all projects.

| SLOT | PROJECT  | ID | HASH                             | SOURCE                         |
|------|----------|----|----------------------------------|--------------------------------|
| 1    | project1 | 00000001  | 85eb8b0773f59442c36db690c865bda7 | chips/00000001/chip_top.gds.gz |
| 2    | project2 | 00000002  | 428e06ac9c44dd2e1938d1e345ded193 | chips/00000002/chip_top.gds.gz |
| ...  | ...      | ... | ...                             | ...                            |

For the hash MD5 is used, as it is fast and only used for file validation.

## Tile Map

The tile map is the mapping from slot to tile location.

|    |    |    |    |    |    |    |    |
|----|----|----|----|----|----|----|----|
| 33 | 34 | 35 | 36 | 37 | 38 | 39 | 40 |
| 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 |
| 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
| 9  | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
| 1  | 2  | 3  | 4  | 5  | 6  | 7  | 8  |

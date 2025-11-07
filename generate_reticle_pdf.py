#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Wafer Space PTE. LTD. <info@wafer.space>
# SPDX-License-Identifier: Apache-2.0

"""
Generate PDF documentation diagram of a reticle layout.

This script creates a technical drawing similar to:
https://github.com/efabless/caravel-gf180mcu/blob/main/docs/reticle.pdf

The PDF includes:
- Overall reticle dimensions (32mm × 26mm)
- Grid of tiles with seal rings
- GF180MCU specifications and calculations
- Dimension annotations
- Project die dimensions
"""

import os
import csv
import argparse

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# Constants - must match those in reticle_stitcher.py
RETICLE_WIDTH = 32000  # micrometers
RETICLE_HEIGHT = 26000  # micrometers
SEAL_RING_SIZE = 26  # micrometers
USER_PROJECT_WIDTH = 3880  # micrometers
USER_PROJECT_HEIGHT = 5070  # micrometers
SAW_STREET_MINIMUM = 60  # micrometers


def read_tilemap(tile_map_file):
    """Read the tile map CSV file."""
    with open(tile_map_file) as csvfile:
        reader = csv.reader(csvfile, delimiter=",", quotechar='"')
        tilemap_data = list(reader)
    return tilemap_data


def create_reticle_pdf(tilemap_data, output_file="reticle.pdf"):
    """
    Create a PDF documentation diagram of the reticle layout.

    Args:
        tilemap_data: 2D list representing the tile map
        output_file: Path to output PDF file
    """

    tile_map_width = len(tilemap_data[0])
    tile_map_height = len(tilemap_data)

    # Get the tile size (with scribe line) in micrometers
    tile_width_um = (
        8
        / tile_map_width
        * (USER_PROJECT_WIDTH + 2 * SEAL_RING_SIZE + SAW_STREET_MINIMUM)
    )
    tile_height_um = (
        5
        / tile_map_height
        * (USER_PROJECT_HEIGHT + 2 * SEAL_RING_SIZE + SAW_STREET_MINIMUM)
    )

    # Calculate saw street width (exact)
    saw_street_exact_um = tile_width_um - USER_PROJECT_WIDTH - 2 * SEAL_RING_SIZE

    print(f"Creating PDF documentation: {output_file}")
    print(f"  Reticle: {RETICLE_WIDTH/1000} mm × {RETICLE_HEIGHT/1000} mm")
    print(f"  Tile map: {tile_map_width} × {tile_map_height}")
    print(f"  Tile size: {tile_width_um:.3f} µm × {tile_height_um:.3f} µm")
    print(f"  Saw street (exact): {saw_street_exact_um:.3f} µm")

    # Create PDF in landscape A4
    c = canvas.Canvas(output_file, pagesize=landscape(A4))
    page_width, page_height = landscape(A4)

    # Drawing parameters (in points, 1 mm = 2.834645669 points)
    # Position the diagram on the left side of the page
    diagram_x_offset = 50  # Left margin in points
    diagram_y_offset = 100  # Bottom margin in points

    # Scale the reticle to fit nicely on the page
    # The reticle is 32mm x 26mm, we'll scale it to about 400 points wide
    scale_factor = 400 / (RETICLE_WIDTH / 1000)  # points per mm

    reticle_width_pts = (RETICLE_WIDTH / 1000) * scale_factor
    reticle_height_pts = (RETICLE_HEIGHT / 1000) * scale_factor

    # Draw overall reticle boundary
    c.setStrokeColor(colors.black)
    c.setLineWidth(1.5)
    c.rect(diagram_x_offset, diagram_y_offset, reticle_width_pts, reticle_height_pts)

    # Draw dimension lines for overall reticle
    # Top dimension (width)
    dim_y_top = diagram_y_offset + reticle_height_pts + 20
    c.setLineWidth(0.5)
    c.line(diagram_x_offset, dim_y_top, diagram_x_offset + reticle_width_pts, dim_y_top)
    c.line(diagram_x_offset, dim_y_top - 5, diagram_x_offset, dim_y_top + 5)
    c.line(diagram_x_offset + reticle_width_pts, dim_y_top - 5, diagram_x_offset + reticle_width_pts, dim_y_top + 5)
    c.setFont("Helvetica", 10)
    c.drawCentredString(diagram_x_offset + reticle_width_pts / 2, dim_y_top + 8, "32 mm")

    # Right dimension (height)
    dim_x_right = diagram_x_offset + reticle_width_pts + 20
    c.line(dim_x_right, diagram_y_offset, dim_x_right, diagram_y_offset + reticle_height_pts)
    c.line(dim_x_right - 5, diagram_y_offset, dim_x_right + 5, diagram_y_offset)
    c.line(dim_x_right - 5, diagram_y_offset + reticle_height_pts, dim_x_right + 5, diagram_y_offset + reticle_height_pts)
    c.saveState()
    c.translate(dim_x_right + 8, diagram_y_offset + reticle_height_pts / 2)
    c.rotate(90)
    c.drawCentredString(0, 0, "26 mm")
    c.restoreState()

    # Calculate tile dimensions in points
    tile_width_pts = (tile_width_um / 1000) * scale_factor
    tile_height_pts = (tile_height_um / 1000) * scale_factor

    # Draw grid of tiles
    for row_idx, row in enumerate(reversed(tilemap_data)):
        for col_idx, slot in enumerate(row):
            x = diagram_x_offset + col_idx * tile_width_pts
            y = diagram_y_offset + row_idx * tile_height_pts

            # Draw tile boundary
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.3)
            c.rect(x, y, tile_width_pts, tile_height_pts)

            # Draw seal ring (red outline inside the tile)
            seal_ring_pts = (SEAL_RING_SIZE / 1000) * scale_factor
            c.setStrokeColor(colors.red)
            c.setLineWidth(0.8)
            c.rect(x + seal_ring_pts, y + seal_ring_pts,
                   tile_width_pts - 2 * seal_ring_pts,
                   tile_height_pts - 2 * seal_ring_pts)

    # Add specifications text box on the right side
    spec_x = diagram_x_offset + reticle_width_pts + 60
    spec_y = diagram_y_offset + reticle_height_pts - 20

    c.setFont("Helvetica-Bold", 11)
    c.drawString(spec_x, spec_y, "GF180MCU specs:")

    c.setFont("Helvetica", 9)
    line_height = 12
    spec_y -= line_height * 1.5

    specs = [
        f"Street size = {SAW_STREET_MINIMUM} µm (minimum)",
        f"Seal ring size = {SEAL_RING_SIZE} µm (exact)",
        "",
        f"Seal × 2 = {SEAL_RING_SIZE * 2} µm (exact)",
        f"Street + 2 × seal = {SAW_STREET_MINIMUM + 2 * SEAL_RING_SIZE} µm (min)",
        f"Street + 1 × seal = {SAW_STREET_MINIMUM + SEAL_RING_SIZE} µm (min)",
        "",
        f"(26 - {tile_map_height} × 0.110 - 2 × 0.085) / 5 = {tile_height_um/1000:.4f} mm",
        f"(32 - {tile_map_width} × 0.110 - 2 × 0.085) / 8 = {tile_width_um/1000:.4f} mm",
        "",
        f"Saw street (exact) = {saw_street_exact_um:.1f} µm",
    ]

    for spec in specs:
        c.drawString(spec_x, spec_y, spec)
        spec_y -= line_height

    # Add detail callout showing seal ring structure
    callout_y = spec_y - 30
    detail_height = 80

    c.setFont("Helvetica", 8)
    c.drawString(spec_x + 60, callout_y + detail_height - 10, "seal ring")
    c.drawString(spec_x + 60, callout_y + detail_height - 30, "saw street")
    c.drawString(spec_x + 60, callout_y + detail_height - 50, "seal ring")

    c.drawString(spec_x + 120, callout_y + detail_height - 10, f"{SEAL_RING_SIZE} µm")
    c.drawString(spec_x + 120, callout_y + detail_height - 30, f"~{SAW_STREET_MINIMUM} µm")
    c.drawString(spec_x + 120, callout_y + detail_height - 50, f"{SEAL_RING_SIZE} µm")

    # Draw lines for the detail
    c.setLineWidth(0.5)
    for i, offset in enumerate([10, 30, 50]):
        y_pos = callout_y + detail_height - offset
        c.line(spec_x, y_pos - 2, spec_x + 50, y_pos - 2)
        c.line(spec_x, y_pos + 2, spec_x + 50, y_pos + 2)

    # Add project die dimensions
    callout_y -= 20
    c.setFont("Helvetica", 8)
    c.drawString(spec_x, callout_y, "Project die dimensions")
    c.drawString(spec_x, callout_y - 10, "(rounded to nearest 10 µm) =")
    c.drawString(spec_x, callout_y - 20, f"{USER_PROJECT_WIDTH/1000:.2f} mm × {USER_PROJECT_HEIGHT/1000:.2f} mm")

    # Add dimension annotation at bottom showing one tile width
    bottom_dim_y = diagram_y_offset - 15
    c.setFont("Helvetica", 8)
    c.setLineWidth(0.5)
    tile_x = diagram_x_offset
    c.line(tile_x, bottom_dim_y, tile_x + tile_width_pts, bottom_dim_y)
    c.line(tile_x, bottom_dim_y - 3, tile_x, bottom_dim_y + 3)
    c.line(tile_x + tile_width_pts, bottom_dim_y - 3, tile_x + tile_width_pts, bottom_dim_y + 3)
    c.drawCentredString(tile_x + tile_width_pts / 2, bottom_dim_y - 12,
                        f"Saw street (exact) = {saw_street_exact_um:.1f} µm")

    # Add tile dimension on right side
    right_dim_x = diagram_x_offset + reticle_width_pts - tile_width_pts
    c.line(right_dim_x, bottom_dim_y - 25, right_dim_x + tile_width_pts, bottom_dim_y - 25)
    c.line(right_dim_x, bottom_dim_y - 28, right_dim_x, bottom_dim_y - 22)
    c.line(right_dim_x + tile_width_pts, bottom_dim_y - 28, right_dim_x + tile_width_pts, bottom_dim_y - 22)
    c.drawCentredString(right_dim_x + tile_width_pts / 2, bottom_dim_y - 37,
                        f"{USER_PROJECT_WIDTH/1000:.2f} mm")

    # Add vertical dimension showing tile height
    left_dim_x = diagram_x_offset - 15
    tile_y = diagram_y_offset
    c.line(left_dim_x, tile_y, left_dim_x, tile_y + tile_height_pts)
    c.line(left_dim_x - 3, tile_y, left_dim_x + 3, tile_y)
    c.line(left_dim_x - 3, tile_y + tile_height_pts, left_dim_x + 3, tile_y + tile_height_pts)
    c.saveState()
    c.translate(left_dim_x - 8, tile_y + tile_height_pts / 2)
    c.rotate(90)
    c.setFont("Helvetica", 8)
    c.drawCentredString(0, 0, f"{USER_PROJECT_HEIGHT/1000:.2f} mm")
    c.restoreState()

    # Save the PDF
    c.showPage()
    c.save()

    print(f"✓ PDF documentation created: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate PDF documentation diagram of a reticle layout."
    )
    parser.add_argument(
        "tilemap",
        help="The CSV tile map for the reticle.",
        metavar="TILEMAP_CSV",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output PDF file (default: reticle.pdf).",
        metavar="OUTPUT_PDF",
        type=str,
        default="reticle.pdf",
    )

    args = parser.parse_args()

    # Validate input file exists
    if not os.path.exists(args.tilemap):
        print(f"Error: Tile map file '{args.tilemap}' does not exist!")
        return 1

    # Read the tile map
    tilemap_data = read_tilemap(args.tilemap)

    # Generate the PDF
    create_reticle_pdf(tilemap_data, output_file=args.output)

    return 0


if __name__ == "__main__":
    exit(main())

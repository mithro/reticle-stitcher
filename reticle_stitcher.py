# SPDX-FileCopyrightText: 2025 Wafer Space PTE. LTD. <info@wafer.space>
# SPDX-License-Identifier: Apache-2.0

import os
import csv
import sys
import hashlib
import argparse

import pya
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# Constants
RETICLE_WIDTH = 32000
RETICLE_HEIGHT = 26000

SEAL_RING_SIZE = 26

USER_PROJECT_WIDTH = 3880
USER_PROJECT_HEIGHT = 5070

SAW_STREET_MINIMUM = 60

RETICLE_X_OFFSET = 124 / 2
RETICLE_Y_OFFSET = 150 / 2

BUF_SIZE = 65536


def read_data(manifest, tile_map):

    with open(manifest) as csvfile:
        dict_reader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
        headers = dict_reader.fieldnames

        data = list(dict_reader)

        manifest_data = {}

        # Set slot as key
        for entry in data:
            manifest_data[entry["SLOT"]] = entry

            # Check the hash
            md5 = hashlib.md5()

            with open(entry["SOURCE"], "rb") as f:
                while True:
                    data = f.read(BUF_SIZE)
                    if not data:
                        break
                    md5.update(data)

            print("MD5: {0}".format(md5.hexdigest()))
            assert entry["HASH"] == md5.hexdigest()

    with open(tile_map) as csvfile:
        reader = csv.reader(csvfile, delimiter=",", quotechar='"')
        tilemap_data = list(reader)

    print(manifest_data)
    print(tilemap_data)

    return manifest_data, tilemap_data

    def get_bounding_box(project_slot, tilemap_data):
        bb0 = None
        bb1 = None

        for y, row in enumerate(reversed(tilemap_data)):
            for x, slot in enumerate(row):
                if slot == project_slot:
                    if bb0 == None:
                        bb0 = [x, y]

                    if bb1 == None:
                        bb1 = [x, y]

                    if x < bb0[0]:
                        bb0[0] = x

                    if y < bb0[1]:
                        bb0[1] = y

                    if x > bb1[0]:
                        bb1[0] = x

                    if y > bb1[1]:
                        bb1[1] = y

        # make sure the project was found
        assert bb0
        assert bb1

        return bb0, bb1

    def get_num_tiles(project_slot, tilemap_data):
        num_tiles = 0

        for y, row in enumerate(reversed(tilemap_data)):
            for x, slot in enumerate(row):
                if slot == project_slot:
                    num_tiles += 1

        return num_tiles


def extract_size_position(manifest_data, tilemap_data):

    tile_map_width = len(tilemap_data[0])
    tile_map_height = len(tilemap_data)

    print(f"tile_map_width: {tile_map_width}")
    print(f"tile_map_height: {tile_map_height}")

    # Make sure all rows have the same size
    for row in tilemap_data:
        assert len(row) == tile_map_width

    # Get the tile size (with scribe line)
    tile_width = (
        8
        / tile_map_width
        * (USER_PROJECT_WIDTH + 2 * SEAL_RING_SIZE + SAW_STREET_MINIMUM)
    )
    tile_height = (
        5
        / tile_map_height
        * (USER_PROJECT_HEIGHT + 2 * SEAL_RING_SIZE + SAW_STREET_MINIMUM)
    )

    print(f"tile_width: {tile_width}")
    print(f"tile_height: {tile_height}")

    # For each slot in manifest, find the slot in the tile map and get the dimensions
    for slot in manifest_data:
        print(f"slot: {slot}")

        # Get the tile map
        bb0, bb1 = get_bounding_box(slot, tilemap_data)

        print(f"bb0: {bb0}, bb1: {bb1}")

        # Get the number of tiles
        num_tiles = get_num_tiles(slot, tilemap_data)

        # Calculate number of tiles in bounding box
        num_tiles_bb = (bb1[0] - bb0[0] + 1) * (bb1[1] - bb0[1] + 1)

        # Make sure projects are quare
        assert num_tiles == num_tiles_bb

        manifest_data[slot]["POSITION_TILES"] = bb0
        manifest_data[slot]["WIDTH_TILES"] = bb1[0] - bb0[0] + 1
        manifest_data[slot]["HEIGHT_TILES"] = bb1[1] - bb0[1] + 1

    return manifest_data


def create_reticle(manifest_data, tilemap_data, output_file="reticle.oas"):

    tile_map_width = len(tilemap_data[0])
    tile_map_height = len(tilemap_data)

    print(f"tile_map_width: {tile_map_width}")
    print(f"tile_map_height: {tile_map_height}")

    # Make sure all rows have the same size
    for row in tilemap_data:
        assert len(row) == tile_map_width

    # Get the tile size (with scribe line)
    tile_width = (
        8
        / tile_map_width
        * (USER_PROJECT_WIDTH + 2 * SEAL_RING_SIZE + SAW_STREET_MINIMUM)
    )
    tile_height = (
        5
        / tile_map_height
        * (USER_PROJECT_HEIGHT + 2 * SEAL_RING_SIZE + SAW_STREET_MINIMUM)
    )

    print(f"tile_width: {tile_width}")
    print(f"tile_height: {tile_height}")

    layout = pya.Layout()
    top_cell = layout.create_cell("reticle")

    # Create boundary (for debugging)
    PR_bndry = pya.LayerInfo(0, 0)
    top_cell.shapes(PR_bndry).insert(pya.DBox.new(0, 0, RETICLE_WIDTH, RETICLE_HEIGHT))

    for slot in manifest_data:

        project = manifest_data[slot]["PROJECT"]
        project_id = manifest_data[slot]["ID"]
        project_id_hash = manifest_data[slot]["HASH"]
        project_source = manifest_data[slot]["SOURCE"]

        x, y = manifest_data[slot]["POSITION_TILES"]

        print(
            f"Placing project {project} in {x}/{y}: {project_id} {project_id_hash} {project_source}"
        )

        # Create a separate layout to prevent cell conflicts
        user_layout = pya.Layout()

        # Read the user project
        user_layout.read(manifest_data[slot]["SOURCE"])
        user_layout_topcell = user_layout.top_cell()

        print(user_layout.top_cell().dbbox())

        x0 = user_layout.top_cell().dbbox().left
        y0 = user_layout.top_cell().dbbox().bottom
        x1 = user_layout.top_cell().dbbox().right
        y1 = user_layout.top_cell().dbbox().top

        # Check origin equals (0, 0)
        assert x0 == 0 and y0 == 0

        print(manifest_data[slot]["WIDTH_TILES"] * tile_width - SAW_STREET_MINIMUM)

        # Check dimensions of the project
        assert (
            manifest_data[slot]["WIDTH_TILES"] * tile_width - SAW_STREET_MINIMUM == x1
        )
        assert (
            manifest_data[slot]["HEIGHT_TILES"] * tile_height - SAW_STREET_MINIMUM == y1
        )

        # Create new cell in reticle layout
        user_cell = layout.create_cell(
            f"{user_layout_topcell.name}_{manifest_data[slot]['ID']}_{x}_{y}"
        )

        # Copy the contents into the cell
        user_cell.copy_tree(user_layout_topcell)

        # Insert the user cell
        top_cell.insert(
            pya.DCellInstArray(
                user_cell,
                pya.DPoint(
                    x * tile_width + RETICLE_X_OFFSET,
                    y * tile_height + RETICLE_Y_OFFSET,
                ),
            )
        )

    print(f"Writing reticle: {output_file}")

    # Write the final oasis
    layout.write(output_file)


def create_reticle_pdf(manifest_data, tilemap_data, output_file="reticle.pdf"):
    """
    Create a PDF documentation diagram of the reticle layout, similar to the
    example at https://github.com/efabless/caravel-gf180mcu/blob/main/docs/reticle.pdf

    This generates a technical drawing showing:
    - The overall reticle boundary with dimensions
    - Grid of tiles with seal rings
    - Dimension annotations
    - Specifications and calculations
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

    print(f"PDF documentation created: {output_file}")


def main():

    def is_valid_file(parser, arg):
        if not os.path.exists(arg):
            parser.error("The file %s does not exist!" % arg)
        else:
            return arg

    parser = argparse.ArgumentParser(
        description="Tool for stitching a full MPW reticle using gf180mcu for delivery to a foundry."
    )
    parser.add_argument(
        "manifest",
        help="The manifest CSV file.",
        metavar="FILE",
        type=lambda x: is_valid_file(parser, x),
    )
    parser.add_argument(
        "tile-map",
        help="The CSV tile map for the reticle.",
        metavar="FILE",
        type=lambda x: is_valid_file(parser, x),
    )
    parser.add_argument(
        "--pdf",
        help="Generate a PDF documentation diagram of the reticle layout.",
        metavar="OUTPUT_PDF",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--output",
        help="Output file for the reticle OASIS file (default: reticle.oas).",
        metavar="OUTPUT_FILE",
        type=str,
        default="reticle.oas",
    )

    args = vars(parser.parse_args())

    # Read the manifest
    manifest_data, tilemap_data = read_data(args["manifest"], args["tile-map"])

    # For each project get the tile position and size
    manifest_data = extract_size_position(manifest_data, tilemap_data)

    # Create the layout
    create_reticle(manifest_data, tilemap_data, output_file=args["output"])

    # Generate PDF documentation if requested
    if args["pdf"]:
        create_reticle_pdf(manifest_data, tilemap_data, output_file=args["pdf"])


if __name__ == "__main__":
    main()

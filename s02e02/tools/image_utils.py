import io
import os

from PIL import Image


def prepare_image(raw: bytes) -> Image.Image:
    """Auto-detect and crop the circuit grid by finding grid lines."""
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    gray = img.convert("L")
    w, h = gray.size
    px = gray.load()
    dark = 128

    row_counts = [sum(1 for x in range(w) if px[x, y] < dark) for y in range(h)]
    col_counts = [sum(1 for y in range(h) if px[x, y] < dark) for x in range(w)]

    row_thresh = max(row_counts) * 0.83
    col_thresh = max(col_counts) * 0.83

    dense_rows = [y for y, c in enumerate(row_counts) if c > row_thresh]
    dense_cols = [x for x, c in enumerate(col_counts) if c > col_thresh]

    return img.crop((dense_cols[0], dense_rows[0], dense_cols[-1], dense_rows[-1]))


def split_cells(img: Image.Image) -> list:
    """Split a cropped grid image into a 3x3 list of cell images."""
    w, h = img.size
    cw, ch = w // 3, h // 3
    cells = []
    for row in range(3):
        row_cells = []
        for col in range(3):
            cell = img.crop((col * cw, row * ch, (col + 1) * cw, (row + 1) * ch))
            row_cells.append(cell)
        cells.append(row_cells)
    return cells


_CELLS_DIR = os.path.join(os.path.dirname(__file__), "..", "cells")

# (top, bottom, left, right) -> circuit character
_BORDER_MAP = {
    (False, False, True,  True ): "─",
    (True,  True,  False, False): "│",
    (False, True,  False, True ): "┌",
    (False, True,  True,  False): "┐",
    (True,  False, False, True ): "└",
    (True,  False, True,  False): "┘",
    (True,  True,  False, True ): "├",
    (True,  True,  True,  False): "┤",
    (False, True,  True,  True ): "┬",
    (True,  False, True,  True ): "┴",
    (True,  True,  True,  True ): "┼",
}


def encode_cell(cell: Image.Image, label: str = "") -> Image.Image:
    """Trim margin, threshold to B&W, optionally save, return processed image."""
    margin = 12
    w, h = cell.size
    cell = cell.crop((margin, margin, w - margin, h - margin))
    cell = cell.convert("L").point(lambda p: 255 if p > 128 else 0, "1")
    return cell


def classify_cell(cell: Image.Image) -> str:
    """Detect black pixels on each border and return the matching circuit character."""
    gray = cell.convert("L")
    w, h = gray.size
    px = gray.load()
    strip = 4

    def has_black(coords):
        return any(px[x, y] < 128 for x, y in coords)

    top    = has_black([(x, y) for y in range(strip)       for x in range(w)])
    bottom = has_black([(x, y) for y in range(h - strip, h) for x in range(w)])
    left   = has_black([(x, y) for x in range(strip)       for y in range(h)])
    right  = has_black([(x, y) for x in range(w - strip, w) for y in range(h)])

    return _BORDER_MAP.get((top, bottom, left, right), "?")


def interpret_circuit_image(img: Image.Image) -> dict:
    """Classify each of the 9 cells individually and return the full matrix."""
    cells = split_cells(img)
    keys = [
        "1x1", "1x2", "1x3",
        "2x1", "2x2", "2x3",
        "3x1", "3x2", "3x3",
    ]
    values = []
    for row in range(3):
        for col in range(3):
            label = f"{row + 1}x{col + 1}"
            processed = encode_cell(cells[row][col], label=label)
            char = classify_cell(processed)
            values.append(char)

    result = {k: v for k, v in zip(keys, values)}
    result["full_grid"] = (
        f"{values[0]} {values[1]} {values[2]}\n"
        f"{values[3]} {values[4]} {values[5]}\n"
        f"{values[6]} {values[7]} {values[8]}"
    )
    return result

#!/usr/bin/env python3
"""randomize_macro_colors.py

Generate a non-adjacent color list for macro buttons and insert it into config.py.
Usage: python randomize_macro_colors.py [path/to/config.py]
"""

from pathlib import Path
import re
import sys
import random
import ast
import shutil
from typing import List, Tuple
import difflib

# Simple pastel palette
PALETTE = [
    "#f5e0dc", "#f2cdcd", "#f5c2e7", "#cba6f7",
    "#f38ba8", "#eba0ac", "#fab387", "#f9e2af",
    "#a6e3a1", "#94e2d5", "#89b4fa", "#b4befe",
    # additional pastel tones
    "#ffd6a5", "#ffe8d6", "#cdeac0", "#bfefff",
    "#e0c8ff", "#ffd1dc", "#d9e2f3", "#fffbdb",
    "#d0f4de", "#e6e6ff", "#f0d9ff", "#cdd6f4",
]

SIMILARITY_THRESHOLD = 70.0

ROWS_RE = re.compile(r'^\s*rows\s*=\s*(\d+)\s*$', re.MULTILINE)
COLS_RE = re.compile(r'^\s*cols\s*=\s*(\d+)\s*$', re.MULTILINE)
MACRO_LIST_RE = re.compile(r"(?P<name>\b[A-Za-z_][A-Za-z0-9_]*macro[_A-Za-z0-9]*colors\b)\s*=\s*(?P<list>\[.*?\])", re.IGNORECASE | re.DOTALL)


def hex_to_rgb(h: str) -> Tuple[int, int, int]:
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


PALETTE_RGB = [hex_to_rgb(x) for x in PALETTE]


def dist_rgb(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def build_neighbors(rows: int, cols: int):
    def neighbors(idx: int):
        r, c = divmod(idx, cols)
        neigh = []
        # Cardinal directions
        if c - 1 >= 0:
            neigh.append(idx - 1)
        if c + 1 < cols:
            neigh.append(idx + 1)
        if r - 1 >= 0:
            neigh.append(idx - cols)
        if r + 1 < rows:
            neigh.append(idx + cols)
        # Diagonal directions
        if r - 1 >= 0 and c - 1 >= 0:
            neigh.append(idx - cols - 1)  # top-left
        if r - 1 >= 0 and c + 1 < cols:
            neigh.append(idx - cols + 1)  # top-right
        if r + 1 < rows and c - 1 >= 0:
            neigh.append(idx + cols - 1)  # bottom-left
        if r + 1 < rows and c + 1 < cols:
            neigh.append(idx + cols + 1)  # bottom-right
        return neigh

    return neighbors


def find_rows_cols(text: str) -> Tuple[int, int]:
    r_m = ROWS_RE.search(text)
    c_m = COLS_RE.search(text)
    if not r_m or not c_m:
        raise SystemExit("Could not find 'rows = N' and 'cols = M' assignments in config.py")
    return int(r_m.group(1)), int(c_m.group(1))


def generate_assignment(rows: int, cols: int, palette: List[str], palette_rgb: List[Tuple[int, int, int]], threshold: float, max_tries: int = 2000) -> List[str]:
    n = rows * cols
    neigh_fn = build_neighbors(rows, cols)

    incompatible = {
        i: set(j for j in range(len(palette)) if dist_rgb(palette_rgb[i], palette_rgb[j]) < threshold)
        for i in range(len(palette))
    }

    solution = [None] * n
    domains = [list(range(len(palette))) for _ in range(n)]
    order = list(range(n))
    attempts = 0

    def backtrack(pos_index: int) -> bool:
        nonlocal attempts
        attempts += 1
        if attempts > max_tries:
            return False
        if pos_index >= n:
            return True
        idx = order[pos_index]
        assigned_neighbors = [solution[nb] for nb in neigh_fn(idx) if solution[nb] is not None]

        choices = domains[idx].copy()
        random.shuffle(choices)
        for color_i in choices:
            ok = True
            for nb_color in assigned_neighbors:
                if nb_color in incompatible[color_i]:
                    ok = False
                    break
            if not ok:
                continue
            solution[idx] = color_i
            saved_domains = []
            fail_forward = False
            for nb in neigh_fn(idx):
                if solution[nb] is None:
                    saved_domains.append((nb, domains[nb].copy()))
                    domains[nb] = [d for d in domains[nb] if d not in incompatible[color_i]]
                    if not domains[nb]:
                        fail_forward = True
                        break
            if not fail_forward and backtrack(pos_index + 1):
                return True
            for nb, dom in saved_domains:
                domains[nb] = dom
            solution[idx] = None
        return False

    success = backtrack(0)
    if not success:
        raise RuntimeError("Failed to find a non-adjacent-color assignment; try relaxing threshold.")
    return [palette[i] for i in solution]


def replace_or_append_list_file(path: Path, var_name_suggestion: str, color_list: List[str]):
    # keep compatibility but prefer inline PAGE#_MACROS replacement in main()
    text = path.read_text(encoding='utf-8')
    m = MACRO_LIST_RE.search(text)
    list_repr = "[" + ", ".join(f"'{c}'" for c in color_list) + "]"
    if m:
        var_name = m.group('name')
        new_text = text[:m.start()] + f"{var_name} = {list_repr}" + text[m.end():]
        path.write_text(new_text, encoding='utf-8')
        print(f"Replaced list variable '{var_name}' in {path}")
    else:
        append_text = f"\n\n# Generated macro colors (randomized)\n{var_name_suggestion} = {list_repr}\n"
        path.write_text(text + append_text, encoding='utf-8')
        print(f"Appended '{var_name_suggestion}' to {path}")


def _find_page_macros(text: str):
    """Find PAGE#_MACROS assignments and return (name, list_text, start, end) tuples.

    This locates the '=' after the PAGE<N>_MACROS name, finds the first '[' and
    then scans forward to the matching ']' while respecting quoted strings and
    escaped characters. This is robust against inner lists and bracket-like
    characters inside strings.
    """
    matches = []
    name_re = re.compile(r"^(?P<name>PAGE\d+_MACROS)\s*=", re.MULTILINE)
    for m in name_re.finditer(text):
        name = m.group('name')
        # find first '[' after the match
        start_search = m.end()
        open_pos = text.find('[', start_search)
        if open_pos == -1:
            continue

        # scan forward for matching closing bracket
        depth = 0
        i = open_pos
        in_string = None
        escaped = False
        while i < len(text):
            ch = text[i]
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif in_string:
                if ch == in_string:
                    in_string = None
            elif ch == '"' or ch == "'":
                in_string = ch
            elif ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    end_pos = i + 1
                    list_text = text[open_pos:end_pos]
                    matches.append((name, list_text, open_pos, end_pos))
                    break
            i += 1
    return matches


def _find_page_rows_cols(text: str, page_num: int):
    rows_re = re.compile(rf'PAGE{page_num}_MACRO_ROWS\s*=\s*(\d+)')
    cols_re = re.compile(rf'PAGE{page_num}_MACRO_COLS\s*=\s*(\d+)')
    r_m = rows_re.search(text)
    c_m = cols_re.search(text)
    return (int(r_m.group(1)), int(c_m.group(1))) if r_m and c_m else (None, None)


def main():
    # Simple CLI: optional path and optional --dry-run flag
    args = sys.argv[1:]
    dry_run = False
    if '--dry-run' in args:
        dry_run = True
        args.remove('--dry-run')

    if len(args) > 1:
        print("Usage: python randomize_macro_colors.py [path/to/config.py] [--dry-run")
        sys.exit(1)
    cfg = Path(args[0]) if len(args) == 1 else Path("config.py")
    if not cfg.exists():
        print(f"Config file not found: {cfg}")
        sys.exit(1)

    # Read original
    text = cfg.read_text(encoding='utf-8')

    # Backup original unless we're doing a dry-run
    if not dry_run:
        backup = cfg.with_name(cfg.name + '.old')
        shutil.copy2(cfg, backup)
        print(f"Backed up {cfg} -> {backup}")

    pages = _find_page_macros(text)
    if not pages:
        print("Error: No PAGE#_MACROS blocks found in config.py; aborting.")
        sys.exit(1)

    # Prepare replacements first (avoid modifying text while iterating positions)
    replacements = []  # list of (start, end, replacement_text, name, replaced_count)
    for name, list_text, start, end in pages:
        try:
            parsed = ast.literal_eval(list_text)
        except Exception as e:
            print(f"Failed to parse {name}: {e}")
            continue
        page_num = int(name.replace('PAGE', '').split('_')[0])
        rows, cols = _find_page_rows_cols(text, page_num)
        if not rows or not cols:
            print(f"Skipping {name}: missing PAGE{page_num}_MACRO_ROWS/COLS")
            continue
        total = rows * cols
        print(f"Processing {name}: rows={rows}, cols={cols}, total={total}")

        random.seed()
        colors = generate_assignment(rows, cols, PALETTE, PALETTE_RGB, SIMILARITY_THRESHOLD)

        replaced = 0
        for i in range(min(total, len(parsed))):
            if isinstance(parsed[i], list) and len(parsed[i]) >= 1:
                parsed[i][0] = colors[i]
                replaced += 1

        # Re-serialize with simple formatting
        new_list_text = '[\n'
        for item in parsed:
            new_list_text += '    ' + repr(item) + ',\n'
        new_list_text += ']' 

        replacements.append((start, end, new_list_text, name, replaced))
        print(f"Prepared replacement for {name}: {replaced} entries to update")

    # Rebuild the new text by applying replacements in order
    if replacements:
        replacements.sort(key=lambda x: x[0])
        out_parts = []
        last = 0
        for s, e, rep, name, replaced in replacements:
            out_parts.append(text[last:s])
            out_parts.append(rep)
            last = e
        out_parts.append(text[last:])
        new_text = ''.join(out_parts)
    else:
        new_text = text

    # Write atomically, or show diff on dry-run
    if dry_run:
        diff = difflib.unified_diff(
            text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=str(cfg),
            tofile=str(cfg) + ' (proposed)',
        )
        sys.stdout.writelines(diff)
        print("-- dry-run: no files were modified --")
    else:
        tmp = cfg.with_suffix('.tmp')
        tmp.write_text(new_text, encoding='utf-8')
        tmp.replace(cfg)
        print(f"Updated {cfg} with new colors")


if __name__ == "__main__":
    main()
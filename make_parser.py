#!/usr/bin/env python3
"""Build a local Node.js module from CrochetPARADE's parse64.js."""
import argparse
from pathlib import Path

# Wrap the browser script and declare the implicit globals it needs as a module.
HEADER = """// Generated from CrochetPARADE parse64.js. Copyright (C) Svetlin Tassev.
// SPDX-License-Identifier: GPL-3.0-or-later
export function createParser(console, alert) {
var Nrows, LIST, otherNodes, connections, Stitches, k;
var isp, i0, i1;
"""
EVALUATOR = "return Function(`'use strict'; return ${expression}`)();"
# Restrict the evaluator to arithmetic, including exponents in numeric literals.
ARITHMETIC_EVALUATOR = r"""const text = String(expression).trim();
    if (!/^[0-9+\-*\/%().\seE]+$/.test(text)) throw new Error('Expected an arithmetic expression.');
    return Function(`'use strict'; return ${text}`)();"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='downloaded parse64.js')
    parser.add_argument('output', type=Path, help='local module, typically parser.mjs')
    args = parser.parse_args()
    try:
        source = args.source.read_text(encoding='utf-8')
        if source.count(EVALUATOR) != 1:
            parser.error('Unexpected parser source. Use the pinned file linked in README.md.')
        source = source.replace(EVALUATOR, ARITHMETIC_EVALUATOR)
        args.output.write_text(HEADER + source + '\nreturn {final, export_to_dot};\n}\n', encoding='utf-8')
    except (OSError, UnicodeError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()

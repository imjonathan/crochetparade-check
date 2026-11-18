#!/usr/bin/env python3
"""Check one CrochetPARADE pattern file."""
import argparse
from pathlib import Path
import subprocess
import sys

from cplib import analyze_one, parse_all
from engalign import coverage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pattern', type=Path, help='CrochetPARADE pattern file')
    parser.add_argument('english', type=Path, nargs='?', help='plain-English pattern file')
    args = parser.parse_args()

    if not Path(__file__).with_name('parser.mjs').is_file():
        parser.error('Build parser.mjs first using the setup steps in README.md.')

    try:
        text = args.pattern.read_text(encoding='utf-8')
        english = args.english.read_text(encoding='utf-8') if args.english else None
        parsed = parse_all({'pattern': {'dsl': text}})['pattern']
    except (OSError, UnicodeError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))

    if 'error' in parsed:
        print(f"Does not compile. {parsed['error']}")
        return 1

    print('Compiles.')
    result = analyze_one(parsed, text)
    for message in parsed['msgs']:
        print(f'Parser note. {message}')
    if not result['mapped']:
        print('Some compiled rows could not be matched to file lines. Comment counts were skipped.')

    issues = 0
    for row in result['rows']:
        location = f"Compiled row {row['number']}"
        if row['line'] is not None:
            location = f"Line {row['line']} (compiled row {row['number']})"
        if row['left'] or row['outside']:
            details = []
            if row['left']:
                details.append(f"Leaves {row['left']} of {row['previous']} previous-round stitches unworked.")
            if row['outside']:
                details.append(f"Works {row['outside']} times into stitches outside the previous round.")
            if row['note']:
                print(f"Note on {location.lower()} ({row['note']}). {' '.join(details)}")
            else:
                print(f"{location}. {' '.join(details)}")
                issues += 1
        if row['stated'] is not None and row['stated'] not in (row['made'], row['made'] - row['chains']):
            print(f"{location}. Makes {row['made']} stitches, but the comment states {row['stated']}.")
            issues += 1

    if issues == 0:
        print('No round-closure or comment-count errors found.')
    if english is not None:
        counts = coverage(english, [row['made'] for row in result['rows']])
        if counts:
            print(f"English comparison. {counts['matched_in_order']} of {counts['english_counts']} "
                  'stated counts appear in order in the compiled rounds.')
        else:
            print('English comparison. No round counts found in the English file.')
    return int(issues > 0)


if __name__ == '__main__':
    sys.exit(main())

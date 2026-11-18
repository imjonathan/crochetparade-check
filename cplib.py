"""Run the parser and check stitch attachments and stated counts."""
import json
import os
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory

from engalign import stated_count

NONSTITCHES = {'tie up stitches', 'ring', 'sk', 'start a new chain'}
STANDARD_JOIN = re.compile(r'\bss\s*@\s*\[\s*%\s*,\s*0\s*\]\s*$')


def parse_all(patterns):
    with TemporaryDirectory(prefix='crochetparade-check-') as directory:
        input_path = Path(directory, 'input.json')
        output_path = Path(directory, 'output.json')
        input_path.write_text(json.dumps(patterns), encoding='utf-8')
        rows_script = Path(__file__).with_name('rows.mjs')
        subprocess.run([os.environ.get('NODE', 'node'), rows_script, input_path, output_path],
                       check=True, stdout=subprocess.DEVNULL)
        return json.loads(output_path.read_text(encoding='utf-8'))


def codelines(lines):
    """Map logical CrochetPARADE rows to the file lines where they start."""
    result = []
    continued = False
    for index, line in enumerate(lines):
        code = line.split('#', 1)[0].strip()
        if not code or code.startswith('DEF') or re.fullmatch(r'\$.*\$', code):
            continue
        if continued:
            start, _, previous = result[-1]
            result[-1] = (start, index, previous + ' ' + code)
        else:
            result.append((index, index, code))
        continued = code.endswith('...')
    return result


def comment_count(lines, start, end):
    candidates = [line.partition('#')[2] for line in reversed(lines[start:end + 1])]
    if start > 0 and lines[start - 1].lstrip().startswith('#'):
        candidates.append(lines[start - 1].lstrip()[1:])
    for comment in candidates:
        count = stated_count(comment)
        if count is not None:
            return count
    return None


def attachment_note(code, previous_code, stitches, mapped):
    if re.search(r'\bturn\s*$', code) or re.search(r'\bturn\s*$', previous_code):
        return 'turned row'
    if re.fullmatch(r'[A-Za-z_]+\d+tog(?:\.\w+)?', code):
        return 'closing gather'
    # A conventional slip-stitch join may accompany an otherwise ordinary round.
    without_join = STANDARD_JOIN.sub('', code)
    if '@' in without_join or (not mapped and any(stitch[3] for stitch in stitches)):
        return 'explicit attachments'
    return None


def analyze_one(parsed, text):
    compiled_rows = parsed['rows']
    lines = text.splitlines()
    code_lines = codelines(lines)
    mapped = all(row['n'] == index for index, row in enumerate(compiled_rows))
    mapped = mapped and len(compiled_rows) == len(code_lines)

    stitch_rows = {}
    made_by_row = {}
    stitches_by_row = {}
    for row in compiled_rows:
        number = row['n']
        made = set()
        stitches = row['st']
        if mapped and STANDARD_JOIN.search(code_lines[number][2]) and stitches[-1][0] == 'ss':
            stitches = stitches[:-1]
        stitches_by_row[number] = stitches
        for kind, ids, _, _ in stitches:
            for stitch_id in ids:
                stitch_rows.setdefault(stitch_id, number)
            if kind not in NONSTITCHES:
                made.update(ids)
        made_by_row[number] = made

    result = []
    for row in compiled_rows:
        number = row['n']
        types = row['types']
        made = made_by_row[number]
        if not made and set(types) <= {'ring', 'start a new chain', 'tie up stitches'}:
            continue
        start, end, code = code_lines[number] if mapped else (None, None, '')
        previous_code = code_lines[number - 1][2] if mapped and number > 0 else ''
        previous = made_by_row.get(number - 1, set())
        new_piece = 'start a new chain' in types or 'ring' in types or not previous
        used = set()
        outside = 0
        if not new_piece:
            stitches = stitches_by_row[number]
            for _, _, attachments, _ in stitches:
                used.update(attachments)
            outside = sum(stitch_rows.get(target) != number - 1
                          for kind, _, attachments, _ in stitches if kind != 'sk'
                          for target in attachments)
        result.append({
            'number': number + 1,
            'line': start + 1 if start is not None else None,
            'made': len(made),
            'chains': types.get('ch', 0),
            'previous': len(previous),
            'left': len(previous - used) if not new_piece else 0,
            'outside': outside,
            'note': attachment_note(code, previous_code, row['st'], mapped),
            'stated': comment_count(lines, start, end) if mapped and made else None,
        })
    return {'mapped': mapped, 'rows': result}

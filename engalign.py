"""Compare stitch-count sequences from plain English and compiled rounds."""
import re

COUNT = re.compile(
    r'(?:^|[.:;(\[=\-–—>])\s*[\[(]?\s*(\d+)\s+'
    r'(?:sc|hdc|dc|tr|ss|sl sts?|slip stitches?|sts?|stitches|single crochets?|half double crochets?|'
    r'double crochets?|treble crochets?)\s*[.)\]*]*\s*$', re.IGNORECASE,
)


def stated_count(line):
    match = COUNT.search(line.strip())
    return int(match[1]) if match else None


def lcs(expected, compiled):
    """Return the length of the longest common subsequence."""
    previous = [0] * (len(compiled) + 1)
    for expected_count in expected:
        current = [0] * (len(compiled) + 1)
        for index, actual_count in enumerate(compiled, 1):
            if expected_count == actual_count:
                current[index] = 1 + previous[index - 1]
            else:
                current[index] = max(previous[index], current[index - 1])
        previous = current
    return previous[-1]


def coverage(english, compiled):
    counts = [count for line in english.splitlines() if (count := stated_count(line)) is not None]
    if not counts:
        return None
    return {'english_counts': len(counts), 'matched_in_order': lcs(counts, compiled)}

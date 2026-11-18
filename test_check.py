import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parent
EXAMPLES = ROOT / 'examples'
START = 'ring.Center\n5sc@Center # 5 sc\n5sc2inc # 10 sc\n'


class CheckPatternTests(unittest.TestCase):
    def run_check(self, *files, directory=ROOT):
        return subprocess.run([sys.executable, ROOT / 'check.py', *files], cwd=directory,
                              env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
                              text=True, capture_output=True)

    def check_round(self, last_round):
        with TemporaryDirectory() as directory:
            pattern = Path(directory, 'pattern.cp')
            pattern.write_text(START + last_round + '\n', encoding='utf-8')
            return self.run_check(pattern, directory=directory)

    def test_clean_example(self):
        result = self.run_check(EXAMPLES / 'clean.cp', EXAMPLES / 'clean.txt')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Compiles.', result.stdout)
        self.assertIn('No round-closure or comment-count errors found.', result.stdout)
        self.assertIn('3 of 3 stated counts appear in order', result.stdout)

    def test_drift_example(self):
        result = self.run_check(EXAMPLES / 'drift.cp', EXAMPLES / 'clean.txt')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('Leaves 2 of 10 previous-round stitches unworked.', result.stdout)
        self.assertIn('Makes 8 stitches, but the comment states 10.', result.stdout)
        self.assertIn('2 of 3 stated counts appear in order', result.stdout)

    def test_overruns_are_errors(self):
        for final_round, count in [('12sc', 2), ('8sc2tog', 6)]:
            with self.subTest(final_round=final_round):
                result = self.check_round(final_round)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(f'Works {count} times into stitches outside the previous round.', result.stdout)

    def test_conventional_join_is_clean(self):
        result = self.check_round('10sc, ss@[%,0] # 10 sc')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('No round-closure or comment-count errors found.', result.stdout)

    def test_slip_stitches_count_when_worked_as_a_round(self):
        result = self.check_round('10ss # 9 sl sts')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('Makes 10 stitches, but the comment states 9.', result.stdout)

    def test_closure_exceptions_are_notes(self):
        for final_round, kind in [('8sc, turn', 'turned row'),
                                  ('8sc@Center', 'explicit attachments'),
                                  ('sc8tog', 'closing gather')]:
            with self.subTest(final_round=final_round):
                result = self.check_round(final_round)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f'Note on line 4 (compiled row 4) ({kind})', result.stdout)

    def test_comment_count_is_checked_on_a_turned_row(self):
        result = self.check_round('8sc, turn # 10 sc')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('turned row', result.stdout)
        self.assertIn('Makes 8 stitches, but the comment states 10.', result.stdout)

    def test_invalid_pattern(self):
        result = self.check_round('undefined_stitch')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('Does not compile.', result.stdout)

    def test_english_counts_are_matched_in_order(self):
        with TemporaryDirectory() as directory:
            english = Path(directory, 'pattern.txt')
            english.write_text('Round 1. 10 sc.\nRound 2. 5 sc.\n', encoding='utf-8')
            result = self.run_check(EXAMPLES / 'clean.cp', english, directory=directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('1 of 2 stated counts appear in order', result.stdout)


if __name__ == '__main__':
    unittest.main()

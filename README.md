# CrochetPARADE Check

Check one CrochetPARADE pattern at a time. The checker tells you whether the pattern compiles, which rounds leave stitches unworked or work outside the previous round, and where the stitch count differs from the count in a comment. If you supply a plain-English pattern, it also reports how many stated stitch counts appear in order in the compiled rounds.

The scripts were written with Claude (an AI model).

## Set up the parser

You need Python 3.10 or later and Node.js 18 or later.

Download [`parse64.js` from CrochetPARADE on Codeberg](https://codeberg.org/crochetparade/CrochetPARADE/raw/commit/be11c8b0a37f2fdeaca39bd2c1cd2b0cc7fc281d/parse64.js) and save it alongside these scripts. Codeberg serves this file at revision `be11c8b0`. It is byte-for-byte identical to the parser at the original pin, [`06e987b1`](https://raw.githubusercontent.com/stassev/CrochetPARADE/06e987b13ccfc94cfdfcebc1fe4664d37d2c6687/parse64.js).

Build the local module from the downloaded file.

```sh
python3 make_parser.py parse64.js parser.mjs
```

The generated module is derived from CrochetPARADE (© Svetlin Tassev, GPL-3.0-or-later). The [MIT license](LICENSE) covers these scripts only. Keep the downloaded parser and the generated module out of Git.

## Check a pattern

```sh
python3 check.py pattern.cp
python3 check.py pattern.cp pattern.txt
```

The second file is optional. Put each English round on a separate line, with a count at the end such as `Round 2. Increase in every stitch. 10 sc.` Inside a CrochetPARADE pattern, put a count like `# 10 sc` on the round's line or on the comment line immediately above it. Counts in comments may include or omit chains. The checker exits with status 0 when it finds no errors, 1 for a compile or count error, and 2 for a setup or input problem.

## Worked example

In [`examples/clean.cp`](examples/clean.cp), the first round makes five single crochets in a magic ring, the second increases to ten, and the third works all ten.

```text
ring.Center
5sc@Center # 5 sc
5sc2inc # 10 sc
10sc # 10 sc
```

Run it with its [English instructions](examples/clean.txt).

```sh
python3 check.py examples/clean.cp examples/clean.txt
```

```text
Compiles.
No round-closure or comment-count errors found.
English comparison. 3 of 3 stated counts appear in order in the compiled rounds.
```

In [`examples/drift.cp`](examples/drift.cp), the last round makes eight stitches. The checker reports two unworked stitches and a mismatch with the stated count of ten. Compare it with the same English instructions to see two of the three counts match.

Run the example tests after building the parser.

```sh
python3 -m unittest -v
```

## Limits

- The checker is built for pieces worked in rounds. Turned rows, explicit attachments, and closing gathers can depart from ordinary round closure. The checker reports those departures as notes.
- Comment counts are skipped if the checker cannot match compiled rows to file lines. It reports when this happens.
- The checks miss mistakes that keep stitch counts consistent, such as using the wrong stitch type or omitting a piece.
- A clean result means the pattern passed these checks. Whether it matches a source pattern is a separate question.

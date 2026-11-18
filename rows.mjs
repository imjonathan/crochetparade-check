// Run CrochetPARADE and record the stitches and attachments for each row.
import fs from 'node:fs';
import { createParser } from './parser.mjs';

const [, , inputPath, outputPath] = process.argv;
const patterns = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
const results = Object.create(null);

for (const [name, { dsl }] of Object.entries(patterns)) {
  const msgs = [];
  const record = { msgs };
  results[name] = record;
  const note = (...args) => msgs.push(args.join(' ').replace(/\s+/g, ' ').trim());
  const parser = createParser({ log() {}, warn: note, error: note }, note);

  let stitches;
  try {
    stitches = parser.final(dsl);
  } catch (error) {
    record.error = String(error.message || error).split('\n')[0];
    continue;
  }
  if (!stitches?.length) {
    record.error = 'The parser returned no stitches.';
    continue;
  }

  const rows = new Map();
  for (const stitch of stitches) {
    const n = stitch.nrow;
    if (!rows.has(n)) {
      rows.set(n, { n, types: Object.create(null), st: [] });
    }
    const row = rows.get(n);
    row.types[stitch.type] = (row.types[stitch.type] || 0) + 1;
    const explicit = stitch.attach_ref != null || Object.values(stitch.at_expr || {}).some(Boolean);
    row.st.push([stitch.type, stitch.id, stitch.id_attach, explicit]);
  }
  record.rows = [...rows.values()].sort((a, b) => a.n - b.n);
}

fs.writeFileSync(outputPath, JSON.stringify(results));

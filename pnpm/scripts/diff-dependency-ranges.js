#!/usr/bin/env node
'use strict';

/**
 * Compares two dependency range snapshots and prints one tab separated
 * `package<TAB>old<TAB>new` line per changed range.
 *
 * Usage: node diff-dependency-ranges.js <before.json> <after.json>
 *
 * Packages that were added or removed are ignored: only ranges present in
 * both snapshots represent an update.
 */

const fs = require('fs');

function main() {
  const [beforePath, afterPath] = process.argv.slice(2);

  if (!beforePath || !afterPath) {
    process.stderr.write(
      'Usage: diff-dependency-ranges.js <before.json> <after.json>\n',
    );
    process.exit(1);
  }

  const before = JSON.parse(fs.readFileSync(beforePath, 'utf8'));
  const after = JSON.parse(fs.readFileSync(afterPath, 'utf8'));

  const lines = Object.keys(before)
    .filter(
      (name) => Object.hasOwn(after, name) && after[name] !== before[name],
    )
    .sort()
    .map((name) => `${name}\t${before[name]}\t${after[name]}`);

  if (lines.length > 0) {
    process.stdout.write(`${lines.join('\n')}\n`);
  }
}

main();

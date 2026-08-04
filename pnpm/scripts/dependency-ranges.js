#!/usr/bin/env node
'use strict';

/**
 * Print declared dependency ranges from package.json as JSON.
 *
 * Usage: node dependency-ranges.js <package.json>
 *
 * Omit peer dependencies because `pnpm update` does not modify them.
 */

const fs = require('fs');

const FIELDS = ['dependencies', 'devDependencies', 'optionalDependencies'];

function main() {
  const manifestPath = process.argv[2];

  if (!manifestPath) {
    process.stderr.write('Usage: dependency-ranges.js <package.json>\n');
    process.exit(1);
  }

  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  const ranges = {};

  for (const field of FIELDS) {
    const deps = manifest[field];

    if (!deps || typeof deps !== 'object') {
      continue;
    }

    for (const [name, range] of Object.entries(deps)) {
      if (typeof range === 'string') {
        ranges[name] = range;
      }
    }
  }

  process.stdout.write(`${JSON.stringify(ranges, null, 2)}\n`);
}

main();

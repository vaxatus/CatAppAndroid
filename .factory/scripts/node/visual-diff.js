#!/usr/bin/env node
/**
 * Compares two screenshots and generates a diff image.
 * Uses pixelmatch for pixel-level comparison.
 * Usage: node visual-diff.js <baseline.png> <current.png> [diff_output.png] [--threshold=0.1]
 */

const fs = require('fs');
const path = require('path');
const { PNG } = require('pngjs');
const pixelmatch = require('pixelmatch');

function comparePNGs(baselinePath, currentPath, diffPath, threshold) {
  const baseline = PNG.sync.read(fs.readFileSync(baselinePath));
  const current = PNG.sync.read(fs.readFileSync(currentPath));

  if (baseline.width !== current.width || baseline.height !== current.height) {
    return {
      match: false,
      error: `Size mismatch: baseline ${baseline.width}x${baseline.height} vs current ${current.width}x${current.height}`,
      baselineSize: { width: baseline.width, height: baseline.height },
      currentSize: { width: current.width, height: current.height },
    };
  }

  const diff = new PNG({ width: baseline.width, height: baseline.height });
  const mismatchedPixels = pixelmatch(
    baseline.data,
    current.data,
    diff.data,
    baseline.width,
    baseline.height,
    { threshold: threshold }
  );

  const totalPixels = baseline.width * baseline.height;
  const mismatchPercentage = ((mismatchedPixels / totalPixels) * 100).toFixed(4);

  if (diffPath) {
    fs.writeFileSync(diffPath, PNG.sync.write(diff));
  }

  return {
    match: mismatchedPixels === 0,
    mismatchedPixels,
    totalPixels,
    mismatchPercentage: parseFloat(mismatchPercentage),
    diffPath: diffPath || null,
    dimensions: { width: baseline.width, height: baseline.height },
  };
}

// Parse CLI args
const args = process.argv.slice(2);
if (args.length < 2) {
  console.error('Usage: node visual-diff.js <baseline.png> <current.png> [diff_output.png] [--threshold=0.1]');
  process.exit(1);
}

const baselinePath = args[0];
const currentPath = args[1];
let diffPath = null;
let threshold = 0.1;

for (let i = 2; i < args.length; i++) {
  if (args[i].startsWith('--threshold=')) {
    threshold = parseFloat(args[i].split('=')[1]);
  } else if (!args[i].startsWith('--')) {
    diffPath = args[i];
  }
}

if (!diffPath) {
  const dir = path.dirname(currentPath);
  const name = path.basename(currentPath, '.png');
  diffPath = path.join(dir, `${name}-diff.png`);
}

if (!fs.existsSync(baselinePath)) {
  console.error(JSON.stringify({ error: `Baseline not found: ${baselinePath}` }));
  process.exit(1);
}
if (!fs.existsSync(currentPath)) {
  console.error(JSON.stringify({ error: `Current screenshot not found: ${currentPath}` }));
  process.exit(1);
}

const result = comparePNGs(baselinePath, currentPath, diffPath, threshold);
console.log(JSON.stringify(result, null, 2));

if (!result.match) {
  process.exit(1);
}

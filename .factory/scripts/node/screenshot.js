#!/usr/bin/env node
/**
 * Takes a screenshot of a URL using Playwright.
 * Usage: node screenshot.js <url> [output_path] [--width=N] [--height=N] [--full-page] [--device=name]
 */

const { chromium, devices } = require('playwright');
const path = require('path');
const fs = require('fs');
const os = require('os');

async function takeScreenshot(options) {
  const browser = await chromium.launch({ headless: true });

  let contextOptions = {};
  if (options.device && devices[options.device]) {
    contextOptions = { ...devices[options.device] };
  } else {
    contextOptions = {
      viewport: {
        width: options.width || 1280,
        height: options.height || 800,
      },
    };
  }

  const context = await browser.newContext(contextOptions);
  const page = await context.newPage();

  try {
    await page.goto(options.url, { waitUntil: 'networkidle', timeout: 30000 });

    // Wait for any animations to settle
    await page.waitForTimeout(1000);

    const outputPath = options.output || path.join(
      os.tmpdir(),
      `screenshot-${Date.now()}.png`
    );

    await page.screenshot({
      path: outputPath,
      fullPage: options.fullPage || false,
      animations: 'disabled',
    });

    console.log(JSON.stringify({
      success: true,
      path: outputPath,
      url: options.url,
      viewport: contextOptions.viewport || `device: ${options.device}`,
    }));
  } catch (err) {
    console.log(JSON.stringify({
      success: false,
      error: err.message,
      url: options.url,
    }));
    process.exit(1);
  } finally {
    await browser.close();
  }
}

// Parse CLI args
const args = process.argv.slice(2);
if (args.length === 0) {
  console.error('Usage: node screenshot.js <url> [output_path] [--width=N] [--height=N] [--full-page] [--device=name]');
  console.error('Devices: "Pixel 5", "iPhone 13", "iPad Pro 11"');
  process.exit(1);
}

const options = { url: args[0] };
for (let i = 1; i < args.length; i++) {
  const arg = args[i];
  if (arg.startsWith('--width=')) options.width = parseInt(arg.split('=')[1]);
  else if (arg.startsWith('--height=')) options.height = parseInt(arg.split('=')[1]);
  else if (arg === '--full-page') options.fullPage = true;
  else if (arg.startsWith('--device=')) options.device = arg.split('=')[1];
  else if (!arg.startsWith('--')) options.output = arg;
}

takeScreenshot(options);

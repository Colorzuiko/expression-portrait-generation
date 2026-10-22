#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) {
  console.log('Usage: node scripts/remove_expression_backgrounds.cjs <raw-chroma-dir> <candidate-output-dir> <temp-root> [--prepare-poses] [--matting-cli <path>] [--force]');
  console.log('Default CLI: scripts/image-matting.cjs beside this wrapper. Install sharp first with npm ci at the skill folder.');
  console.log('Use on new pose bases only; expression variants reuse the frozen base alpha.');
  process.exit(0);
}
const prepareIndex=args.indexOf('--prepare-poses');
const preparePoses=prepareIndex!==-1;
if(preparePoses)args.splice(prepareIndex,1);
const forceIndex = args.indexOf("--force");
const force = forceIndex !== -1;
if (force) args.splice(forceIndex, 1);

const cliIndex = args.indexOf("--matting-cli");
let mattingCli = path.join(__dirname, 'image-matting.cjs');
if (cliIndex !== -1) {
  if (!args[cliIndex + 1] || args[cliIndex + 1].startsWith('--')) throw new Error('--matting-cli requires a path');
  mattingCli = args[cliIndex + 1];
  args.splice(cliIndex, 2);
}

if (args.length !== 3) {
  console.error("Usage: node remove_expression_backgrounds.cjs <input-dir> <output-dir> <temp-root> [--matting-cli <path>] [--force]");
  process.exit(1);
}

const [inputDir, outputDir, tempRoot] = args.map((value) => path.resolve(value));
mattingCli = path.resolve(mattingCli);
if (!fs.existsSync(inputDir)) throw new Error(`Input directory not found: ${inputDir}`);
if (!fs.existsSync(mattingCli)) throw new Error(`Matting CLI not found: ${mattingCli}`);
if (inputDir === outputDir) throw new Error('Input and RGBA output directories must be different');

fs.mkdirSync(outputDir, { recursive: true });
fs.mkdirSync(tempRoot, { recursive: true });
const images = fs.readdirSync(inputDir, { withFileTypes: true })
  .filter((entry) => entry.isFile() && path.extname(entry.name).toLowerCase() === ".png")
  .map((entry) => entry.name)
  .sort();
if (images.length === 0) throw new Error(`No PNG files found in ${inputDir}`);

for (const name of images) {
  const input = path.join(inputDir, name);
  const output = path.join(outputDir, name);
  const tempDir = path.join(tempRoot, path.parse(name).name);
  const cliArgs = preparePoses
    ? [path.join(__dirname,'prepare_matted_pose.cjs'),input,output,tempDir,'--matting-cli',mattingCli]
    : [mattingCli, input, output, "--chroma-key", "#00ff00", "--temp-dir", tempDir];
  if (force) cliArgs.push("--force");
  const result = spawnSync(process.execPath, cliArgs, { stdio: "inherit" });
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error(`Background removal failed for ${input}`);
}

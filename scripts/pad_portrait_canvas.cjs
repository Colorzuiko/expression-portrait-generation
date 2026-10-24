#!/usr/bin/env node
// Keep the native RGBA crop unchanged; add transparent pixels around it.
const fs = require('node:fs/promises');
const path = require('node:path');
const { createHash } = require('node:crypto');
const sharp = require('sharp');

function padBottomCenter(data, width, height, target = 720) {
  if (![width, height, target].every(n => Number.isInteger(n) && n > 0)) {
    throw Error('Dimensions must be positive integers');
  }
  if (width > target || height > target) {
    throw Error(`Native crop ${width}x${height} exceeds ${target}x${target}; no automatic resize or subject clipping`);
  }
  if (data.length !== width * height * 4) throw Error('Expected 8-bit RGBA pixels');
  const left = Math.floor((target - width) / 2);
  const top = target - height;
  const output = Buffer.alloc(target * target * 4);
  for (let row = 0; row < height; row++) {
    data.copy(output, ((top + row) * target + left) * 4, row * width * 4, (row + 1) * width * 4);
  }
  return {
    data: output,
    offset: [left, top],
    padding: { left, top, right: target - width - left, bottom: 0 },
  };
}

async function prepareCanvas(input, output, { box, force = false, writeReport = true } = {}) {
  input = path.resolve(input);
  output = path.resolve(output);
  const samePath = process.platform === 'win32'
    ? input.toLowerCase() === output.toLowerCase() : input === output;
  if (samePath) throw Error('Source and output must differ');
  if (path.extname(output).toLowerCase() !== '.png') throw Error('Output must be a PNG');
  if (!force) {
    for (const file of [output, output + '.qa.json']) {
      try { await fs.access(file); } catch (e) { if (e.code === 'ENOENT') continue; throw e; }
      throw Error('Candidate or QA exists; use --force intentionally');
    }
  }
  const original = await fs.readFile(input);
  const metadata = await sharp(original).metadata();
  if (!metadata.hasAlpha) throw Error('Input must already have alpha; matte opaque/chroma sources first');
  if ((metadata.pages || 1) !== 1) throw Error('Expected one still image');
  const crop = box || [0, 0, metadata.width, metadata.height];
  const [left, top, right, bottom] = crop;
  if (crop.length !== 4 || !crop.every(Number.isInteger) || left < 0 || top < 0 ||
      right <= left || bottom <= top || right > metadata.width || bottom > metadata.height) {
    throw Error('Crop box must be [left,top,right,bottom) inside the source');
  }
  const width = right - left, height = bottom - top;
  if (width > 720 || height > 720) throw Error(`Native crop ${width}x${height} exceeds 720x720; no automatic resize or subject clipping`);
  const { data, info } = await sharp(original)
    .extract({ left, top, width, height }).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  if (info.channels !== 4 || info.depth !== 'uchar') throw Error('Expected 8-bit RGBA pixels');
  const padded = padBottomCenter(data, width, height);
  const png = await sharp(padded.data, { raw: { width: 720, height: 720, channels: 4 } }).png().toBuffer();
  const report = {
    status: 'needs-visual-review',
    method: 'bottom-center-transparent-padding',
    input, output,
    source_sha256: createHash('sha256').update(original).digest('hex'),
    output_sha256: createHash('sha256').update(png).digest('hex'),
    source_size: [metadata.width, metadata.height],
    crop_box: crop,
    native_crop_size: [width, height],
    canvas: [720, 720],
    offset: padded.offset,
    padding: padded.padding,
    scale: [1, 1],
    resampled: false,
    native_720: width === 720 && height === 720,
    rgba_copy: 'native crop RGBA bytes copied unchanged; added pixels are [0,0,0,0]',
  };
  await fs.mkdir(path.dirname(output), { recursive: true });
  await fs.writeFile(output, png, { flag: force ? 'w' : 'wx' });
  if (writeReport) await fs.writeFile(output + '.qa.json', JSON.stringify(report, null, 2) + '\n', { flag: force ? 'w' : 'wx' });
  return report;
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes('--help') || args.length < 2) {
    console.log('Usage: node scripts/pad_portrait_canvas.cjs <native-rgba> <candidate-720.png> [--box left top right bottom] [--force]');
    process.exitCode = args.includes('--help') ? 0 : 1;
    return;
  }
  const [input, output] = args;
  let box, force = false;
  for (let i = 2; i < args.length; i++) {
    if (args[i] === '--force') force = true;
    else if (args[i] === '--box') {
      if (i + 4 >= args.length) throw Error('--box needs four integer coordinates');
      box = args.slice(i + 1, i + 5).map(Number); i += 4;
    } else throw Error('Unknown argument: ' + args[i]);
  }
  console.log(JSON.stringify(await prepareCanvas(input, output, { box, force })));
}

module.exports = { padBottomCenter, prepareCanvas };
if (require.main === module) main().catch(e => { console.error(e.message); process.exitCode = 1; });

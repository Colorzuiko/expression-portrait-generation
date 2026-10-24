const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { createHash } = require('node:crypto');
const sharp = require('sharp');
const { padBottomCenter, prepareCanvas } = require('./pad_portrait_canvas.cjs');
const repo = path.resolve(__dirname, '..');

function patterned(width, height) {
  const data = Buffer.alloc(width * height * 4);
  for (let p = 0; p < width * height; p++) {
    data[p * 4] = p % 251;
    data[p * 4 + 1] = p % 197;
    data[p * 4 + 2] = p % 139;
    data[p * 4 + 3] = [0, 1, 128, 254, 255][p % 5];
  }
  return data;
}

function assertPixels(padded, source, width, height) {
  const [left, top] = padded.offset;
  for (let y = 0; y < 720; y++) {
    if (y < top || y >= top + height) {
      assert.ok(padded.data.subarray(y * 720 * 4, (y + 1) * 720 * 4).every(v => v === 0));
    } else {
      const start = (y * 720 + left) * 4;
      assert.deepEqual(padded.data.subarray(start, start + width * 4), source.subarray((y - top) * width * 4, (y - top + 1) * width * 4));
      assert.ok(padded.data.subarray(y * 720 * 4, start).every(v => v === 0));
      assert.ok(padded.data.subarray(start + width * 4, (y + 1) * 720 * 4).every(v => v === 0));
    }
  }
}

test('627 crop is copied at (46,93), with all RGBA bytes and transparent margins preserved', () => {
  const source = patterned(627, 627);
  const result = padBottomCenter(source, 627, 627);
  assert.deepEqual(result.offset, [46, 93]);
  assert.deepEqual(result.padding, { left: 46, top: 93, right: 47, bottom: 0 });
  assertPixels(result, source, 627, 627);
});

test('720 crop stays unchanged and rectangular crops are centered without stretching', () => {
  const full = patterned(720, 720);
  assert.deepEqual(padBottomCenter(full, 720, 720).data, full);
  const rectangle = patterned(111, 499);
  const result = padBottomCenter(rectangle, 111, 499);
  assert.deepEqual(result.offset, [304, 221]);
  assertPixels(result, rectangle, 111, 499);
});

test('oversized and malformed crops are rejected rather than resized or clipped', () => {
  assert.throws(() => padBottomCenter(Buffer.alloc(721 * 627 * 4), 721, 627), /exceeds/);
  assert.throws(() => padBottomCenter(Buffer.alloc(627 * 721 * 4), 627, 721), /exceeds/);
  assert.throws(() => padBottomCenter(Buffer.alloc(0), 0, 627), /positive/);
  assert.throws(() => padBottomCenter(Buffer.alloc(10), 627, 627), /RGBA/);
});

test('PNG crop, CLI, overwrite protection and matting wrapper preserve native dimensions', async t => {
  const reports = path.join(repo, 'output', 'skill-revisions', 'third-edition-bottom-center-padding-v6', 'checks');
  await fs.mkdir(reports, { recursive: true });
  const temp = await fs.mkdtemp(path.join(reports, 'canvas-'));
  const source = patterned(627, 627);
  const input = path.join(temp, '原生627.png');
  await sharp(source, { raw: { width: 627, height: 627, channels: 4 } }).png().toFile(input);
  const original = await fs.readFile(input);
  const output = path.join(temp, 'padded.png');
  const run = (file, args) => spawnSync(process.execPath, [path.join(__dirname, file), ...args], { encoding: 'utf8', cwd: temp });
  await t.test('CLI records no resampling and output PNG retains every crop pixel', async () => {
    const result = run('pad_portrait_canvas.cjs', [input, output]);
    assert.equal(result.status, 0, result.stderr);
    const report = JSON.parse(result.stdout);
    assert.equal(report.resampled, false);
    assert.deepEqual(report.scale, [1, 1]);
    assert.equal(report.native_720, false);
    assert.deepEqual(report.offset, [46, 93]);
    const { data, info } = await sharp(output).raw().toBuffer({ resolveWithObject: true });
    assert.equal(info.width, 720); assert.equal(info.height, 720); assert.equal(info.channels, 4);
    assertPixels({ data, offset: report.offset }, source, 627, 627);
    assert.deepEqual(await fs.readFile(input), original);
  });
  await t.test('existing output and source path are protected; intentional derived overwrite works', async () => {
    assert.notEqual(run('pad_portrait_canvas.cjs', [input, output]).status, 0);
    assert.notEqual(run('pad_portrait_canvas.cjs', [input, input, '--force']).status, 0);
    assert.equal(run('pad_portrait_canvas.cjs', [input, output, '--force']).status, 0);
    assert.deepEqual(await fs.readFile(input), original);
  });
  await t.test('explicit source crop uses the recorded coordinates without changing pixel values', async () => {
    const result = await prepareCanvas(input, path.join(temp, 'box.png'), { box: [20, 30, 120, 230] });
    assert.deepEqual(result.native_crop_size, [100, 200]);
    assert.deepEqual(result.offset, [310, 520]);
    const cropped = await sharp(input).extract({ left: 20, top: 30, width: 100, height: 200 }).raw().toBuffer();
    const data = await sharp(path.join(temp, 'box.png')).raw().toBuffer();
    assertPixels({ data, offset: result.offset }, cropped, 100, 200);
    await assert.rejects(prepareCanvas(input, path.join(temp, 'bad-box.png'), { box: [-1, 0, 100, 200] }), /Crop box/);
  });
  await t.test('oversized full input creates no candidate', async () => {
    const big = path.join(temp, 'big.png');
    await sharp({ create: { width: 721, height: 627, channels: 4, background: '#fff' } }).png().toFile(big);
    const candidate = path.join(temp, 'big-out.png');
    assert.match(run('pad_portrait_canvas.cjs', [big, candidate]).stderr, /exceeds/);
    await assert.rejects(fs.access(candidate));
  });
  await t.test('real matting wrapper pads its native result instead of resizing to 690 or 720', async () => {
    const rgb = Buffer.alloc(627 * 627 * 3);
    for (let y = 0; y < 627; y++) for (let x = 0; x < 627; x++) {
      const color = x >= 150 && x < 477 && y >= 80 && y < 600 ? [190, 70, 50] : [0, 255, 0];
      color.forEach((v, k) => { rgb[(y * 627 + x) * 3 + k] = v; });
    }
    const green = path.join(temp, 'green.png');
    await sharp(rgb, { raw: { width: 627, height: 627, channels: 3 } }).png().toFile(green);
    const candidate = path.join(temp, 'matted.png'), matte = path.join(temp, 'matte');
    const result = run('prepare_matted_pose.cjs', [green, candidate, matte]);
    assert.equal(result.status, 0, result.stderr);
    const report = JSON.parse(result.stdout);
    assert.equal(report.resampled, false);
    assert.deepEqual(report.offset, [46, 93]);
    assert.equal(report.source_sha256, createHash('sha256').update(await fs.readFile(green)).digest('hex'));
    assert.equal(report.native_rgba_sha256, createHash('sha256').update(await fs.readFile(path.join(matte, 'native-rgba.png'))).digest('hex'));
    const native = await sharp(path.join(matte, 'native-rgba.png')).raw().toBuffer();
    const data = await sharp(candidate).raw().toBuffer();
    assertPixels({ data, offset: report.offset }, native, 627, 627);
  });
});

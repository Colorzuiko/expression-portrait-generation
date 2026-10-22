const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const sharp = require('sharp');
const repo = path.resolve(__dirname,'..');
const cli = path.join(__dirname,'image-matting.cjs');
const batch = path.join(__dirname,'remove_expression_backgrounds.cjs');
const run = (script,args,cwd)=>spawnSync(process.execPath,[script,...args],{cwd,encoding:'utf8',env:process.env});

test('bundled matting retains soft alpha, dimensions, inputs and portable batch paths',async t=>{
  const reports=path.join(repo,'output','test-runs','matting');
  await fs.mkdir(reports,{recursive:true});
  const temp=await fs.mkdtemp(path.join(reports,'smoke-'));
  const inputDir=path.join(temp,'綠幕 input');await fs.mkdir(inputDir);
  const input=path.join(inputDir,'pose.png');const w=96,h=96,rgb=Buffer.alloc(w*h*3);
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const coverage=Math.max(0,Math.min(1,(34-Math.max(Math.abs(x-47.5),Math.abs(y-47.5)))/12));
    [190,70,50].forEach((v,k)=>rgb[(y*w+x)*3+k]=Math.round(coverage*v+(1-coverage)*[0,255,0][k]));
  }
  await sharp(rgb,{raw:{width:w,height:h,channels:3}}).png().toFile(input);
  const original=await fs.readFile(input),out=path.join(temp,'rgba.png'),mattes=path.join(temp,'matte');
  await t.test('CLI produces same-sized RGBA plus three masks with soft edges',async()=>{
    const result=run(cli,[input,out,'--chroma-key','#00ff00','--temp-dir',mattes],temp);
    assert.equal(result.status,0,result.stderr);
    const {data,info}=await sharp(out).ensureAlpha().raw().toBuffer({resolveWithObject:true});
    assert.equal(info.width,w);assert.equal(info.height,h);assert.equal(info.channels,4);
    assert.equal(data[3],0);assert.equal(data[(48*w+48)*4+3],255);
    assert.ok(data.some((v,i)=>i%4===3&&v>0&&v<255),'partial-alpha pixels required');
    for(const name of ['concentric-polyhedra.png','soft-chroma-key.png','pixel-wise-min.png'])await fs.access(path.join(mattes,name));
    assert.deepEqual(await fs.readFile(input),original);
  });
  await t.test('existing output is protected without --force',()=>{
    const result=run(cli,[input,out,'--chroma-key','#00ff00','--temp-dir',mattes],temp);
    assert.notEqual(result.status,0);assert.match(result.stderr,/already exists/);
  });
  await t.test('batch finds its sibling CLI from another working directory',async()=>{
    const target=path.join(temp,'透明 output');const result=run(batch,[inputDir,target,path.join(temp,'batch matte')],temp);
    assert.equal(result.status,0,result.stderr);
    assert.deepEqual(await fs.readFile(path.join(target,'pose.png')),await fs.readFile(out));
    assert.deepEqual(await fs.readFile(input),original);
  });
  await t.test('batch refuses to overwrite the input directory',()=>{
    const result=run(batch,[inputDir,inputDir,path.join(temp,'unsafe-matte'),'--force'],temp);
    assert.notEqual(result.status,0);assert.match(result.stderr,/must be different/);
  });
  const thinInput=path.join(temp,'thin-strands.png');
  const thin=Buffer.alloc(w*h*3);
  for(let p=0;p<w*h;p++){thin[p*3]=0;thin[p*3+1]=255;thin[p*3+2]=0;}
  const paint=(x,y,c)=>c.forEach((v,k)=>thin[(y*w+x)*3+k]=v);
  for(let y=30;y<66;y++)for(let x=30;x<66;x++)paint(x,y,[250,230,210]);
  for(let y=8;y<26;y++)paint(12,y,[35,30,40]);
  for(let y=42;y<52;y++)for(let x=42;x<52;x++)paint(x,y,[40,170,210]);
  await sharp(thin,{raw:{width:w,height:h,channels:3}}).png().toFile(thinInput);
  await t.test('preserves one-pixel hair and original opaque cyan clothing',async()=>{
    const out2=path.join(temp,'thin-rgba.png');const result=run(cli,[thinInput,out2,'--chroma-key','#00ff00','--temp-dir',path.join(temp,'thin-masks')],temp);
    assert.equal(result.status,0,result.stderr);
    const data=await sharp(out2).ensureAlpha().raw().toBuffer();
    for(let y=8;y<26;y++)assert.equal(data[(y*w+12)*4+3],255,'thin strand must not be deleted');
    assert.deepEqual(Array.from(data.subarray((46*w+46)*4,(46*w+46)*4+4)),[40,170,210,255]);
    const report=JSON.parse(await fs.readFile(out2+'.qa.json','utf8'));assert.equal(report.status,'passed');assert.equal(report.foreground_deleted_pixels,0);assert.equal(report.opaque_rgb_changed_pixels,0);
  });
  await t.test('rejects a contracting mask that deletes clear foreground',async()=>{
    const out2=path.join(temp,'contracted.png');const result=run(cli,[thinInput,out2,'--chroma-key','#00ff00','--temp-dir',path.join(temp,'contracted-masks'),'--erode-radius','1'],temp);
    assert.equal(result.status,2,result.stderr);const report=JSON.parse(await fs.readFile(out2+'.qa.json','utf8'));assert.equal(report.status,'needs-review');assert.ok(report.foreground_deleted_pixels>0);
  });
});

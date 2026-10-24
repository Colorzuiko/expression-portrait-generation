#!/usr/bin/env node
// Native-resolution matting -> foreground QA -> bottom-center transparent padding.
// Output is a candidate; visually review it before freezing a pose contract.
const fs = require('node:fs/promises');
const path = require('node:path');
const {createHash}=require('node:crypto');
const {spawnSync}=require('node:child_process');
const {prepareCanvas}=require('./pad_portrait_canvas.cjs');

(async()=>{
  const args=process.argv.slice(2);
  if(args.includes('--help')||args.length<3){console.log('Usage: node scripts/prepare_matted_pose.cjs <original-chroma> <candidate-720.png> <temp-dir> [--matting-cli <path>] [--force]');process.exitCode=args.includes('--help')?0:1;return;}
  const [input,output,temp]=args.slice(0,3).map(p=>path.resolve(p));const force=args.includes('--force');
  if(input===output)throw Error('Source and output must differ');
  if(!force){try{await fs.access(output);throw Error('Candidate exists; use --force intentionally');}catch(e){if(e.message.startsWith('Candidate exists'))throw e;}}
  await fs.mkdir(temp,{recursive:true});await fs.mkdir(path.dirname(output),{recursive:true});
  const native=path.join(temp,'native-rgba.png');
  const override=args.indexOf('--matting-cli');
  if(override>=0&&!args[override+1])throw Error('--matting-cli requires a path');
  const mattingCli=override>=0?path.resolve(args[override+1]):path.join(__dirname,'image-matting.cjs');
  const call=[mattingCli,input,native,'--chroma-key','#00ff00','--temp-dir',path.join(temp,'masks')];if(force)call.push('--force');
  const result=spawnSync(process.execPath,call,{encoding:'utf8'});
  if(result.status!==0)throw Error('Native matting did not pass foreground QA: '+result.stderr);
  const report=JSON.parse(await fs.readFile(native+'.qa.json','utf8'));
  if(report.status!=='passed')throw Error('Native foreground QA has not passed');
  const padded=await prepareCanvas(native,output,{force,writeReport:false});
  const sourceHash=createHash('sha256').update(await fs.readFile(input)).digest('hex');
  const review={...padded,workflow_version:'foreground-preserving-v3-bottom-center-padding',input,source_sha256:sourceHash,native_rgba:native,native_rgba_sha256:padded.source_sha256,native_qa:report,alpha_resampling:'none; native matte RGBA pixels copied unchanged'};
  await fs.writeFile(output+'.qa.json',JSON.stringify(review,null,2)+'\n');console.log(JSON.stringify(review));
})().catch(e=>{console.error(e.message);process.exitCode=1;});

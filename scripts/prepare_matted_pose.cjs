#!/usr/bin/env node
// Native-resolution matting -> foreground QA -> premultiplied-alpha resize.
// Output is a candidate; visually review it before freezing a pose contract.
const fs = require('node:fs/promises');
const path = require('node:path');
const {spawnSync}=require('node:child_process');
const sharp=require('sharp');

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
  // Sharp premultiplies alpha around resampling; avoid resizing RGB-on-green.
  const {data,info}=await sharp(native).resize({width:690,height:690,fit:'inside'}).png().toBuffer({resolveWithObject:true});
  const left=Math.floor((720-info.width)/2),top=720-info.height;
  await sharp({create:{width:720,height:720,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).composite([{input:data,left,top}]).png().toFile(output);
  const review={status:'needs-visual-review',workflow_version:'foreground-preserving-v2',input,native_rgba:native,output,native_qa:report,resize:[info.width,info.height],offset:[left,top],canvas:[720,720],alpha_resampling:'Sharp premultiplied alpha; matting performed before resize'};
  await fs.writeFile(output+'.qa.json',JSON.stringify(review,null,2)+'\n');console.log(JSON.stringify(review));
})().catch(e=>{console.error(e.message);process.exitCode=1;});

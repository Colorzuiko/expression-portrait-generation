#!/usr/bin/env python3
"""Build the portable skill ZIP from an explicit source allowlist."""
from pathlib import Path
import hashlib,json,re,zipfile

ROOT=Path(__file__).resolve().parents[1]
FILES=[
 'README.md','LICENSE','THIRD_PARTY_NOTICES.md','CHANGELOG.md','RELEASE_NOTES.md',
 'SKILL.md','SKILL_New.md','SKILL_3RD.md','package.json','package-lock.json','requirements.txt','agents/openai.yaml',
 'references/body-language-catalog-60.md','references/dual-variant-workflow.md','references/expression-catalog-60.md','references/expression-prompts.md','references/image-matting.md','references/local-expression-diffs.md',
 'scripts/compose_expression_patch.py','scripts/image-matting.cjs','scripts/prepare_matted_pose.cjs','scripts/remove_expression_backgrounds.cjs',
 'scripts/render_batch_report.py','scripts/test_render_batch_report.py','scripts/test_compose_expression_patch.py','scripts/test_image_matting.cjs','scripts/make_release.py','scripts/licenses/commander-LICENSE'
]

def build():
    package=json.loads((ROOT/'package.json').read_text(encoding='utf-8'))
    version=package['version']
    if not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('Expected a semantic release version')
    assert (ROOT/'SKILL.md').read_bytes()==(ROOT/'SKILL_New.md').read_bytes()==(ROOT/'SKILL_3RD.md').read_bytes(),'Skill aliases differ'
    names=set(FILES)
    for name in FILES:
        p=ROOT/name
        if not p.is_file():raise FileNotFoundError(name)
        if p.suffix=='.md':
            for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
                if target.startswith(('#','http://','https://','mailto:')):continue
                linked=(p.parent/target.split('#')[0]).resolve()
                if linked.relative_to(ROOT).as_posix() not in names:raise ValueError(f'Unpackaged reference: {name} -> {target}')
    dest=ROOT/'dist';dest.mkdir(exist_ok=True)
    out=dest/f'expression-portrait-generation-v{version}.zip'
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name in sorted(FILES):
            # Normalize text line endings and timestamps for reproducible bytes.
            data=(ROOT/name).read_text(encoding='utf-8').replace('\r\n','\n').encode('utf-8')
            info=zipfile.ZipInfo('expression-portrait-generation/'+name,date_time=(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(FILES)
    digest=hashlib.sha256(out.read_bytes()).hexdigest()
    (dest/'SHA256SUMS').write_text(f'{digest}  {out.name}\n',encoding='utf-8')
    print(json.dumps({'file':str(out),'files':len(FILES),'bytes':out.stat().st_size,'sha256':digest}))

if __name__=='__main__':build()

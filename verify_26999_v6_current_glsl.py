#!/usr/bin/env python3
"""Physical/current-source Experiment C GLSL and optional-resource reference audit.

Strictly additive to successful 26974 validator; does NOT replace or bypass it.
Modes: --inventory (local, create sealed source manifest); --audit (Actions
live and local, check sealed source manifest); --emit (run same check and
write exact selected live GLSL for compiler, no old expanded templates).
Dynamic Kotlin interpolations remain classified as runtime-only: no offline
claim that template text alone has been compiled or is device-proven.
"""
import argparse, hashlib, json, pathlib, re, sys, textwrap

R=pathlib.Path(__file__).resolve().parent
APP=R/'app'
SRC=APP/'src/main/java/com/hinnka/mycamera/processor'
OWN=SRC/'experimentc'
ASSETS=APP/'src/main/assets/experimentc/original129'
PINNED=R/'26999_V6_CURRENT_SHADER_INVENTORY.json'

# ESSL 3.00/3.10 keyword set, including the reserved declarations that
# broke earlier GLSL versions: flat / coherent. Only declaration sites are
# examined: a legal qualifier like `flat in int id;` is not a variable named flat.
RESERVED=set('attribute varying precision highp mediump lowp in out inout uniform buffer shared coherent volatile restrict readonly writeonly const invariant layout flat smooth noperspective patch sample centroid subroutine common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output filter sizeof cast namespace using row_major switch default case struct while do for if else continue break return discard true false void int uint float double bool atomic_uint'.split())
RESERVED.add('packed')
RESERVED |= {'gl_FragColor','gl_FragData','gl_FragCoord','gl_VertexID','gl_Position','gl_GlobalInvocationID'}
TYPE=r'(?:float|int|uint|bool|double|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|isampler\w*|usampler\w*|image\w*|iimage\w*|uimage\w*)'
VAR=re.compile(r'\b'+TYPE+r'\s+([a-zA-Z_]\w*)\b\s*(?=[;=,\[\(\)])')
INTERP=re.compile(r'\$\{[^}]*\}|(?<!\\)\$[A-Za-z_]\w*')
SHADER_INDICATOR=('void main(', 'gl_FragCoord','gl_GlobalInvocationID','gl_Position','sampler2D','texelFetch','imageStore','#version 300 es','#version 310 es')
VERSION=re.compile(r'#version\s+3(?:00|10)\s+es\b')


def sha(data): return hashlib.sha256(data).hexdigest()
def fail(s):raise RuntimeError('26975 V6 C GLSL BLOCKED: '+str(s))

def owners():
    own=list(OWN.rglob('*.kt'))
    own.extend(p for p in SRC.glob('*.kt') if re.match(r'Iris2697[25]C.*\.kt',p.name))
    own.extend(p for p in SRC.glob('C26986Gles*.kt'))
    return sorted(set(own))

def strip_comments(shader):
    # GLSL comments only, not Kotlin. No macro substitution or fake GLSL compile.
    return re.sub(r'//[^\n]*|/\*.*?\*/','',shader,flags=re.S)

def lexical_check(code,label):
    text=strip_comments(code)
    bad=[]
    for m in VAR.finditer(text):
        if m.group(1) in RESERVED or m.group(1).startswith('gl_'):
            bad.append((m.group(1),text.count('\n',0,m.start())+1))
    # GLSL also forbids a reserved keyword in a function declaration or argument.
    for m in re.finditer(r'\b(?:void|'+TYPE+r')\s+([A-Za-z_]\w*)\s*\(',text):
        if m.group(1) in RESERVED or m.group(1).startswith('gl_'):
            bad.append((m.group(1),text.count('\n',0,m.start())+1))
    if bad:fail(f'reserved GLSL identifiers {label}: {bad[:12]}')


def scan():
    result=[];glsl_like=0
    for p in owners():
        source=p.read_text(encoding='utf8')
        for m in re.finditer(r'"""(.*?)"""',source,re.S):
            frag=m.group(1)
            if not any(i in frag for i in SHADER_INDICATOR):continue
            glsl_like+=1
            loc=p.relative_to(APP).as_posix() + ':' + str(source.count('\n',0,m.start())+1)
            lexical_check(frag,loc)
            body=textwrap.dedent(frag).strip()+'\n'
            full=bool(re.match(r'^#version\s+3(?:00|10)\s+es\b',body) and re.search(r'\bvoid\s+main\s*\(',body))
            dynamic=bool(INTERP.search(body))
            # Kotlin concatenated GLSL or trimMargin strings are not standalone
            # compilable sources even when their raw triple quote has main().
            tail=source[m.end():m.end()+130]
            joined=bool(re.match(r'\s*(?:\.trimIndent\(\))?\s*\+',tail))
            if full and not dynamic and not joined:
                stage=('comp' if re.search(r'layout\s*\([^)]*local_size_|gl_GlobalInvocationID',body)
                       else 'vert' if 'gl_Position' in body else 'frag')
                kind='static'
            else:
                stage='dynamic';kind='dynamic'
            result.append({'location':loc,'hash':sha(body.encode()),'kind':kind,'stage':stage,'bytes':len(body.encode()),'version':body.splitlines()[0].strip() if full else '' ,'source':body})
    static=[x for x in result if x['kind']=='static']
    dynamic=[x for x in result if x['kind']=='dynamic']
    if len(static)<130 or len(dynamic)<40:fail(f'unexpected shader count: static={len(static)} dynamic={len(dynamic)}')
    return result,glsl_like

# All sources still mentioning missing optional asset packs remain retained
# as *source code* to keep pinned upstream algorithms intact. They must be
# unreachable from the C entry point's explicitly selected AdobeCurve branch.
OPTIONAL=('luts','spektrafilm','canon','fotufilm','lumix','leica','hncs','dcp','u2netp','frame_glass')
REQUIRED=('noise_profiles','mgc_denoise','mgc_ae','mgc_hdrnet','internal')

def asset_audit():
    for n in OPTIONAL:
        if (ASSETS/n).exists() or (ASSETS/'shaders'/n).exists():fail('optional asset pack reintroduced: '+n)
    for n in REQUIRED:
        if not (ASSETS/n).is_dir() or not any((ASSETS/n).rglob('*')):fail('required donor resource missing: '+n)
    c_entry=(OWN/'Iris26975CPinnedDonorProEngine.kt').read_text()
    for t in ('rawRenderingEngine = RawRenderingEngine.AdobeCurve','rawOutputUpscaleMode = proSabre1x.outputUpscaleMode',
              'embeddedDngRenderPlan = embeddedPlan','sharpeningValue = Iris26975COriginalDonorEngine.DEFAULT_SHARPENING',
              'MultiFrameStacker.processBurstRaw','renderer.processMgcSpatialGpuLinearRgb',
              'rawGpuGainmapProducer.build','Jpeg444ExportEncoder'):
        if t not in c_entry:fail('selected Pro Sabre -> Adobe path changed: '+t)
    for t in ('RawRenderingEngine.Spektrafilm','RawRenderingEngine.Fotufilm','RawRenderingEngine.Canon',
              'RawRenderingEngine.Leica','RawRenderingEngine.Hncs','RawRenderingEngine.Lumix',
              'DcpManager(', 'SpectralFilmProfile.loadCombinedLut','LutManager('):
        if t in c_entry:fail('optional donor style branch called by C entry: '+t)
    # Scan every *literal* donor resource path and distinguish required vs
    # optional-source-only references. Dynamic lookups are reported, not
    # represented as proven reachable/unused.
    present=[];optional_missing=[];unknown=[];dynamic=[]
    for p in sorted(OWN.rglob('*.kt')):
        t=p.read_text(encoding='utf8')
        for m in re.finditer(r'["\'](experimentc/original129/([^"\']+))["\']',t):
            logical=m.group(1)
            rest=m.group(2)
            loc=str(p.relative_to(APP))+':'+str(t.count('\n',0,m.start())+1)
            first=rest.split('/',1)[0]
            if '$' in rest:
                dynamic.append({'owner':loc,'asset':logical,'class':'optional' if first in OPTIONAL else 'review'})
                continue
            if (APP/'src/main/assets'/logical).is_file():present.append({'owner':loc,'asset':logical})
            elif first in OPTIONAL:optional_missing.append({'owner':loc,'asset':logical})
            else:unknown.append({'owner':loc,'asset':logical})
    if unknown:fail('missing nonoptional literal donor assets: '+str(unknown[:8]))
    return {'present_literal_refs':present,'missing_optional_source_only_refs':optional_missing,'dynamic_asset_refs':dynamic,
            'orphan_frame_glass_removed':not (ASSETS/'shaders/frame_glass').exists(),
            'limits':'Source-path guard only; does not establish reachability of dynamically selected original app styles'}

def main():
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True)
    for n in ('inventory','audit','emit','selftest'):g.add_argument('--'+n,action='store_true')
    ap.add_argument('--out',default='photon_26989_outputs/26989_V6_CURRENT_EXTRACTED_GLSL')
    a=ap.parse_args()
    if a.selftest:
        for s in ('#version 300 es\nvoid main(){ float flat=1.; }',
                  '#version 310 es\nvoid main(){ vec2 coherent = vec2(1.); }',
                  '#version 300 es\nvoid main(){ vec4 gl_FragColor = vec4(1.); }',
                  '#version 310 es\nvoid main(){ uint packed = 0u; }'):
            try:lexical_check(s,'selftest')
            except RuntimeError:pass
            else:fail('reserved declaration negative test accepted')
        lexical_check('#version 300 es\nflat in int valid; layout(location=0) out vec4 o; void main(){float flatness=1.;o=vec4(flatness);}', 'selftest valid')
        print('PASS 26975 V6 reserved flat/coherent/gl_ negative and qualifier-positive tests')
        return
    entries,like=scan()
    assets=asset_audit()
    manifest=[{k:x[k] for k in ('location','hash','kind','stage','bytes','version')} for x in entries]
    manifest.sort(key=lambda v:(v['location'],v['hash']))
    actual={'version':'26975-v9-current-actual-RAW-only-donor-and-Iris-C-shaders',
            'sources':manifest,
            'source_count':len(manifest),
            'static_count':sum(s['kind']=='static' for s in manifest),
            'dynamic_count':sum(s['kind']=='dynamic' for s in manifest),
            'glsl_like_count':like,
            'assets':assets}
    if a.inventory:
        PINNED.write_text(json.dumps(actual,sort_keys=True,indent=2)+'\n')
    else:
        if not PINNED.exists():fail('missing authoritative generated shader inventory')
        expected=json.loads(PINNED.read_text())
        if expected!=actual:fail('stale/incorrect GLSL source inventory or asset dependency changed')
    if a.emit:
        root=R/a.out
        root.mkdir(parents=True,exist_ok=True)
        import shutil
        for f in root.iterdir():
            if f.is_file():f.unlink()
        for x in entries:
            if x['kind']!='static':continue
            stem=sha(x['location'].encode())[:12]
            name=stem+'_'+x['hash'][:12]+'.'+x['stage']
            (root/name).write_text(x['source'])
        (root/'COMPILATION_METADATA.json').write_text(json.dumps([{'file':sha(x['location'].encode())[:12]+'_'+x['hash'][:12]+'.'+x['stage'],**{k:x[k] for k in ('location','hash','stage')}} for x in entries if x['kind']=='static'],sort_keys=True,indent=2)+'\n')
        if len(list(root.glob('*.frag')))+len(list(root.glob('*.comp')))+len(list(root.glob('*.vert')))!=actual['static_count']:fail('static GLSL file emission count mismatch')
    print(f'PASS 26975 V6 pinned-current GLSL source+identifier/static-resource audit: {actual["static_count"]} static, {actual["dynamic_count"]} dynamic, {len(assets["missing_optional_source_only_refs"])} optional missing source-only refs, no unclassified static missing paths')
    print('NOTE: dynamic Kotlin-assembled GLSL requires actual device runtime compilation; shader static inventory is NOT device IQ proof')

if __name__=='__main__':
    try: main()
    except Exception as e:
        print(str(e),file=sys.stderr);raise SystemExit(2)

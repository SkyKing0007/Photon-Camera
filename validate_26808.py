#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26808.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
VGN='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
GALLERY='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java'
VER='app/version.properties'; MOD={VGN,GALLERY,VER}
def need(c,m):
    if not c: raise AssertionError(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uni(r): return {p.relative_to(r).as_posix():sha(p) for p in (r/'app').rglob('*') if p.is_file()}
a,c=uni(BASE),uni(CAND); need(len(a)==1782 and len(c)==1782,(len(a),len(c))); need(set(a)==set(c),'file universe changed')
need({p for p in a if a[p]!=c[p]}==MOD,'modified allowlist mismatch')
print('PASS 26808 authority-seeded scope: 1782 -> 1782, exactly 3 modified / 0 added / 0 deleted')
v=(CAND/VER).read_text(); need('VERSION_NAME=0.9726808' in v and 'VERSION_BUILD=26808' in v,'version')
print('PASS 26808 version 0.9726808 / 26808')
g=(CAND/VGN).read_text(); bg=(BASE/VGN).read_text()
for token in ('IRIS_26806_BROAD_2D_BRIGHT_COLOR_OPT_IN','IRIS_26807_HIGHLIGHT_CLEANUP_OUTRANKS_EDGE_PROTECTION','IRIS_26807_CONTIGUOUS_HIGHLIGHT_CLEANUP_TRANSPORT','IRIS_26807_NO_DOWNSTREAM_HIGHLIGHT_CHROMA_RESURRECTION'):
    need(token in g,f'inherited owner missing {token}')
need('float inheritedHighlightPermission=1.0-smoothstep(0.72,0.92,centerNormalizedY);' in g,'successful 26806 highlight curve changed')
for token in ('IRIS_26808_LOCAL_HIGHLIGHT_EDGE_ADMISSION','brightNeutralCoreSum26808','brightNeutralCoreStrongest26808','secondBrightNeutralCore26808','smoothstep(0.78,0.88,firstNormalizedY26808)','smoothstep(0.30,0.46,centerNormalizedY)','smoothstep(0.050,0.105,centerChromaMagnitude)','1.0-smoothstep(0.22,0.34,centerChromaMagnitude)','1.0-smoothstep(0.38,0.70,broadTwoDimensionalMaterial)','localHighlightEdgeCleanupProof26808>0.58'):
    need(token in g,f'26808 bounded seed extension missing {token}')
for token in ('IRIS_26804_PRE_VGN_THIN_NEUTRAL_RIDGE_REPAIR','IRIS_26805_PRE_RESOLVE_NEUTRAL_DISAGREEMENT','uPreResolveCalculationRgb26805'):
    need(token not in g,f'rejected owner returned {token}')
# Simple equation fixtures: requires two-direction core support, moderate luma/chroma, and non-broad material.
def sm(a,b,x):
    if x<=a:return 0.0
    if x>=b:return 1.0
    t=(x-a)/(b-a); return t*t*(3-2*t)
def proof(y,chroma,second,broad,phase=False):
    geom=sm(.30,.78,second); lum=sm(.30,.46,y); band=sm(.050,.105,chroma)*(1-sm(.22,.34,chroma)); non=1-sm(.38,.70,broad)
    if phase: non=1.0
    return geom*lum*band*non
need(proof(.55,.12,.80,.0)>.58,'known contaminated-edge fixture rejected')
need(proof(.55,.12,0.0,.0)==0.0,'no-core fixture admitted')
need(proof(.20,.12,.80,.0)==0.0,'dark center admitted')
need(proof(.55,.38,.80,.0)==0.0,'strong saturated color admitted')
need(proof(.55,.12,.80,.90)==0.0,'broad trusted 2-D material admitted')
print('PASS 26808 seed admission: local highlight-linked moderate chroma only; global 0.72..0.92 curve unchanged; dark/saturated/broad material regressions protected')
f=(CAND/GALLERY).read_text(); bf=(BASE/GALLERY).read_text()
onpause=f[f.index('    public void onPause() {'):f.index('    @SuppressWarnings("deprecation")',f.index('    public void onPause() {'))]
need('IRIS_26808_PAUSE_MUST_NOT_OPEN_SETTINGS' in onpause,'pause owner marker missing')
need('if (manualModeConsole != null && manualModeConsole.isPanelVisible())' in onpause,'manual close guard missing')
need('cameraFragmentViewModel.setSettingsBarVisible(false);' in onpause,'pause settings close missing')
need(onpause.count('mSwipe.SwipeDown();')==1,'unexpected SwipeDown count in onPause')
need('IRIS_26807_FIRST_PRESS_GALLERY_CONTENT_URI_OWNER' in f,'26807 content URI chooser owner lost')
need('Intent chooserIntent = Intent.createChooser(galleryIntent, null);' in f,'chooser owner lost')
print('PASS 26808 gallery lifecycle: chooser/content-URI owner preserved; onPause can close manual panel but can never open gear/settings bar')
for rel in a:
    if rel in MOD: continue
    need(a[rel]==c[rel],f'unexpected protected change {rel}')
print('PASS 26808 protected runtime: 1779 files byte-invariant')

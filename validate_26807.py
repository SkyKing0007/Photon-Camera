#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,textwrap
if len(sys.argv)!=3: raise SystemExit('usage: validate_26807.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
VGN='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
GALLERY='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java'
VER='app/version.properties'
MOD={VGN,GALLERY,VER}
def need(c,m):
    if not c: raise AssertionError(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uni(r): return {p.relative_to(r).as_posix():sha(p) for p in (r/'app').rglob('*') if p.is_file()}
def shader(root,name):
    text=(root/VGN).read_text(); m=re.search(r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',text,re.M); need(m is not None,f'{name}: declaration missing'); b=text.find('""".trimIndent()',m.end()); need(b>=0,f'{name}: terminator missing'); src=textwrap.dedent(text[m.end():b]).strip('\n')+'\n'
    if '$common' in src:
        cm=re.search(r'^\s*private\s+val\s+common\s*=\s*"""',text,re.M); need(cm is not None,'common missing'); cb=text.find('""".trimIndent()',cm.end()); need(cb>=0,'common terminator missing'); common=textwrap.dedent(text[cm.end():cb]).strip('\n'); src=src.replace('$common',common)
    return src

a,c=uni(BASE),uni(CAND)
need(len(a)==1782 and len(c)==1782,(len(a),len(c)))
need(set(a)==set(c),'file universe changed')
mods={p for p in a if a[p]!=c[p]}
need(mods==MOD,f'modified allowlist mismatch {sorted(mods)}')
print('PASS 26807 authority-seeded scope: 1782 -> 1782, exactly 3 modified / 0 added / 0 deleted')
v=(CAND/VER).read_text(); need('VERSION_NAME=0.9726807' in v and 'VERSION_BUILD=26807' in v,'version')
print('PASS 26807 version 0.9726807 / 26807')

g=(CAND/VGN).read_text(); bg=(BASE/VGN).read_text()
# 26806 bright-color gate itself must remain exact: 26807 changes downstream ownership only.
need(shader(BASE,'seed')==shader(CAND,'seed'),'26806 seed/bright-material classifier changed')
for token in (
 'IRIS_26806_BROAD_2D_BRIGHT_COLOR_OPT_IN',
 'float broadTwoDimensionalMaterial=smoothstep(0.45,1.10,remainingPairSupport);',
 'broadTwoDimensionalMaterial*phaseColorOwnershipPermission;',
 'float highlightColorOwnershipPermission=max(inheritedHighlightPermission,realBrightColorProof);'):
    need(token in g,f'26806 successful seed contract missing: {token}')
print('PASS 26807 preserves successful 26806 seed and far-4 broad-2D real-color opt-in byte-identical')

# Failed 26804/26805 RGB authority may not return anywhere in current runtime owner.
for token in (
 'IRIS_26804_PRE_VGN_THIN_NEUTRAL_RIDGE_REPAIR','thinNearWhiteRatio','thinNearWhiteCandidate',
 'IRIS_26805_PRE_RESOLVE_NEUTRAL_DISAGREEMENT','IRIS_26805_PRE_RESOLVE_NEUTRAL_AUTHORITY',
 'IRIS_26805_EXACT_RESOLVE_INPUT_AUTHORITY_LIFETIME','preResolveCalculationRgb26805',
 'uPreResolveCalculationRgb26805','uLensShading26805','uCameraDomainScale26805'):
    need(token not in g,f'rejected 26804/26805 owner returned: {token}')

# Exact immutable bit-13 cleanup ownership must survive all downstream chroma stages.
for token in (
 'IRIS_26807_HIGHLIGHT_CLEANUP_OUTRANKS_EDGE_PROTECTION',
 'if((int(center.a)&0x2000)!=0)edgeProtection=0.0;',
 'bool highlightCleanupOwned26807=(int(e.a)&0x2000)!=0;',
 'highlightCleanupPermission26807=highlightCleanupOwned26807?0.0:1.0;',
 'if(!highlightCleanupOwned26807&&originalMagnitude>192.0',
 'IRIS_26807_CONTIGUOUS_HIGHLIGHT_CLEANUP_TRANSPORT',
 'return highlightInvalidAt(currentP)&&highlightInvalidAt(previousP);',
 'bool highlightCleanupReceivesState26807=i>0&&highlightInvalidAt(p)&&transportAllowed26807;',
 'IRIS_26807_HIGHLIGHT_CLEANUP_OWNERSHIP_HANDOFF',
 'layout(rgba16ui, binding = 2) readonly uniform highp uimage2D uOwnership;',
 'IRIS_26807_NO_DOWNSTREAM_HIGHLIGHT_CHROMA_RESURRECTION',
 'preVgnChromaPresent * artifactPermission * highlightCleanupPermission26807;',
 'float highlightCleanupVeto26807=highlightInvalid26772(p)?1.0:0.0;',
 '(1.0-phaseFloorVeto)*(1.0-highlightCleanupVeto26807);'):
    need(token in g,f'26807 ownership contract missing: {token}')
# Universal pass must consume the already-existing immutable owner map; no allocation/lifetime changes.
need('finalScratch, filteredYccd, originalYccd, sabreSupportR, sabreSupportGb, sabreValidWeights,' in g,'original ownership map not handed to universal stage')
need('bindImage(2, ownership, GLES31.GL_READ_ONLY)' in g,'universal ownership binding missing')
need(g.count('createRgba16UiTexture(')==bg.count('createRgba16UiTexture('),'new VGN image allocation introduced')
need(g.count('allocate("')==bg.count('allocate("'),'new VGN work allocation introduced')
print('PASS 26807 VGN ownership: bit-13 cleanup outranks edge/topology reauthorization through median/directional/IIR/recovery/floor; no new GPU allocation')

# Luma path remains untouched by design: changed downstream shaders only alter chroma permission/state.
for required in (
 'float y=uFilterLuma!=0?apply(ys,currentY,uA10,uB10,true):currentY;',
 'imageStore(uOutput,p,uvec4(uint(clamp(y,0.0,65504.0)),unsignedChroma(int(r)),unsignedChroma(int(q)),px.a));',
 'imageStore(uOutput,p,uvec4(\n                center.r,'):
    need(required in g,f'luma invariant anchor missing: {required[:50]}')
print('PASS 26807 luma invariants: local median pass-through and IIR luma equation preserved')

# Gallery: first saved image caches FileProvider content://, first press always chooser, camera settings bar closes.
f=(CAND/GALLERY).read_text(); bf=(BASE/GALLERY).read_text()
for token in (
 'import androidx.core.content.FileProvider;',
 'IRIS_26807_FIRST_PRESS_GALLERY_CONTENT_URI_OWNER',
 'cameraFragmentBinding.getUimodel().setSettingsBarVisibility(false);',
 '"file".equalsIgnoreCase(latest.getScheme())',
 'Intent chooserIntent = Intent.createChooser(galleryIntent, null);',
 'startActivity(chooserIntent, null);',
 'android.content.ActivityNotFoundException | SecurityException | IllegalArgumentException',
 'imageUri = FileProvider.getUriForFile(',
 'activity.getPackageName() + ".provider"'):
    need(token in f,f'gallery repair missing: {token}')
need('triggerMediaScanner(imageUri = Uri.fromFile(savedFilePath.toFile()))' not in f,'file:// still cached as gallery image URI')
need('startActivity(galleryIntent, null);' not in f,'gallery bypasses chooser')
# Media scanner can keep filesystem URI internally; external gallery target may never dispatch file://.
launch=f[f.index('    public void launchGallery() {'):f.index('    public void launchSettings() {')]
need('Uri.fromFile' not in launch,'launchGallery constructs file URI')
need('FLAG_GRANT_READ_URI_PERMISSION' in launch,'gallery read grant missing')
print('PASS 26807 gallery: fresh capture caches content:// FileProvider URI; file:// dispatch rejected; first press chooser; settings bar closes; launch failures are nonfatal')

# Exact 26806 protected runtime outside 3-file allowlist.
for rel in a:
    if rel in MOD: continue
    need(a[rel]==c[rel],f'unexpected protected change {rel}')
print('PASS 26807 protected runtime: 1779 files byte-invariant, including stacker/Resolve/DNG/UHDR/SR/native/vendor/tone/color transform and 26803 late path')

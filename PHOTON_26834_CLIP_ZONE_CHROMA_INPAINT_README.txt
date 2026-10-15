PHOTON 26834 — CLIP-ZONE CHROMA INPAINT

STATUS: PREPARED / UPLOAD-READY. GitHub Actions must prove real GLSL/Kotlin/Java/NDK/full assemble.
RUNTIME AUTHORITY: successful 26833 run 38631133356, commit bd6f5afdf1429f973afe965729612a24ab834aca, artifact 11926845551.
VERIFICATION MECHANICS: exact successful 26833 17-stage procedure; procedural delta ZERO.
BACKUP: NONE, per user instruction.

RUNTIME ALLOWLIST (exactly 6):
- app/src/main/assets/shaders/motionv2/gainmap.glsl
- app/src/main/assets/shaders/motionv2/render.glsl
- app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
- app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
- app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java
- app/version.properties

26834 CONTRACT
- 26833 SHADOW_LONG remains luminance-only: no LONG hue/chroma/RGB temporal/DNG/SR authority.
- A read-only NORMAL-only scalar sidecar accumulates source-neighborhood headroom confidence. It does not alter Sabre RGB or weights.
- Mask: Z0=1-sum(w*confidence)/sum(w), 2-px dilation, sigma=1 blur, gain=1.6, default clip-start 0.9925.
- Final chroma pass executes after VGN + extended-HDR restoration + 26833 LONG scalar luminance, and immediately before nativeHdrAuthority26601/tone/UHDR.
- M==0 takes an explicit exact-copy branch.
- Chroma uses normalized (R-G)/Y and (B-G)/Y; valid field Wv=(1-M)^2.
- Small fill: sigma 3 full-res. Broad fill: 1/4-res sigma 2.5 (=10 px full-res), bilinear upsample.
- No valid nearby chroma -> neutral fill.
- RGB rebuild exactly preserves Y=(R+2G+B)/4.
- DNG path is outside runtime allowlist and byte-protected.
- Tunables default ON: enable, clip-start, dilation, mask sigma/gain, sigma small/big, Y floor, local-support threshold.
- Runtime log IRIS_26834_CLIP_ZONE_CHROMA reports zoneFraction, mean/max chroma delta, pixelsChanged, maxDeltaPixel, DNG untouched.

- Universal high-zoom barcode guard: producer reserves a target 32 detail texels per side; render and gain-map use exact native Sabre/VGN through the outer 16 texels and transition only 16..24.
- High-zoom reconstruction fails closed to native Sabre/VGN if >=24 trusted halo texels cannot be guaranteed.
- This applies to every high-zoom direct-CFA detail route, not a 30x/120x special case.

UPLOAD IN VSCODE.DEV — THREE COMMITS
1) Upload everything from folder 1 to repository root. Commit: 26834: prepare clip-zone chroma inpaint
2) Upload folder 2 contents, preserving .github/workflows path. Commit: 26834: add clip-zone chroma inpaint workflow
3) Upload folder 3 contents to repository root. Commit: 26834: activate clip-zone chroma inpaint build
Only commit 3 changes TRIGGER_26834.txt and should launch Actions.

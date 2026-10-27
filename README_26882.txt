PHOTON 26882 — THREE-STAGE SOURCE-ONLY VSCODE HANDOFF (NO BACKUP)
Branch: experimental-clean-photon-rebuild. Never modify/push dev. Do not upload APKs.
Runtime authority: successful 26881 Actions 40415858178, commit c28269f36b5754bded0623c104b9dcc1244b15d3, artifact 12695143651.
Verification mechanics: successful 26881 generated 17-stage runner SHA-256 8e9d44d66e4c955c105d136a1c380206ae93b671b9e57806412c2c991a791fc5.
Stage 1 upload contents into repository root preserving all folders; the app source lives under handoff_payload_26882, NEVER upload directly to app/src.
Stage 2 upload its single .github/workflows/build-26882-iris-rawr.yml to exact nested location.
Stage 3 upload its sole TRIGGER_26882.txt and push last, enabling only the intended 26882 workflow.

RUNTIME EXACT CHANGED ALLOWLIST (3):
app/src/main/java/com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt
app/src/main/java/com/unspektrawesome/vulkan/params/RawShaderParameters.kt
app/version.properties
No source deletions, no new native/vendor/DNG, no modifications to experiment routing.

Spektra: correct physically rotated output dimension bounds without shrinking FOV;
original Camera2 RAW input and original JNI library unmodified. Preview/shutter on-device
must still be validated: 26881 log fails before native rendering.
Highlight: preserve original-sensor clipping and B-exclusive white fade shared by HDRq
Super Res OFF and Wronski Super Res ON; relax third-channel requirement smoothly
while protecting fully unclipped and low-blue colored neon. Device scene results are
not proven until testing after Actions success.

LOCAL COMPLETED: exact authority file hashes, candidate manifest, 2006 protected
files invariant, strict 3-file source allowlist, full-index deterministic 7/12/40
forward+rollback, source shader reserved scan, true orientation regression.

NOT RUN LOCALLY: pinned real GLSL compiler, Android Kotlin/Java/NDK compiler,
full :app:assembleDebug or complete 17-stage Actions runner. Strict compiler
and APK proof must pass the new isolated GitHub Actions build before success.

Permanent 26881 historical failure fixtures and hashes are replayed by the
unchanged successful 26881 workflow reconstruction block. New 26882 program
must preserve exact stage order and no shell variables leak between stages.

SOURCE-ONLY UPLOAD: Stage 1 contains 22 files. Do not upload __pycache__/ or
*.pyc/*.pyo files. Neither the handoff hashes nor the upload allowlist include
Python cache files; the Actions runner compiles required Python from .py source.

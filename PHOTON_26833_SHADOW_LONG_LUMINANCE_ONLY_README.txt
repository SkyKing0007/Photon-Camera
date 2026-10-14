PHOTON 26833 — SHADOW LONG LUMINANCE ONLY

STATUS
PREPARED / UPLOAD-READY after the required backup branch is created. Real 26833 GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally. GitHub Actions is authoritative.

RUNTIME AUTHORITY
Successful 26832 Actions compiled candidate only:
commit d4f16fcef30d2220c4c9d08e65bacb26c9089a25
run 38619517561
artifact 11921457067 photon-26832-cfa-chroma-authority-quarantine
artifact SHA-256 9941b0eb16bcd1a832441ea03022c161c1e89bec16cc1da9b253038c8a0edeef
candidate TAR SHA-256 2b40bbff5fc8e3b628cb93285aa5c07b2017b8776a9a73e4a8c7a207bfaef536

VERIFICATION MECHANICS
Exact successful 26832 17-stage build procedure. Procedural delta: ZERO.

26833 RUNTIME CONTRACT
- Fully remove failed 26832 CFA chroma quarantine by restoring the postprocessor to exact successful-26831 bytes/hash.
- SHADOW_LONG never enters NORMAL RGB/chroma/CFA-validity/coverage/temporal-support/DNG/SR accumulators.
- Each LONG is reconstructed only into a temporary private carrier and immediately collapsed to scalar luminance + conservative all-channel scalar support.
- Multiple Night LONGs may accumulate only scalar luminance/support.
- LONG gain is admitted only in dark, low-gradient, supported, radiometrically-consistent regions.
- Resolve/VGN operate on NORMAL(+optional SHORT) RGB only.
- LONG publishes only AFTER VGN by one identical scalar multiplier on R/G/B; hue/chroma direction and RGB ratios are invariant.
- LONG cannot contribute to high-contrast boundaries, highlights, strong edges, hue, chroma, DNG, SR detail, or temporal/noise support counts.

EXACT RUNTIME CHANGED-FILE ALLOWLIST — 5
app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
app/version.properties

REQUIRED BACKUP FIRST
26833 changes LONG ownership and is therefore treated as an architectural/high-risk transition. ChatGPT attempted to create the backup branch through the GitHub connector, but GitHub returned 403. Before Stage 1, create branch:
backup-26832-before-long-luminance-only
from the current experimental-clean-photon-rebuild branch. Current branch HEAD is exactly successful 26832 commit d4f16fcef30d2220c4c9d08e65bacb26c9089a25.
GitHub UI: Code -> branch dropdown -> View all branches -> New branch -> name above -> source experimental-clean-photon-rebuild.
Do not modify dev.

VSCODE.DEV THREE-STAGE UPLOAD
Upload the CONTENTS of each numbered folder to repository root, preserving paths.

STAGE 1: folder 1/
Commit message:
26833: prepare shadow LONG luminance only
Push. No build should trigger.

STAGE 2: folder 2/
Commit message:
26833: add shadow LONG luminance-only workflow
Push. No build should trigger.

STAGE 3: folder 3/
Commit message:
26833: activate shadow LONG luminance-only build
Push. This is the only intended trigger.

DO NOT upload the numbered folder itself. Upload its contents to repository root.
DO NOT push APKs.

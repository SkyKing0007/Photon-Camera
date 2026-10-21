PHOTON 26863 — THREE-STAGE VSCode.dev guarded handoff, experimental-clean-photon-rebuild only.

RUNTIME AUTHORITY: successful 26862 Actions run 39515783515,
  commit 46ebca7eb440ac3a3ca9f24a2de7e9cd671e5f70,
  artifact 12307258881 photon-26862-iris-amaze-ab,
  artifact SHA-256 f061aa238c874d660e331ef0da0c8d809e3c889224c4e30122eea3a6159a1f0b,
  exact 1840-file compiled candidate tar SHA-256 da1f43d7c3e16d0c24742aed0b48e0adbc34fe02d00073302ce361c9906c31bc.
VERIFICATION AUTHORITY: exact successful 26862 inherited guarded 17-stage build
  (26862_SUCCESSFUL_MECHANICS_REFERENCE.sh, pinned glslang 16.5.0; no redesign).
INTENDED RUNTIME ALLOWLIST: exactly 5 B-only Kotlin paths and app/version.properties;
  see 26863_ALL_CANDIDATE_CHANGED_PATHS.txt. Freeze derived candidate, no live app/src edits.
INFRASTRUCTURE: see exact 26863_INFRASTRUCTURE_CHANGED_PATHS.txt; version/authority
  scope, B regression and relevant shaders updated, 17 stages unchanged.
BACKUP: NONE. COMMIT/PUSH: by USER ONLY after independently verifying intended stage.

THREE SEPARATE VSCode.dev commits to trigger ONE intended Actions build:
  1. Upload all ZIP paths EXCEPT .github/workflows/build-26863-iris-amaze-ab.yml
     and TRIGGER_26863.txt. Save replacement files at exact relative paths;
     do not copy into app/src or change app/version.properties in live repo.
     Commit/push stage 1 to experimental-clean-photon-rebuild. No build should trigger.
  2. Upload ONLY .github/workflows/build-26863-iris-amaze-ab.yml;
     commit/push stage 2 to SAME branch. Do not use workflow_dispatch.
  3. Upload ONLY TRIGGER_26863.txt; commit/push stage 3 to SAME branch.
     Intended workflow: Build 26863 Iris AMaZE A/B.

Every guarded build stage uses the actual 26862 successful candidate, not live
repository sources. The guarded script increments 0.9726863 / 26863 and builds
one APK in the same sequence. Do NOT manually run local .sh/.ps1.

B-only change: measured RAW four-phase burst noise tracked through ordinary
CFA temporal moment packing and independent 2x CFA tile pack; true actual
variance/sum(w)^2 and effective support passed through pinned AMaZE; after one
physical LSC, gain^2-aware bounded camera-linear chroma cleanup before temporary
WB; existing B highlight, defringe, FCC, inverse WB and A/long/DNG/UHDR protected.
Reference implementation: RAWR HDR+ Higher quality, NOT its separate algorithm.
No Camera2 or Experiment A B-noise profile fallback. Capture flicker/EV intact.

At handoff: Real 26863 GLSL/Kotlin/Java/NDK/full assemble NOT RUN in this environment.
If any Actions gate fails, do not install APK or claim success; fix failure and
add exact permanent regression. Do not infer 26863 runtime success from 26862.

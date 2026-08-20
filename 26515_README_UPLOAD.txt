PHOTON / IRIS 26515 — SHORT/BENTO EXPOSURE-DOMAIN FIX

Base handoff HEAD:
  e9855a3af7a79801a762ec3f99b441474926f009
Branch:
  experimental-clean-photon-rebuild
Verified backup required by builder:
  backup-26514-before-26515-short-bento-fix-20260820
Expected APK:
  IrisCamera-0.9726515-26515-short-bento-domain-fix-debug.apk

PURPOSE
- Keep the Short/Bento recovery frame. Do NOT disable Short and do NOT loosen/tighten Bento.
- Keep pinned bjzhou MGC Spatial/Bento/noise/native code byte-identical.
- Keep 26513 Spatial 1.10 / 0.40 detail tuning unchanged.
- Keep 26514 luma/chroma/noise-profile/presentation controls unchanged.
- Correct only Iris's consumer boundary for accepted-Short MGC BaselineExposure.

CORRECTION
Before 26515:
  motionV2DisplayGain = referenceDisplayGain * 2^baselineExposureEv
This mixed MGC source-domain normalization into Photon's scene/display authority. Accepted Short
therefore changed MotionV2Render sceneWhite while rejected Short did not.

26515:
  motionV2MgcSourceExposureGain = 2^baselineExposureEv
  motionV2DisplayGain = referenceDisplayGain
The existing linear DisplayExposure pass multiplies the two gains together, preserving the prior
linear pixel product. MotionV2Render sceneWhite uses only reference display gain. UHDR max-gain
capacity still includes the source-domain gain so accepted Short recovery is not discarded.

SAFETY
- apply_26515 writes 26515_RUNTIME_DELTA_FROM_GOLDEN_26514.patch and its SHA before runtime writes.
- validator requires exactly four runtime files to differ from the reconstructed 26514 candidate.
- display_exposure.glsl, render.glsl, color transform, tone controls, MGC core/assets/native closure,
  capture scheduling, denoise controls and UHDR shader are frozen.
- version increment and the only Gradle APK build occur inside the same guarded constructor.
- dev is never modified or pushed.

UPLOAD
Upload this package's files preserving the .github/workflows directory, commit them to
experimental-clean-photon-rebuild, and let the push-triggered workflow run. Do not upload the ZIP
itself into the repository.

CI RETRY NOTE
- This corrected handoff scopes inherited 26514 constructor identity edits to executable top-level
  headers. Duplicate literals inside PYDERIVE/proof heredocs are intentionally ignored.
- This is a constructor-only correction after a pre-source/pre-Gradle failure. Runtime fix, version
  0.9726515 / 26515, and the existing 26514 backup remain unchanged.

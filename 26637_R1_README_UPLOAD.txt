PHOTON / IRIS 26637 R1 — HEIC OPAQUE RGB + P3/sRGB CONTAINER CORRECTION

Runtime authority:
  successful 26636 R1.4 commit 52be30fe45f9492a765efe6437a6b2c1de6b7ff3
  Actions run 34796574775
  artifact 10330345660 (photon-26636-r1-heic-ultrahdr)
  artifact SHA-256 1e27ea4f52618e2dcd42d1eded2e5aa7f8a47350c4f6bdd3e26d41703c5c5307
  compiled-candidate TAR SHA-256 3f6fbb19d7821eaed9a3c76578c5f70edebb14721f920a2e4040fc7da1847960

Verification-mechanics authority:
  exact successful 26636 R1.4 ordering inherited from successful 26635 mechanics:
  sealed package -> exact prior Actions artifact -> deterministic authority-seeded candidate ->
  semantic/regression/ownership checks -> GLSL stage retained (N/A: zero modified shaders) ->
  authority-seeded live byte identity -> real Kotlin/Java -> both NDK ABIs -> deterministic
  full-index forward/rollback patch proof -> PRE-BUILD SAFETY PROOF -> full :app:assembleDebug ->
  exactly one intended APK -> post-build candidate/protected/DNG/native/vendor invariance ->
  deterministic final compiled-candidate export.

No backup is created. No source is pushed or committed by this handoff.

Exact runtime changed-file allowlist (3):
  app/src/main/cpp/iris_heic_jni.cpp
  app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java
  app/version.properties

26637 runtime behavior:
  1) HEIC base publication discards Bitmap alpha and gives libheif opaque interleaved RGB,
     preventing libheif from creating the erroneous auxiliary alpha image/item.
  2) HEIC base NCLX transfer is IEC 61966-2-1 (sRGB), matching the existing Display-P3+sRGB ICC.
  3) Existing Android hardware MediaCodec HEVC 8-bit 4:2:0 encoding behavior is unchanged.
  4) Diagnostic-only logging records hardware codec capabilities plus the actual emitted HEVC SPS
     chroma format / bit depth / profile / level for the later 4:2:2 capability decision.
  5) JPEG/JPEG-R, SABRE/MGC, denoise/noise, exposure, SDR rendering, gain-map production,
     ISO 21496 metadata, 3-stop capacity and 26635 highlight rolloff remain frozen.

Upload/replace the contents of this ZIP at repository root in vscode.dev on branch
experimental-clean-photon-rebuild, commit once, and push. Do not add live app/src edits manually.
The new workflow is build-26637-r1-heic-container-fix.yml; the older 26636 workflow path filters do
not overlap these 26637 names, so one upload/commit launches only the intended 26637 workflow.

Before Actions proof this handoff is only PREPARED / UPLOAD-READY. GitHub Actions is the real
Kotlin/Java/NDK/full-assemble authority.

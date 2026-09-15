PHOTON 26646 R1 — UNIVERSAL HDR SHORT / EDGE-ISOLATED RADIANCE SURVIVAL / TRUE-2X HEIC ULTRA HDR

Runtime authority:
  successful 26645 R1 commit ac23dcf3e5e71cb0b3e668c9ad3f23f5195e9320
  Actions run 35010153364
  artifact 10413177407 photon-26645-r1-visual-short-heic-ui
  artifact SHA-256 a68e42a8a6346a181ee853248a1449270f0da66821c6c4acad45fb8ef400ea94
  exact compiled candidate TAR SHA-256 dfacbda1ae6dacda18c8ee4436376b236a0a7550f8903e5bdd63d16a01157a3d
  candidate universe 1720 app files

Verification-mechanics authority:
  exact successful 26645 build script git blob 7ad58735c84a839035b0dfec3a872066db193918
  exact successful 26645 workflow git blob 6c6e3cd675d0161badbf786779b874e2f8908080
  compiler/native/patch/PRE-BUILD/assemble/postbuild order inherited unchanged.

Backup: NONE, explicitly requested.

Runtime changed-file allowlist: exactly 9, 0 additions.
  app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl
  app/src/main/cpp/CMakeLists.txt
  app/src/main/cpp/iris_heic_jni.cpp
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
  app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
  app/version.properties

26646 intent:
  1) Universal HDR SHORT: retain 26644 fail-closed warped/source-footprint safety, the existing literal/effective-loss rescue and the physical -2.5 EV capture. For the 26645 same-domain correlated-radiance proof only, remove the sparse componentTrust bottleneck and cap its contribution by the exact post-rejection physicalWeight plus SHORT headroom. No semantic mask, grey fill, border synthesis, spatial propagation, late RGB blend or adaptive-EV change.
  2) Tone survival: preserve only extended-linear SourceLinear residual that is missing from CurrentToneLog inside >=3/4 same-material cardinal support. One-sided strong boundaries fail closed; residual is scalar log-luma and capped at 0.18 EV, preserving tree/sky and branch/sky edge neutrality while allowing genuine interior HDR texture to survive the final highlight owner.
  3) HEIC 1x: keep the successful 26645 MediaCodec FULL-range hardware HEVC encoder byte-identical and keep Display-P3/sRGB publication in HEIF NCLX. Android read-back is diagnostic/non-destructive, so a platform-recognition mismatch cannot delete an otherwise structurally saved HEIC; existing asynchronous decode proof is scheduled after save.
  4) HEIC Super Res: remove the old SR+HEIC block and reuse the established true-2x renderer, local-tone map and true-2x gain quotient. Publish the ~50MP base as a 2x2 HEIF grid of hardware-HEVC tiles, box-average the logarithmic true-2x gain carrier to half-linear resolution, and attach the same ISO 21496-1 gain-map relationship to the grid primary. No 12MP fallback, JPEG fallback, x265/software HEVC, gain-map retuning or duplicate ISO metadata version byte.
  5) Successful 26645 manual popup cleanup is outside this runtime delta and protected byte-identical.

Version/build: 0.9726646 / 26646

Delivery: extract this ZIP at repository root on experimental-clean-photon-rebuild, replace same-named files, commit once, push once. The new 26646 workflow is the intended trigger. Do not upload APKs to Git.

Before Actions proof this handoff is only PREPARED/UPLOAD-READY. Real pinned GLSL 16.5.0, Kotlin, Java, both NDK ABIs, full assemble, one-APK, and post-build invariance are authoritative in GitHub Actions.

PHOTON 26644 R1 — VISUAL HIGHLIGHT / SHORT BORDER SAFETY / HEIC RANGE / MANUAL UI

Runtime authority:
  successful 26643 R1 commit 874d4f65af760ae6a2fcfdd119acdc55ed47e78f
  Actions run 34992998426
  artifact 10406636312 photon-26643-r1-aosp-heic-ui
  artifact SHA-256 0c7e02bc53df26d3bf70b6a715ee58c0440381660992d4260cf0a97959d3d9b0
  exact compiled candidate TAR SHA-256 730c28f0dc72d629b53c509659392f9273922e40372fc8cf7f3006d038ce3806
  candidate universe 1720 app files

Verification-mechanics authority:
  exact successful 26643 build script blob c5c6a31b0497f03c8e92a29d3418015f098d110e
  exact successful 26643 workflow blob 3c2eb98c8dc476a7945010cc3133ab7cdb50c345
  compiler/native/patch/PRE-BUILD/assemble/postbuild order inherited unchanged.

Backup: NONE, explicitly requested.

Runtime changed-file allowlist: exactly 6, 0 additions.
  app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java
  app/version.properties

26644 intent:
  1) SHORT: do not change -2.5 EV/capture/effective-loss thresholds. Remove mirrored/clamped synthetic SHORT border ownership. Every complete same-CFA/bilinear source footprint must exist or SHORT weight is zero.
  2) Visual highlight detail: preserve successful 26635 coherent rolloff for genuinely smooth bright fields, but do not suppress small residual structure when balanced local structure is physically present in pre-tone SourceLinear.
  3) HEIC: libheif supplies full-range I420 and native HEIF NCLX is already full-range. Explicitly request MediaCodec COLOR_RANGE_FULL and abort HEIC if output format reports anything else. Native 26643 libheif patch/JNI/ISO21496/gain-map bytes are protected unchanged.
  4) Manual popup: no circularbarlib source change. The app runtime clears the legacy translucent palette rectangle and applies exact AuxButtonText lens typography to Focus/Shutter/ISO/EV values.

Version/build: 0.9726644 / 26644

Delivery: extract this ZIP at repository root on experimental-clean-photon-rebuild, replace same-named files, commit once, push once. The new 26644 workflow is the intended trigger. Do not upload APKs to Git.

Before Actions proof this handoff is only PREPARED/UPLOAD-READY. Real pinned GLSL 16.5.0, Kotlin, Java, both NDK ABIs, full assemble, one-APK, and post-build invariance are authoritative in GitHub Actions.

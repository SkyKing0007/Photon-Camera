PHOTON 26645 R1 — VISUAL HIGH-RADIANCE SHORT / HEIC ANDROID READBACK / MANUAL KNOB CLEANUP

Runtime authority:
  successful 26644 R1 commit d4574c5a0163c6030b8573accb9a5fe6bff86246
  Actions run 35002525151
  artifact 10410108784 photon-26644-r1-visual-short-heic-ui
  artifact SHA-256 45ffa739b72848321fc1f4d6760cdccc446e0893758d49dfa6c681d1a1cdcfbf
  exact compiled candidate TAR SHA-256 9aa4b27d02288bda2601306e56c1b3f4e407fe5cb90fe0715067370630ab501d
  candidate universe 1720 app files

Verification-mechanics authority:
  exact successful 26644 build script git blob 0b879132987c5a20c2ea2e1e4e9290eed8e6eb32
  exact successful 26644 workflow git blob ef12742cdfedfec128a006b4e39f4b2d1c7ac022
  compiler/native/patch/PRE-BUILD/assemble/postbuild order inherited unchanged.

Backup: NONE, explicitly requested.

Runtime changed-file allowlist: exactly 5, 0 additions.
  app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
  app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java
  app/version.properties

26645 intent:
  1) SHORT: retain the proven physical -2.5 EV exposure, flow/alignment, common Sabre accumulator, 26644 fail-closed borders, and old literal/effective-loss recovery. Add a separate visual high-radiance authority using same-domain NORMAL/SHORT spatial correlation: SHORT may receive consequential weight only where it preserves materially greater radiance separation in the same correlated structure. No uncorrelated flat-normal/noise fail-open, no spatial fill, no late RGB blend.
  2) Resolve/tone: retain smooth-field 26635 highlight rolloff, but identify real local texture in SourceLinear, reduce shoulder lift for that structured field, and reserve display headroom for its residual rather than clipping/flattening it into a pale near-white plateau.
  3) HEIC: preserve successful 26644 full-range hardware HEVC transport and all native libheif/NCLX/ISO21496/gain-map bytes. Make Android platform decode of the exact saved HEIC a synchronous fail-closed contract: Display-P3 base, Gainmap present, dimensions equal, and ratio/gamma/epsilon/display-ratio metadata equivalent to the source. A failed readback deletes the HEIC rather than silently publishing non-parity output. No fake BT.709/SDR-video color-aspect substitution and no gain-map retuning.
  4) Manual popup: retain 26644 rectangle removal/typography. Neutralize only circularbarlib KnobView's private translucent background Paint after inflation, preserving knob ticks, text, selection and touch behavior while keeping repo-only circularbarlib source outside app candidate authority.

Version/build: 0.9726645 / 26645

Delivery: extract this ZIP at repository root on experimental-clean-photon-rebuild, replace same-named files, commit once, push once. The new 26645 workflow is the intended trigger. Do not upload APKs to Git.

Before Actions proof this handoff is only PREPARED/UPLOAD-READY. Real pinned GLSL 16.5.0, Kotlin, Java, both NDK ABIs, full assemble, one-APK, and post-build invariance are authoritative in GitHub Actions.

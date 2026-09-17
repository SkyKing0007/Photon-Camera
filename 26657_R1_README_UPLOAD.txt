PHOTON / IRIS 26657 R1 — PHOTON NEW RGB CARRIER CORRECTION

Runtime authority:
  successful 26656 commit fedd17af01cfc113b66e9b56c4c8083bf336d841
  Actions run 35236339680 / artifact 10503720660
  artifact ZIP SHA-256 01d3d26b6dd4bfb9852d1032cd6970584a9cdc41558e96d3c2c05485b0050065
  compiled candidate TAR SHA-256 5f2bd5e9e192b0a0dda3435e4809d43ae89188bb4e77a5236aa035ec78ac3be6

Verification-mechanics authority:
  exact successful 26656 build/handoff order. Functional infrastructure delta is ZERO apart from
  26657 identity, advancing runtime authority to successful 26656, exact 2-path scope, and the
  permanent RGB-carrier regression required by the observed red-only rendering failure.

No backup was created, per user instruction.

Runtime allowlist: exactly 2 paths = 2 modifications + 0 additions:
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
  app/version.properties

Root cause and correction:
  Successful 26656 allocated iris26656PhotonPrepare() output with GLFormat(FLOAT_16), whose
  one-argument constructor sets mChannels=1. photon_new_prepare.glsl outputs vec4 and the first
  LocalLaplacian level consumes RGB, so the R16F attachment discarded G/B and produced the red-only
  image. 26657 changes only that destination to GLFormat(FLOAT_16, 4), i.e. explicit RGBA16F.

LOCKED byte-identical successful-26656 behavior:
  capture/shutter/ISO/AE/frame counts/prebuffer/anti-flicker/NORMAL-SHORT-LONG lifecycle;
  Wronski/Sabre reconstruction; Iris CFA/chromatic-edge protection; Iris color/ACR3; denoise;
  Photon AutoExposureCurve-equivalent pre-color exposure stage; Photon local-white/tone/gamma;
  exact Photon LocalLaplacian shaders/parameters; SR reconstruction/detail; true-2x publication;
  UHDR equations; HEIC/JPEG publication; Night graph; DNG.

No exposure-curve, tone-map, highlight, saturation, color, denoise, SHORT/LONG, SR, or UHDR tuning is
performed in 26657. This build exists only to make the intended 26656 experiment render RGB correctly.

Delivery:
  Upload/replace every file from this ZIP at repository root on experimental-clean-photon-rebuild,
  commit once, and push. Do not upload an APK. GitHub Actions is the authoritative real compiler
  and full-build proof.

Compiler status at handoff preparation:
  Real GLSL/Kotlin/Java/NDK/full assemble are NOT claimed locally. The exact successful 26656
  sequence is packaged so Actions reruns pinned glslang 16.5.0 on the same nine runtime-expanded
  variants, Kotlin/Java, both NDK ABIs, deterministic patch proof, PRE-BUILD, full assemble,
  one-APK proof, and post-build invariance.

PHOTON 26697 SPEKTRA AE 1.1.2 PARITY — TWO-STAGE VSCODE.DEV HANDOFF

Runtime authority: successful 26696 R1 Actions compiled candidate, commit 737d521f6b3439dda2e358ba1b44235967e35297, run 35958217220, artifact 10791487190, artifact SHA-256 8820658f4b06ceaf0fb328b172a5fb9aac8e1f902bd94d240917a9e0ecc976f1, compiled-candidate TAR SHA-256 e0bc256578e3a4d8c7ce524835fb116b992119051f4695aa26aaa2d4708e1866.
Verification mechanics authority: exact successful 26696 R1 build script blob a0d55730e53a0ed4d09f22fc453372663cecf5ee and workflow blob 5518554e40be2b80382545e05b0efc120f479ce2; compiler/build stage order unchanged.
Backup: NONE, per user request.
Runtime scope: exactly 5 modified paths, 0 additions/removals:
  app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraExposureController.java
  app/src/main/java/com/unspektrawesome/camera/session/Camera2RawSession.java
  app/src/main/java/com/unspektrawesome/camera/session/RawCaptureMetadata.java
  app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt
  app/version.properties

26697 correction: preserve the 26696 R1 RAW/Vulkan/meter-generation/processing-ring/warmup/release/save/gallery architecture, but replace the incorrect reconstructed AE semantics with the audited Unspektrawesome 1.1.2 contract: native meter is signed EV; exact Camera2 request generation/requested ISO/actual ISO/shutter/timestamp bind every solve; 1.1.2 target-history/smoothing/rates/deadbands/limits/AE-BAL allocation are retained. No Photo/Android AE substitution, no second 18%-gray conversion, no positive-only meter gate.

Infrastructure delta: identity/scope/regression/authority wrappers only. Successful 26696 R1 compiler/build stage order is unchanged. The obsolete secondary-26694 restore input is removed because the successful 26696 R1 compiled candidate is now sole runtime authority.

Real compiler status before upload: NOT RUN locally. GitHub Actions remains authoritative for pinned GLSL, Kotlin/Java, JNI ABI, both NDK ABIs, full assemble, APK contract and post-build invariance.

STAGE 1
Upload every file/folder from this handoff EXCEPT:
.github/workflows/build-26697-spektra-ae-112-parity.yml
Commit message: 26697 payload and proofs

STAGE 2
Upload only:
.github/workflows/build-26697-spektra-ae-112-parity.yml
Commit message: 26697: activate Unspektra AE 1.1.2 parity build

Do not upload APK files. GitHub Actions is the real compiler/build authority.

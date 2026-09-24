PHOTON 26699 MOTION PERFORMANCE + UI — TWO-STAGE VSCODE.DEV HANDOFF

Runtime authority: successful 26698 Actions compiled candidate, commit 98dcc60feee76570d45c17c34662660c4f6ac62c, run 36052849510, artifact 10831292210, artifact SHA-256 591f472eea7855c4015322341abfa378c500f45c76f3fab3b6371b79bf89510c, compiled-candidate TAR SHA-256 a830a2aa32e45704afc3cf98d6ea112d78109836661dd84a59bfc558c979d312.
Verification mechanics authority: exact successful 26698 build script blob 1a138e9b8cb6c4541397f2033f855552adf8020d and workflow blob 32a56ab993c41b9a9dbb84f3086c38d88dad4432; compiler/build stage order unchanged.
Backup: NONE, per user request.
Runtime scope: exactly 13 modified paths, 0 additions/removals:
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
  app/src/main/java/com/particlesdevs/photoncamera/control/Swipe.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/StageTelemetry.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
  app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/SurfaceViewOverViewfinder.java
  app/src/main/res/layout/camera_fragment.xml
  app/version.properties

26699 performance contract:
  - remove only the seven proven-redundant StageTelemetry completion drains and five proven diagnostic-only Sabre completion drains;
  - preserve timeline-release and EGL-lifecycle completion barriers;
  - preserve the existing full-resolution MGC CPU residual denoise and all capture/fusion/render math;
  - standard Bayer Motion carries the denoised RGBA16F buffer directly into PostPipeline via explicit GL_HALF_FLOAT upload and frees the native carrier immediately after synchronous upload;
  - Night retains its proven RGBA32F bridge;
  - add nanoTime/log-only JPEG-R publication timing without additional file/decode work.

26699 UI contract:
  - Video + RAW Video reject touch-to-focus coordinates inside the actual bottom control-bar region while controls remain usable;
  - RAW Video counter is below the Iris live histogram with 4dp spacing;
  - normal Video uses the same pill for elapsed MM:SS only;
  - all four grid styles are 60% visible (alpha 153/255) and 1.0px wide; grid geometry unchanged.

Protected photography behavior: successful-26698 Camera2/Spektra exposure owners, RAW/ZSL acquisition, frame policy, alignment/fusion/reconstruction, MGC denoise, VGN, color/highlight/tone, UHDR math, JPEG/HEIC codec semantics, DNG and Super Resolution remain unchanged except the explicitly scoped transport/synchronization/timing work above.

Infrastructure delta: identity/scope/regression/authority wrappers only. Exact successful 26698 compiler/build stage order is unchanged.

Real compiler status before upload: NOT RUN locally. GitHub Actions remains authoritative for pinned GLSL, Kotlin/Java, JNI ABI, both NDK ABIs, full assemble, APK contract and post-build invariance.

STAGE 1
Upload every file/folder from this handoff EXCEPT:
.github/workflows/build-26699-motion-performance-ui.yml
Commit message: 26699 payload and proofs

STAGE 2
Upload only:
.github/workflows/build-26699-motion-performance-ui.yml
Commit message: 26699: activate Motion performance and UI build

Do not upload APK files. GitHub Actions is the real compiler/build authority.

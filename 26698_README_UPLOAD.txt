PHOTON 26698 MOTION RUNTIME CLEANUP — TWO-STAGE VSCODE.DEV HANDOFF

Runtime authority: successful 26697 Actions compiled candidate, commit 007440f59feac3788de3e00df67b5e406fc2ce25, run 36008582142, artifact 10811677678, artifact SHA-256 7fa6507954845cae22cec9ef0ffc878d317ade607ce4fcc97e1b78fb4bab525e, compiled-candidate TAR SHA-256 a7716ffbbcb99ccd0db4d43ac8e2e98b35258bab7d0ddd37d2553992f759b5ec.
Verification mechanics authority: exact successful 26697 build script blob 181dfef3ad75d3cd9d10b36193165a1ba997e767 and workflow blob b1c075c8f2e922948e8eef7be3b01177b83b127e; compiler/build stage order unchanged.
Backup: NONE, per user request.
Runtime scope: exactly 6 modified paths, 0 additions/removals:
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
  app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/StageTelemetry.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java
  app/version.properties

26698 correction: preserve the entire successful 26697 camera/viewfinder/exposure/capture/Sabre/post/render/encoder behavior, while stopping only proof/telemetry image work proven to have no production consumer. StageTelemetry remains an exact texture pass-through and retains an explicit GPU completion boundary. Sabre keeps all production fusion/support/reconstruction owners and replaces only proof-only readbacks/probes with explicit completion boundaries. Post-save JPEG/HEIC dimension/gain-map proof decodes are skipped after publication; encoded bytes/save result remain authoritative.

Infrastructure delta: identity/scope/regression/authority wrappers only. Successful 26697 compiler/build stage order is unchanged.

Real compiler status before upload: NOT RUN locally. GitHub Actions remains authoritative for pinned GLSL, Kotlin/Java, JNI ABI, both NDK ABIs, full assemble, APK contract and post-build invariance.

STAGE 1
Upload every file/folder from this handoff EXCEPT:
.github/workflows/build-26698-motion-runtime-cleanup.yml
Commit message: 26698 payload and proofs

STAGE 2
Upload only:
.github/workflows/build-26698-motion-runtime-cleanup.yml
Commit message: 26698: activate Motion runtime cleanup build

Do not upload APK files. GitHub Actions is the real compiler/build authority.

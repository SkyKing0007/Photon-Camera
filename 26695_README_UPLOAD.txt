PHOTON 26695 — SPEKTRA RUNTIME PARITY

Runtime authority: exact successful 26694 Actions compiled candidate.
Commit ee6058be072556c6605b4ea46f1a002802f332f3; run 35943631402; artifact 10785824126.
Artifact SHA-256 fc8b76899753fecbcca682a98ffb02e31688cf488f3bdb6c4306d879eaddd8e2.
Compiled candidate TAR SHA-256 874928c07ce1aeeddd96f440fcfe4f004fce4fc10dac67f0bf9969872fc9e2d9.
Verification mechanics: exact successful 26694 build/workflow mechanics, retaining inherited successful 26693/26691 compiler/build ordering. No backup.

26695 fixes the exact 26694 device failures:
- consume the nativeRender-delivered Unspektra meter instead of immediately polling a second time;
- warm exact native 1.1.2 still/capture startup stages 0..9 before opening Spektra Camera2;
- use Photo's proven CaptureController.isProcessing gate for the yellow shutter processing ring;
- block Spektra -> Iris camera handoff until CameraDevice.onClosed proves transport release.
26694 DCIM/Camera publication, gallery URI bridge, fixed UI geometry, histogram presentation, RAW/RCD/SPEKTRA ownership and exact native library remain preserved.

Upload in two stages:
1. Upload everything EXCEPT .github/workflows/build-26695-spektra-runtime-parity.yml.
2. Commit: 26695 payload and proofs
3. Upload only .github/workflows/build-26695-spektra-runtime-parity.yml.
4. Commit: 26695: activate Spektra runtime parity build
5. GitHub Actions is authoritative compiler/build proof.

Do not commit live app/src directly. The workflow reconstructs the exact candidate from successful 26694 compiled authority.

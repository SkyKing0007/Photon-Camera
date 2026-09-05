Photon 26598 V1.1 — semantic scene-white + exact Motion capture ownership

Runtime authority: exact successful 26597 V1.1 compiled Actions candidate
  commit a46d2fb15a64a7676a92453bbfb2093626841ad1
  run 33920477863 / job 101177394212 / artifact 9954920345
  artifact ZIP SHA-256 0f81d5b344179035d6fe6e2c928a84a31a4a1abe1976117009cff8f4b76b4c46
  compiled-candidate tar SHA-256 3d871181037f5f48500c2be874159286bbba39663cdf67d8b7290c336a66cacc

Verification mechanics: exact successful 26597 implementation and successful 26593 compiler/build order are retained.
Architectural backup: backup-26597-before-26598-capture-ownership -> a46d2fb15a64a7676a92453bbfb2093626841ad1.

Runtime allowlist: exactly 6 files. The five previously audited 26598 scene-white files are byte-identical to the held 26598 V1 candidate; CaptureController.java adds the unified ownership correction.

Scene-white correction:
- Motion final publication uses physical/body baseSceneWhite with the successful 26597 monotonic publication curve.
- Night keeps adaptive sceneWhite.
- 1x, adaptive color safety, and true-2x publication use one Motion publication selector.

Capture correction:
- slider N remains exact NORMAL+SHORT+LONG physical budget; 15+SHORT+LONG = 13+1+1.
- accepted pre-shutter NORMALs become immutable generation-owned slots; missing NORMALs are explicit timestamp-owned Camera2 requests.
- rolling repeating RAWs cannot substitute into the active capture.
- RAW callback drains all queued Motion RAWs.
- one-deep deferred shutter replaces the old silent busy return.
- Super Res uses the same exact capture and does not change frame accounting.
- failures become explicit; no known application-side silent shutter drop/top-up ownership timeout remains.

STATUS AT DELIVERY: PREPARED / UPLOAD-READY ONLY. GitHub Actions must run pinned GLSL, Kotlin, Java, both NDK ABIs, and full assemble before this becomes successful runtime authority.

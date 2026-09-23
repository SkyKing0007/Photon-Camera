PHOTON 26693 — GLOBAL 4:3/16:9 UI GEOMETRY + STANDALONE-OWNED SPEKTRA HISTOGRAM LIFECYCLE

Runtime authority:
- Successful 26692 R1.1 activation commit: e3d7c511920be03fc1854546101a462ca24a8937
- Actions run: 35916329007
- Artifact: 10775875663 / photon-26692-r1-1-spektra-standalone-parity-capture-ui
- Artifact SHA-256: d9a4facc1d6d1cc757f0669f300b7efa761da67a2cc5a3624b5c999469567b32
- Compiled candidate TAR SHA-256: e8d58068812dc119519a8b6b75a70e5be97db25bdc69c5fcba8d9c986f62a960

Verification-mechanics authority:
- Exact successful 26692 R1.1 wrapper implementation, inheriting successful 26691 compiler/build order.
- 26692 build-script blob: 9d57410f3b293eb2f9515227886b133aba7b11bb
- 26692 workflow blob: 756a909d55c274d4e1fcb1dc72da3acd4081d2d1
- No backup branch.

Runtime scope relative to successful 26692 R1.1: exactly 7 modified paths, 0 additions, 0 removals.
- CameraUIViewImpl.java
- camera_fragment.xml
- SpektraLiveHistogramView.java
- SpektraModeController.java
- RawVulkanPreviewController.kt
- VulkanRenderer.kt
- app/version.properties

Locked implementation:
- Preview/dummy aspect remains free to change for 4:3/16:9/Video/RAW Video.
- Fixed camera chrome consumes a dedicated Photo 3:4 control-geometry reference normalized to the root Photo top-shell boundary.
- Video/RAW Video retain recording visuals/behavior but videoStyle is not a control-geometry authority.
- Spektra histogram native acquisition is owned by the Unspektrawesome streaming preview lifecycle; no Iris HandlerThread/pollOnce remains.
- Iris Spektra histogram is presentation-only and keeps Photo-style 64-bin RGB/pill visuals.
- Histogram null/no-frame/capture/stop/teardown states clear safely; presentation exceptions cannot fail the camera session.
- Exact Unspektrawesome 1.1.2 arm64 native .so remains SHA-256 f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd.
- 26692 R1 RawFormat missing-import failure remains a permanent regression.

Upload procedure (same two-stage browser workflow):
1. Upload every visible handoff file/folder EXCEPT the hidden .github workflow and commit as: 26693 payload and proofs
2. Upload only .github/workflows/build-26693-global-ui-spektra-lifecycle.yml and commit as: 26693: activate global UI and standalone Spektra lifecycle build
3. GitHub Actions remains the real GLSL/Kotlin/Java/NDK/full-assemble authority.

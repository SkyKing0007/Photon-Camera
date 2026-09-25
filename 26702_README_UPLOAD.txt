PHOTON 26702 — LOCAL LAPLACIAN A/B + ACTIVE SPEKTRA ORIENTATION

Upload in two stages on experimental-clean-photon-rebuild.
Stage 1: upload every path in 26702_UPLOAD_PATHS.txt except .github/workflows/build-26702-laplacian-ab-spektra-orientation.yml; commit "26702 payload and proofs" and push.
Stage 2: upload only .github/workflows/build-26702-laplacian-ab-spektra-orientation.yml; commit "26702: activate Laplacian A/B and Spektra orientation build" and push.
Do not upload live app/src files directly. No backup branch was created (user explicitly requested none).

RUNTIME AUTHORITY
Successful 26701 commit fdc1a06a0fe252de84f0dfde3593927e7c9a428a
Actions run 36088833926
Artifact 10845117229 photon-26701-highlight-orientation-gainmap
Artifact SHA-256 b83ff245ee439d0b40e90b3b7fcb557e63a9a0cbb8bca57ec4f295140227375e
Compiled candidate TAR SHA-256 cfe219ac6ced5635768dc276125b5d57221fc19d3f1f43d2e76a0a327a0fc6bd
Candidate universe 1823 app files.

VERIFICATION MECHANICS AUTHORITY
Exact successful 26701 build/workflow ordering and toolchain pins.
Build script blob c8c0ce0fea4e3b5b7addd7b7212f4b96946b7a04
Workflow blob 84f0c35d972e2d37dc951c4ca9bfdd2a9ec6527b

RUNTIME SCOPE
Exactly 15 modified runtime files, 0 additions/removals, 1808 protected unchanged.
Native: 819 files total, exactly one intentional native delta (motionv2_jpeg444_jni.cpp), 818 native-protected unchanged.
Vendor 778, DNG 7, asset shaders 271: byte-invariant.

26702 BEHAVIOR
- Fixes saved Spektra still orientation in the active RawVulkanPreviewController capture owner using the same PhotonCamera.Gravity camera rotation Motion freezes. Spektra live preview geometry remains unchanged. The dormant 26701 SpektraCameraOwner orientation attempt is neutralized.
- Adds Motion setting "Local Laplacian Tone", default ON and frozen at shutter.
- ON is exact 26701 Local-Laplacian behavior.
- OFF is a true bypass: neither the primary Local-Laplacian pyramid nor bounded source-preservation pyramid is constructed. Existing global monotonic tone owns SDR presentation; existing byte-identical render/gain-map shaders select their global fallback.
- True2x/Super Res explicitly supports the same ON/OFF contract: ON requires the local-tone map; OFF requires no map and remains Motion HDR/global-tone, not Night/legacy fallback.
- Adds observer-only render begin/end thermal-status and battery-temperature logging; no GPU sync/readback/probe is added.
- 26701 bounded highlight recovery, 26680 stability, observer-only flicker, Sabre, denoise, color, RGBA32F carrier/release, 26701 gain-map byte-array/LUT optimization, JPEG 4:4:4, HEIC, DNG and UHDR shader/math remain protected.

LOCAL PACKAGE STATUS
All locally available authority/semantic/regression/patch/infrastructure gates must pass before this handoff is delivered. Real GLSL/Kotlin/Java/NDK/full assemble/APK/postbuild proof are intentionally Actions-only and must not be claimed before the workflow succeeds.

PHOTON / IRIS 26684 R1 — SPEKTRA VF-S NATIVE SESSION REUSE

Upload/replace every file and folder from this ZIP at the repository root in vscode.dev, preserving paths. Commit and push experimental-clean-photon-rebuild. Do not copy handoff_payload_26684 into app/src manually; Actions reconstructs the candidate from exact successful 26683 compiled authority.

Runtime authority: successful 26683 R1 commit 41f737a4dc726649a8af2b90c68c0634f19944f6, Actions run 35680589765, artifact 10674272396, artifact SHA-256 65b554695d51274ae0c90c37d215ecacc73217c89962903796165c38a789f655, candidate TAR SHA-256 5e398b2501ef95cb34dcf1e2747121063a6e48a9fbc293e6a068ff63f9ff804e.
Verification mechanics authority: exact successful 26683 R1 build-script blob 1d9066fa7d94c70a01aa98ad79077541348627fa + workflow blob 27ad00c50535fdb4e90bb9324034c3365a3fa8df, including pinned glslang 16.5.0 native/CMake repair and successful compiler/build order.
Backup: NONE, per user request. Exact prewrite hashes + deterministic forward/rollback patches included.
Runtime allowlist: exactly 7 modified files / 0 additions / 0 deletions.
Infrastructure delta: 26684 handoff/workflow/validators only; no app build infrastructure change; compiler/build ordering unchanged. The changed SpektraNativeJni.cpp is outside the inherited 804-file protected-native universe, and all 804 protected native files remain byte-identical.

26684 correction: automatic RAW10-first/RAW_SENSOR-fallback lens candidate discovery with real preview/still/resume verification persisted per lens; standalone-default VF-S processing at 480 short edge (640x480 for 4:3), 30fps, saved-only highlight/chroma processing; no Java full-frame RAW10/RAW12 preview unpack; strict row-stride-aware native packed RAW decode; one still request reuses the active full-resolution RAW ImageReader/CaptureSession; exact timestamp pairing; independent watchdog scheduler; hard structural exclusion of every legacy Iris Camera2 open while Spektra is selected/active; saved one-RAW -> .shot -> full RAW/RCD/color -> SPEKTRA -> JPEG100 contract retained.

Expected Actions artifact: photon-26684-r1-spektra-vfs-native-session-reuse
Expected APK: IrisCamera-0.9726684-26684-r1-spektra-vfs-native-session-reuse-debug.apk

PHOTON 26689 R1 — UNSPEKTRAWESOME HOSTED MODE

STATUS: PREPARED / UPLOAD-READY ONLY. NOT ACTIONS-PROVEN YET.
BACKUP: NONE, per user instruction.
BRANCH: experimental-clean-photon-rebuild

RUNTIME AUTHORITY
Successful 26688 R1 compiled candidate:
- commit 166e71a1794157d4cd430d231584d832df5e782e
- Actions run 35791510751
- artifact 10721859325 / photon-26688-r1-spektra-cpu-raw-frontend
- artifact SHA-256 2447ef7bf164b573bdfb9db68aa9fa4f2fcaa2de6436d8476929ea514cebcc8
- candidate TAR SHA-256 7432f115ca9f834d9e0b9fbfd4a2f37f07d3e7fde35ab06dc67537c6f0312039

VERIFICATION-MECHANICS AUTHORITY
Exact successful 26688 procedure. Compiler/build ordering is unchanged.

TARGET
0.9726689 / 26689

RUNTIME SCOPE
55 exact paths:
- 49 additions
- 6 modifications
- 0 deletions
- 1819 candidate files
- 1764 authority files protected byte-identical
- app/src/main/cpp native universe: 819/819 invariant
- vendor protected: 778/778 invariant
- DNG: 7/7 invariant
- existing asset shaders: 271/271 invariant

ARCHITECTURE
Iris is the outer shell only while Spektra is active.
Unspektrawesome owns Camera2 RAW discovery/session, preview Surface lifecycle, newest-frame handling, exposure-meter-driven sensor exposure, RAW/CaptureResult pairing, one-RAW still capture, RCD/SPEKTRA processing, JPEG100 and preview restoration.
The 26688 recreated SpektraCameraOwner/CPU/Vulkan RAW owners remain protected historical bytes but are unreachable from the active SpektraModeController facade.

KEY PERMANENT REGRESSIONS
- Surface exists/is visible before first Spektra frame; no 26688 circular presentation gate.
- no Iris-created pre-camera warmup gate; no 26687 warmup stall.
- no active SpektraRawCpuOwner/SpektraRawVulkanOwner/SpektraRawDevelop path.
- default preview LOW/0.25.
- exactly one full-resolution RAW per shutter.
- newest preview frame policy; no stored preview history/ZSL/temporal stack.
- exact 1.1.2 native .so and 648-byte parameter block hashes.
- nativeCaptureRcd production trailing controls false/true/true/0.
- saved JPEG quality 100.
- no hidden public DNG side effect.
- clean Spektra exit before Iris Camera2 ownership restoration.

COMPILER STATUS AT DELIVERY
- real GLSL: NOT RUN locally; Actions required
- real Kotlin: NOT RUN locally; Actions required
- real Java: NOT RUN locally; Actions required
- real NDK: NOT RUN locally; Actions required
- full :app:assembleDebug: NOT RUN locally; Actions required

UPLOAD
Extract this ZIP into the vscode.dev repository root so the included paths replace/create files exactly. Commit all resulting 26689 handoff files together on experimental-clean-photon-rebuild and push once. Do not copy files into live app/ manually; Actions reconstructs app/ from the exact successful 26688 compiled candidate plus handoff_payload_26689.

Do not upload or commit an APK.

PHOTON 26597 V1.1 — UNIVERSAL HIGHLIGHT PRESERVATION

RUNTIME AUTHORITY
- exact successful 26596 compiled candidate, not live repository app/src
- commit: 00084c9ef2135c92f708441e9e64e33d22e48e5b
- Actions run/job: 33908848179 / 101140212956
- artifact: 9950655842 photon-26596-v1-phase-complete-short-uhdr-sr-handoff
- artifact ZIP SHA-256: 216f52c154f7d7c7fd0693c9dc3b61453dfb80a3b4fd8c312b9ebfb3cfd647b6
- compiled candidate tar SHA-256: 2e799f9510ad9b4f1ddd4f247ad6c6ef1ee4bd083e2923fd9642b573cc9427ec

VERIFICATION MECHANICS AUTHORITY
- exact successful 26596 implementation, inheriting successful 26595/26593 compiler/build order
- successful 26596 build script SHA-256: a6ae1c00e5a08fb5c90e1762e7a571d4237112e384a197eb03f9def04c6e8bb0
- successful 26596 workflow SHA-256: 0ba8a0d3134b1ba2fd38a3797fc85fae36597bffc3f453729cabc05d4cb94077
- successful 26593 compiler/build ordering is not redesigned or reordered

GOAL
Keep Iris overall exposure/body brightness unchanged while reserving enough highlight display range that recoverable bright roads, ground, foliage, cars, walls, clouds, signs and similar surfaces retain visible structure instead of washing toward white. The rule is scene-independent and monotonic; it does not detect roads/windows or use a scene-specific object threshold.

RUNTIME CHANGED FILES — EXACTLY FOUR
1. app/src/main/assets/shaders/motionv2/render.glsl
2. app/src/main/cpp/motionv2_jpeg444_jni.cpp
3. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
4. app/version.properties

IMPLEMENTATION
- Body/midtone/shadow path is unchanged: all global exposure solve/display-gain owners remain protected and byte-identical to 26596.
- At/below the existing Motion highlight start, publication is mathematically identical.
- The recoverable highlight interval uses a body-anchored linear allocation to preserve ordering/separation and keeps the exact 26596 scene-white output anchor.
- Beyond scene white, a C1-matched monotonic rational tail lets true speculars approach white without collapsing the recoverable interval.
- 1x GLSL, true2x CPU and true2x GPU publication use the same math.
- For actual NORMAL sensor loss, the 26596 SHORT final mask no longer lets an unrelated merely-bright SHORT CFA phase veto a clipped phase that SHORT genuinely explains. Whole-RGB restore still fails if any SHORT phase is physically at/near sensor white, if the actually clipped NORMAL phase lacks strict SHORT reserve/explanation, or if the near-clip fail-closed path is used.
- 26596 UHDR capacity/gain-map ownership is preserved unchanged; the corrected SDR base and existing HDR carrier flow through the same UHDR and true2x architecture.
- DNG remains byte-identical.

VERSION
VERSION_NAME=0.9726597
VERSION_BUILD=26597

BACKUP
None, per user request. Deterministic forward/rollback patches are packaged.

DELIVERY
Upload/replace the contents of this ZIP in vscode.dev as one clean handoff commit directly on successful 26596 authority. GitHub Actions is the authoritative real GLSL/Kotlin/Java/NDK/full-assemble proof.

V1.1 compiler correction: the failed V1 Actions run 33917619870 exposed ESSL 3.20 'non-constant initializer' at runtime-expanded motionv2_render_26597. V1.1 preserves the exact highlight math using precomputed IEEE-754 float literals and adds a permanent expanded-shader regression for this failure class.

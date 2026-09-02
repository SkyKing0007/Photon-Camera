Photon Camera 26581 V1 — Foliage/Sky Gap Ownership + SR Edge Envelope

TARGET BRANCH
experimental-clean-photon-rebuild

RUNTIME AUTHORITY
Successful 26580 V1 compiled candidate:
commit a59edaf3cb9f3a476c62e807415bf1c6595aaf84
Actions run 33631623625
job 100252212772
artifact 9847163972
artifact SHA-256 90fc486f8510735acd68c01939cf49a4c9ad5e0d88767867770a3cb408b06c26
compiled-candidate tar SHA-256 97b436af3f3e8c23672b5d43461bae62cfda6fa68a5a28e7861f443ea7b458c8

VERIFICATION-MECHANICS AUTHORITY
Successful 26580 V1. Its authority-seeded handoff/build order is inherited unchanged.

NO BACKUP
Requested by user and appropriate for this localized refinement. Deterministic rollback to exact successful 26580 is packaged.

EXACT RUNTIME CHANGED-FILE ALLOWLIST
app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
app/version.properties

RUNTIME INTENT
- add strict paired foreground/background gap ownership so tiny sky holes use supported sky chroma rather than foreground-majority color;
- add decisive SR cross-edge chroma bridge veto at unambiguous material boundaries;
- replace mixed-material 2x2 block residual centering with material-separated direct-CFA residuals only at proven boundaries;
- add evidence-derived boundary luminance envelope so uniform sky cannot acquire a compensating bright halo while textured foliage retains detail;
- keep 26580 micro-object/text protections, directChromaOwner=false, alignment/flow/phase/HDR/DNG/Night/capture ownership and device-proven GPU publication native bytes unchanged.

LOCAL STATUS
Prepared/upload-ready after exact successful-26580 artifact replay, deterministic transforms, semantic/ownership checks, regressions, reserved-identifier scan, authority manifests and deterministic patch proof.
Real pinned GLSL, Kotlin, Java, NDK and full Android assemble remain Actions authority unless separately reported otherwise.

DELIVERY
Extract this ZIP into the root of experimental-clean-photon-rebuild in vscode.dev, commit once and push. The unique 26581 workflow performs authoritative compiler/build proof.

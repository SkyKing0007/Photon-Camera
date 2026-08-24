Photon Camera 26533 V1.4 — Iris Motion + Night RCD / Jin handoff

TARGET
- Branch: experimental-clean-photon-rebuild
- Exact successful runtime base: 26532 V1.4 / HEAD 22222d162053fefade881a4c37dc388c6f68c581
- Required correction parent: failed 26533 V1.3 handoff HEAD 55bbaae3d86f031d3bb0951554502ba7ed0152fa
- Target version/build remains 0.9726533 / 26533
- Workflow: Build 26533 V1.4 Iris Motion Night RCD Jin

WHAT V1.4 CORRECTS
1. Restores the successful 26532 V1.4 native dependency procedure exactly:
   pinned bjzhou sparse checkout -> app/src/main/cpp/third_party_26507 -> manifest verification there -> compile -> post-build manifest verification.
   The failed V1.3 direct app/src/main/cpp/libultrahdr placement is forbidden.
2. Motion now keeps its proven 26532 MotionBatch / reference / Short-A / MGC Spatial ownership, but standard Bayer rendering crosses the validated fused RAW16 Bayer sidecar into provenance-aware RCD26498 before display exposure/color/tone.
3. Existing direct-RGB Motion output no longer owns normal geometry. It is retained only as a Short-A auxiliary; after RCD, only validated Short-A highlight chromatic ratios can be blended back while RCD luminance/geometry stays authoritative.
4. Night remains Night-owned for exposure/frame policy, uses MGC fused Bayer -> same provenance-aware RCD reconstruction, and does not become Motion mode.
5. 26532 Super-Res/20x/1:1 DNG-JPEG FOV/UltraHDR/DNG/capture behavior remains the base unless explicitly routed above.

STRICT GATES
- exact 951-file successful-26532 candidate artifact + manifest
- exact eight-owner 26532 source contract
- current 26532 provenance-aware RCD26498 source/assets must exist before transform
- temporary candidate transform only
- exact changed-file allowlist from transform
- forward + rollback patch proof before live writes
- inherited shader/Kotlin/native/Java/XML/DNG preflights
- Motion MGC fusion + bridge remain exact 26532 hashes
- Motion graph order: fused Bayer -> RCD26498 -> Short-A chroma-only bridge -> display exposure -> color -> render
- Night graph order: fused Bayer -> RCD26498 -> display exposure -> color -> render
- PRE-BUILD SAFETY PROOF PASSED before version increment
- version increment + exact 26532 native restore + Kotlin/Java compile + assembleDebug in one guarded block
- post-build source/native revalidation
- exactly one APK
- deterministic next-candidate archive

UPLOAD
Upload the contents of this ZIP to the root of experimental-clean-photon-rebuild, preserving .github/workflows.
Do not manually edit app/src or app/build.gradle.

Commit message:
26533 V1.4: restore proven native build and route Motion through RCD

If Actions fails, keep build 26533 and send 26533_build.log. Do not advance to 26534.

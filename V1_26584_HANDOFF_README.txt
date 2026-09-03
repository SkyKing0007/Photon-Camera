Photon / Iris 26584 V1 — All-Scene Highlight Guide + Night Jin Cleanup
Target: 0.9726584 / 26584
Branch: experimental-clean-photon-rebuild

PURPOSE
- Preserve successful 26583 V2 projected broad + compact highlight protection as a strict floor.
- Generalize highlight adaptation beyond global percentile/population thresholds using the complete existing low-resolution projected guide field.
- Let small but coherent practical lights/clouds/windows earn global headroom while isolated sparkles/glints remain ignored.
- Preserve Night mode's intentional +0.30..0.40 EV visibility advantage exactly.
- Keep Jin inference enabled as a final cleanup tool, but constrain its RGB residual so broad color/exposure/style repainting and detail smear cannot own the photograph.

RUNTIME + VERIFICATION-MECHANICS AUTHORITY
Successful 26583 V2:
commit 899c0e654cdab64f473bc9f4b7190a4a265ea733
run 33701626044
job 100481948781
artifact 9873805313
artifact name photon-26583-v2-projected-broad-compact-highlight-tail
artifact ZIP SHA-256 264aa6a22c18179062dfb340465a6170f3632e6136168e6b34aa72afb28f0561
compiled candidate tar SHA-256 ec00b03a6b3ec8c1aae25c126e87af443995bf4da997b258f8f9088f230af388
candidate files 1708

EXACT RUNTIME CHANGED-FILE ALLOWLIST
1 app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java
2 app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java
3 app/version.properties

ALL-SCENE HIGHLIGHT CONTRACT
- 26583 adaptiveSceneWhite is a hard floor: 26584 can only add headroom.
- complete existing low-resolution max-channel guide field is projected through the actual viewfinder gain + successful baseline global tone response
- continuous tail pressure responds smoothly rather than waiting for one population threshold
- spatial coherence lets a small real 2-D highlight region qualify even when global P99/P99.5 population is too small
- one sparkle / two-pixel glint cannot qualify
- no full-resolution readback, no local tone map, no per-channel rendering; final tone remains one scalar on RGB
- below the existing linear 0.50 tone start remains unchanged

JIN CONTRACT
Iris owns the photograph. Jin cleans the photograph.
- Jin ONNX inference remains enabled and byte-identical
- broad/global exposure, WB and color-style residual are centered/rejected fail-closed
- localized/highlight cleanup remains available within bounded luma/chroma caps
- guide detail suppresses Jin correction to protect sharpness/microcontrast
- residual sign cannot reverse and centered magnitude cannot exceed Jin's original proposal
- existing native full-resolution guided transfer remains byte-identical

BACKUP
Backup-ref creation was attempted twice but the GitHub integration returned 403. No backup branch exists and no repository state was changed by those attempts. Exact successful-26583 hashes and deterministic full-index rollback are packaged.

STATUS
Prepared/upload-ready only after final real-artifact local replay succeeds. GitHub Actions remains required for real pinned GLSL, Kotlin, Java, both NDK ABIs, full assemble and final invariance.

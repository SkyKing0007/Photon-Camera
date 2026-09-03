Photon Camera 26585 V1 — Structured Highlight Shape + Tone-Aware Highlight Chroma

Authority: successful 26584 V1 compiled candidate only.
Branch: experimental-clean-photon-rebuild.
No backup branch was requested or created; deterministic rollback to successful 26584 is packaged.

Runtime changes:
1) MotionV2ViewfinderExposureMatcher.java — preserve 26584 all-scene detector but allocate coherent structured highlight shape from P98 toward 0.945 rather than P90/0.965.
2) MotionV2AdaptiveColorAppearance.java — pass solved adaptive sceneWhite to color appearance stage.
3) adaptive_color_appearance_26563.glsl — preserve <=26584 legacy chroma path as floor and permit <=1.12x own-chroma-axis restoration in highlights only when exact post-tone output has gamut headroom.
4) app/version.properties — 0.9726585 / 26585.

Frozen: final render shader, Jin cleanup, Night brightness, Night capture/model/native transfer, Sabre/VGN/SR/alignment, DNG/UHDR, native GPU publication.

Normal delivery: upload/extract this ZIP at repository root in vscode.dev, commit once, push. GitHub Actions performs authoritative real GLSL/Kotlin/Java/NDK/full assemble proof.

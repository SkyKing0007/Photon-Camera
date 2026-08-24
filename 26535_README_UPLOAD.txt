PHOTON CAMERA 26535 — SHARED SPATIAL-RGB / SUPPORT / SUPER RES RELIABILITY

Upload/extract every file in this handoff to experimental-clean-photon-rebuild.
Do not upload to dev. Do not push an APK.

Runtime authority:
- exact successful 26534 Actions artifact: photon-26534-v2-motion-spatial-rgb-night-spatial-bayer
- candidate source TAR SHA256: a595fe6e78a96004a4631d6e6e03bae23c7d3cabd02b7e89fab1a177b324a58c
- exact 26534 candidate source manifest is packaged and verified 962/962
- repository app/src is NOT used as runtime authority

26535 target: 0.9726535 / 26535
Runtime delta: exactly 8 app/src files (6 modified + 2 new).

Architecture:
- Motion: one MGC Spatial-RGB production carrier; DNG Bayer remains export only.
- Night: exact V1.6 timestamp/radiometry metadata -> same one MGC Spatial-RGB core -> shared RGB post -> Jin.
- Night no longer runs Spatial Bayer/RCD and no longer performs a second MGC pass for Super Res.
- Super Res: native 2x detail remains optional. MGC's own rejection/noise-derived Spatial strength map gates only SR detail residual; native Spatial-RGB base is never replaced or blended away.
- New reliability telemetry reports mean/low fraction and an 8x6 spatial grid. It is explicitly NOT called effective frame count.
- Highlight false color: one narrow pre-profile RGB guard, adapted only from RawTherapee's chroma-only false-color principle. It requires near clipping + strong luma edge + local chroma outlier. No hue targeting; luma is mathematically preserved with a gamut-safe correction limit.
- Short/Bento rejection, capture AE, DNG writer, UHDR native encoder, MGC core/AOT and Jin model remain protected unless listed in the 8-file allowlist.

Strict procedure:
Gate 0 -> 1 -> 2 -> 3 -> PRE-BUILD SAFETY PROOF -> Gate 4 version+compile+assemble same block -> Gate 5 -> Gate 6.
Gate 2 uses the exact required git diff and git diff -R commands and fuzz=0 proof in both directions.

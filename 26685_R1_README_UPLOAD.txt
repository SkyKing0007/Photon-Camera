PHOTON 26685 R1 — SPEKTRA VERIFIED AUTO-DISCOVERY + NATIVE RAW GEOMETRY OWNER

Runtime authority: exact successful 26684 R1 Actions compiled candidate.
Verification mechanics authority: exact successful 26684 R1 build/workflow ordering, including native glslang setup.
Backup: none (user explicitly requested no backup).
Runtime scope: exactly 8 modified files, all Spektra runtime files plus app/version.properties; no Photo/Motion/Night/general Iris lens-discovery source changes.

26685 target:
- Spektra-only automatic functional lens discovery on new/changed camera topology.
- Logical/physical route dedupe; RAW capability from lens, MANUAL_SENSOR from opened owner.
- RAW10 first, RAW_SENSOR fallback.
- A lens is admitted only after real VF-S preview + hidden one-RAW still + resumed VF-S.
- Fail-closed Bayer origin ownership; CFA and black-level phase shift together.
- VF-S reconstructs camera RGB from physically adjacent full-RAW photosites off the Camera2 thread before 480-short-edge/640x480 reduction; reduced Bayer is meter-only and never displayed.
- Full-res saved path receives the same verified Bayer-origin/black-level phase contract before RCD.
- Preview logging is throttled; saved processing remains JPEG100 Spektra defaults.

Prepared/upload-ready only until GitHub Actions runs real Java/Kotlin/native/full assemble and post-build invariance.

PHOTON CAMERA — 26533 V1.6 INTEGRATED RCD REGRESSION CORRECTION

Target branch: experimental-clean-photon-rebuild
Base runtime authority: exact successful 26533 V1.5 Actions candidate
Base handoff commit: 10d1aa2c1a37adcfd36533ba4c3879046fd29c3e
Version/build: 0.9726533 / 26533
Backup branch: intentionally NOT created per user instruction
Do not modify or push dev.

Upload/extract this handoff at repository root while on experimental-clean-photon-rebuild.
Commit only the handoff/workflow files supplied here. The workflow reconstructs the exact successful
V1.5 candidate from its Actions artifact, applies the guarded V1.6 transform to an isolated candidate,
proves forward+rollback patches, runs inherited V1.5/26532 preflights plus the new changed-source syntax
and integrated contract checks, reasserts 0.9726533/26533, restores the exact pinned native dependencies,
compiles Kotlin+Java, assembles, post-validates source/native state, and emits exactly one APK.

V1.6 runtime scope (7 files only):
- CaptureController.java: exact Night SENSOR_TIMESTAMP result/request ownership; reuse proven exact per-frame metadata helper.
- ImageFrame.java: retain exact Night result/request beside copied RAW.
- SaverImplementation.java: preserve physical RAW row/pixel stride + logical copied geometry while Image is alive.
- IrisRcdBayerInput.java: preserve V1.5 normalized16 0/65535 domain; replace null->all-NORMAL provenance with GPU CENSORED classification; do not invent SHORT_VALIDATED; neutralize MGC source gain for NORMAL-only Bayer sidecar.
- PostPipeline.java: restore proven source/color/viewfinder/display/manual-control owner ordering after RCD.
- HdrxProcessor.java: Night uses exact first/MGC-base metadata, logical RAW geometry, and strict per-frame radiometric validation.
- IrisNightMgc1271Bridge.kt: exact timestamp/result/request/white metadata only; no fallbacks.

Protected / unchanged by V1.6:
- MGC/Wronski stacker and contribution/rejection logic
- Bento tiling rejection
- Camera2 Motion exposure policy, Short-A capture depth, Long policy
- V1.5 normalized16 black=0 white=65535 correction
- RCD implementation/shaders themselves
- Super Res and zoom behavior
- DNG / 1:1 behavior
- UltraHDR/JPEG-R
- Jin model/runtime
- pinned bjzhou libjpeg/libultrahdr native dependency procedure
- no ADRC fallback; no single-frame fallback
- no heavy provenance CPU readback

Expected GitHub Actions artifact:
photon-26533-v1-6-integrated-rcd-correction

Expected APK inside artifact:
IrisCamera-0.9726533-26533-v1-6-integrated-rcd-correction-debug.apk

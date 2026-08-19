26507 ROOT-FIX HANDOFF — RAW/2 MGC + IMMUTABLE AUX + SHARED HDR REJECTION + UHDR CAPACITY PARITY + JPEG 4:4:4

Branch: experimental-clean-photon-rebuild
Required tested 26506 handoff: 951f63980608eaaf2adba245bdd268a890f6a8ab
Required backup: backup-26506-tested-before-26507-20260818 -> exact same SHA (verified before handoff)
Expected version/build: 0.9726507 / 26507
Expected APK: IrisCamera-0.9726507-26507-mgc-parity-immutable-hdr-jpeg444-debug.apk

WHAT 26507 CHANGES
1. Correct MGC geometry: guide/covariance become RAW/2 (one texel per 2x2 Bayer quad). Removes the old extra center*2 step. Flow-variation threshold is derived from actual guide width: 2016/guideWidth*1e-4.
2. Freeze Short-A/Long-A schedule before Motion processing: only roles actually requested get a bounded 80 ms processing-side completion window; then both slots are permanently sealed. Shutter acknowledgement remains nonblocking.
3. Short-A color now requires BOTH physical Short provenance and the same Wronski/MGC rejection chain used by normal frames before R-G/B-G accumulation.
4. Long-A color now retains 26506 all-four-phase coherence AND also requires the same Wronski/MGC rejection chain before R-G/B-G accumulation.
5. Short topology stays GPU-only: local 8-neighbor Short connectivity suppresses isolated fully-known chroma islands near unresolved clipped regions. No full-frame provenance CPU readback is added.
6. Retires stale 26506 Short provenance immunity so a Short region rejected by the newer topology/MGC gate can still use the normal opponent-confidence reference-chroma safety path.
7. Ultra HDR keeps the correct 26506 SDR=0.80 / HDR target=1.00 signal. It changes only Android full-HDR display-capacity metadata to a bjzhou-style 1.6033 fallback while retaining the higher content ratioMax.
8. Motion JPEG output uses libjpeg-turbo TJSAMP_444 from full-resolution RGBA. Ultra HDR packages that already-compressed 4:4:4 base with libultrahdr instead of recompressing it through Bitmap.compress. No hidden 4:2:0 fallback.

PRESERVED
- Normal Wronski reference anchoring and equal-exposure stack.
- 26504 highlight provenance/exhaustion and Short-A physical recovery.
- 26505 physical Long-A exact Camera2 timestamp/exposure ownership.
- 26506 opponent-confidence chroma and Long-A quad coherence.
- HAL/system AE authority, sharpening off, no ADRC fallback, no single-frame fallback, no PyramidAlignment fallback.
- ParseExif/getMPY untouched.

SAFETY
The Action reconstructs exact tested 26506, emits a pre-change patch/archive BEFORE applying 26507, proves an exact changed-file allowlist, compiles all six changed shaders with pinned glslang 16.5.0, syntax-scans changed Java, fetches only pinned bjzhou commit 09c76e57e8f01a5a8fc536ab41fc80ba642d4042 for native libjpeg-turbo/libultrahdr, then prints PRE-BUILD SAFETY PROOF PASSED before version increment + Gradle build.

UPLOAD
Extract this ZIP at repository root with hidden .github preserved. Commit/push the handoff files only; the workflow reconstructs runtime source during Actions.
Suggested commit message: 26507: fix MGC geometry and unify HDR chroma rejection

26507 V3 native-gate correction (handoff infrastructure only):
- Corrects the pinned bjzhou libultrahdr public API path to libultrahdr/ultrahdr_api.h.
- Adds explicit dependency-layout failures instead of silent `test -f` exits.
- Matches bjzhou CMake's root libultrahdr include contract and disables unused TurboJPEG tools/tests/Java targets.
- No RAW/2, Wronski/MGC, Short-A, Long-A, UHDR signal, or JPEG 4:4:4 runtime math changed from 26507 V2.

PHOTON 26723 — INTELLIGENT FLICKER + HIGH-ZOOM DETAIL

Purpose
- Stop 26720 row-flicker confidence from retroactively promoting an entire selected NORMAL burst to full-strength correction after one detector activation.
- Use OFF/SUSPECT/ACTIVE selected-burst evidence. ACTIVE requires >=3 same-harmonic candidates, >=2 exact selected frames with measured active strength, and >=2 coherent phase-drift transitions. Only exact ACTIVE frames keep their measured strength; no frame is forced to 1.0.
- Preserve the existing physical row-reliability shader for genuinely proven flicker; RAW/preview pixels remain untouched.
- Improve >=20x fine alignment with a high-zoom-only weighted 3x3 quad-luma proxy while the original RAW remains the reconstruction evidence.
- Log accepted 4x4 fractional-offset diversity without adding another GPU readback.
- Add only a bounded 1.00..1.10 support-gated microcontrast gain to the existing zero-mean direct-CFA luminance-detail residual.
- Add no broad spatial luma denoise, no conventional sharpening, and no direct-CFA chroma.
- Preserve successful 26722 native Sabre/VGN chroma ownership exactly.

Authority
- Branch: experimental-clean-photon-rebuild
- Successful runtime authority: 26722 commit 069f19e3f79a803d00339a2a7eb494519b1bce3e
- Actions run: 36357844301
- Artifact: 10944876040 / photon-26722-high-zoom-native-chroma
- Artifact SHA-256: 7e852ac7b1915c5a9c014ae9f3550c8b047f73ccd05fd58c747849b1df750ab2
- Candidate TAR SHA-256: 9b893c74ffab036496f888d1805207beb48b3f3ee2042543a14e1f42a671951e
- Verification mechanics: exact successful 26722 sequence, hash-pinned; compiler/build order and commands unchanged.
- Backup: NONE, per user.

Runtime changed-file allowlist (exactly 4)
1. app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
2. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
3. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
4. app/version.properties

Infrastructure role files (exactly 9)
- .github/workflows/build-26723-intelligent-flicker-high-zoom-detail.yml
- build_26723_intelligent_flicker_high_zoom_detail.sh
- transform_26723.py
- validate_26723.py
- verify_26723_authority.py
- verify_26723_infrastructure.py
- verify_26723_patches.py
- verify_26723_regressions.py
- verify_26723_shaders.py
Infrastructure mechanics differ from successful 26722: NO. Authority/version/scope/applicable validators and names advance only.

Protected behavior
- 26722 native Sabre/VGN chroma owner and same-material topology.
- 26721 RGB32F transport.
- Wronski/Sabre base geometry and original RAW reconstruction evidence.
- LONG/SHORT capture and highlight recovery.
- exposure, tone/color, UHDR, DNG.
- <20x Motion path.
- explicit Super Res 26574 refinement path.
- native/vendor source and assets outside the exact allowlist.

Upload on github.com / vscode.dev
1. Extract this ZIP locally. Do NOT upload the ZIP itself.
2. On experimental-clean-photon-rebuild, upload every listed path EXCEPT the workflow YML. Preserve folders. Commit/push with a message such as:
   26723: prepare intelligent flicker and high-zoom detail
3. Then upload only:
   .github/workflows/build-26723-intelligent-flicker-high-zoom-detail.yml
   Commit/push with a message such as:
   26723: activate intelligent flicker and high-zoom detail
4. Only the intended 26723 workflow should trigger.

Status before Actions
- Exact successful 26722 compiled-candidate authority: PASS.
- Deterministic candidate reconstruction: PASS.
- Exact 4-file runtime allowlist / 1819 protected files: PASS.
- Runtime ownership/regression validation: PASS.
- Native 820 / vendor 1 / DNG 6 invariance: PASS.
- Asset shader universe 271 unchanged: PASS.
- Runtime-expanded shader structural/reserved/hash validation: PASS (10 variants).
- Deterministic full-index forward/rollback patches core.abbrev 7/12/40, fuzz=0: PASS.
- Modified shader-owner Kotlin standalone compile: PASS (supplementary).
- Pinned real glslang 16.5.0: NOT RUN locally; authoritative Actions gate.
- Real project Kotlin/Java compilers: NOT RUN locally; authoritative Actions gates.
- Both NDK ABIs and full :app:assembleDebug: NOT RUN locally; authoritative Actions gates.
- Status: PREPARED / UPLOAD-READY, NOT ACTIONS-PROVEN.

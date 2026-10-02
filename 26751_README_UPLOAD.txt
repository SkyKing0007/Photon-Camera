PHOTON 26751 — FROZEN RECIPROCAL FINE COLOR

Branch: experimental-clean-photon-rebuild
Backup branch: NONE (explicit user instruction).

Upload exactly like successful 26750:
1. Extract this ZIP. Do NOT upload the ZIP itself.
2. Upload/replace every path listed in 26751_UPLOAD_PATHS.txt EXCEPT the workflow YML; preserve folders.
3. Commit with: 26751: prepare frozen reciprocal fine color
4. Upload only .github/workflows/build-26751-frozen-reciprocal-fine-color.yml.
5. Commit with: 26751: activate frozen reciprocal fine color
6. Push. Only the intended 26751 workflow should trigger.

Runtime authority: exact successful 26750 Actions compiled candidate (run 37039400846, commit 2202d37797d0feb6c40d58d1eea4deaeab3110c8, artifact 11242915354).
Verification mechanics: exact successful 26750 procedure; procedural delta ZERO.
Runtime scope: exactly 2 files, no additions/deletions.

26751 removes the unsafe 26750 per-pixel pre-VGN hue replacement. The clean VGN result remains authoritative. A frozen sparse seed map is created only where color is genuinely missing, same-hue/same-luma source evidence is bounded in both axes, CFA validity is near-perfect, a nearby material boundary proves fine structure, a saturated different-luma background does not explain the hue, and the inherited highlight lock permits it. A separate non-recursive pass restores only missing color from local seed consensus. Restored pixels can never alter their own ownership map.

Device regressions made permanent: multi-pixel horizontal teeth/zipper lines, blue contamination inside white text, nonuniform red glyphs, cross-material chroma leakage, and gray/QR/maze blocks inside uniform blue. Black/white neutral polarity and highlight hard-lock remain required. Super Res continues using the same corrected native Sabre/VGN chroma guide with direct CFA luma/detail only.

Pre-upload status: prepared/upload-ready, NOT Actions-proven. Real pinned glslang 16.5.0, project Kotlin/Java, both NDK ABIs and full :app:assembleDebug will run in GitHub Actions in the unchanged successful-26750 order.

PHOTON 26859 — EXACT SUCCESSFUL 26858 GUARDED A/B BUILD
BRANCH: experimental-clean-photon-rebuild only. NO backup, no dev, no APK push.
Successful runtime: 26858 run 39414428763, commit 7f8f747e6258ab8e47c1658405407fef06a91aab, artifact 12261820369.
Mechanics: exact successful 26858 guarded 17 stages, commands and candidate freeze.

UPLOAD USING vscode.dev, THREE SEPARATE STAGES (<100 files each):
1. Upload CONTENTS of STAGE_1_ROOT to repository root with paths intact. Commit & push. No 26859 workflow triggered.
2. Upload CONTENTS of STAGE_2_WORKFLOW including .github/workflows path. Commit & push. Still no 26859 trigger.
3. Upload CONTENTS of STAGE_3_TRIGGER: TRIGGER_26859.txt. Commit & push. Exactly this push triggers intended 26859 Actions build.

DO NOT upload handoff_payload_26859/app/* into live app/src.
The successful compiled 26858 candidate, not stale live app/src, is reconstructed, frozen, and overlaid with exactly two B source files and guarded app/version.properties = 0.9726859/26859.
All other 1836 candidate files are protected byte-for-byte, including A/Sabre, native/vendor/DNG and native AMaZE.
Preserves B temporal CFA merge, 26857 WB, AMaZE, Lab then FCC, NORMAL+LONG no SHORT, DNG/UHDR, all lens zoom/true2x and A/B/A+B settings.
B changes ONLY: smooth sensor clip white fading without hue propagation; single per-physical-lens LSC; post-LSC noise variance-aware residual chroma at original alpha cap.
NO RAWR HDR+ Quality frequency merger.

This package, when exact prebuild gates replay successfully, is PREPARED/UPLOAD-READY, NOT compiler or build-proven.
GitHub Actions real compiler/build/proof remains authoritative.
If Actions fails: STOP and inspect exact failure; never bypass gate.
No changes to dev, backup, source commits/pushes or APK delivery by ChatGPT.

Commit suggestions:
Stage 1: 'Photon 26859 sealed B-only source and guarded proof'
Stage 2: 'Photon 26859 single guarded Actions workflow'
Stage 3: 'Trigger Photon 26859 guarded build'

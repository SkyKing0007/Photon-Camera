26775 — Resolve/VGN CFA-Phase Chroma Validity

Use vscode.dev in exactly three stages. Do not combine root and .github/workflows uploads.

STAGE 1 — repository root
Upload all contents of STAGE1_UPLOAD_TO_REPO_ROOT.
Commit message:
26775: upload Resolve VGN phase-validity correction
Push. No 26775 Actions run should start.

STAGE 2 — .github/workflows only
Upload only build-26775-resolve-vgn-phase-validity.yml into .github/workflows/.
Commit message:
26775: add Resolve VGN phase-validity workflow
Push. No 26775 Actions run should start.

STAGE 3 — repository root
Upload only TRIGGER_26775.txt.
Commit message:
26775: trigger Resolve VGN phase-validity build
Push.

Expected workflow:
Build 26775 Resolve VGN Phase Validity

Expected artifact:
photon-26775-resolve-vgn-phase-validity

Expected APK inside artifact:
IrisCamera-0.9726775-26775-resolve-vgn-phase-validity-debug.apk

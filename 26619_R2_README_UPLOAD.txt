PHOTON 26619 R2 — MONOTONIC GUIDED BASE/DETAIL COMPILER REPAIR

UPLOAD METHOD (vscode.dev)
1. Stay on branch experimental-clean-photon-rebuild at failed 26619 R1 parent commit 7a0532a9aa26ea0d92ab71c8d7c6965a9139524b.
2. Upload/extract ALL files in this handoff ZIP to the repository ROOT, preserving folders.
3. DO NOT copy handoff_payload_26619_r2/app/** into the live repository app/** tree manually.
4. Source Control must contain only the sealed 26619 R2 handoff/infrastructure paths. No live app/src/** changes are allowed in the handoff commit.
5. Commit once with: 26619 R2 native namespace compiler repair
6. Push once. The intended workflow is Build 26619 R2 Monotonic Guided Base Detail Compiler Repair.

RUNTIME AUTHORITY
Successful 26618 R1 commit: 34dce306c8f1b333511db8e2fbdb58555e9e9bd2
Actions run: 34426075869
Artifact ID: 10132769400
Artifact: photon-26618-r1-guided-base-detail-ltm
Artifact ZIP SHA-256: 3121977d6f6064e6cd2f41e3ad913572505df2f3a892671736af8ef0db1327f1
Compiled candidate TAR SHA-256: 150e70d4b044ae8c3caa35758f5dbbffa505dd31b80ec76c535864f55645e3ea
Candidate universe: 1712 app files

FAILED R1 EVIDENCE
Failed 26619 R1 commit: 7a0532a9aa26ea0d92ab71c8d7c6965a9139524b
Actions run: 34430769401
Failure gate: real NDK arm64-v8a compile, before PRE-BUILD/assemble.
Exact failure: unqualified smooth01 in iris26619MapMotionBroadBase; compiler identified iris26564::smooth01 as the intended symbol.

R2 REPAIR
The 26619 rendering algorithm is unchanged from R1. R2 changes exactly one line relative to failed R1 candidate:
  smooth01(...) -> iris26564::smooth01(...)
R2 is nevertheless reconstructed directly from successful 26618, so failed R1 never becomes runtime authority.

VERIFICATION-MECHANICS AUTHORITY
Exact successful 26618 R1 procedure. Ordering/isolation/compiler/NDK/patch/PRE-BUILD/assemble/invariance mechanics are not redesigned or reordered.

DO NOT manually edit app/src. GitHub Actions reconstructs the exact corrected candidate from the successful 26618 compiled artifact.

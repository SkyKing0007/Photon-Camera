PHOTON 26619 R1 — MONOTONIC GUIDED BASE/DETAIL FINAL COMPOSITION

UPLOAD METHOD (vscode.dev)
1. Stay on branch experimental-clean-photon-rebuild at successful 26618 parent commit 34dce306c8f1b333511db8e2fbdb58555e9e9bd2.
2. Upload/extract ALL files in this handoff ZIP to the repository ROOT, preserving folders.
3. DO NOT copy handoff_payload_26619/app/** into the live repository app/** tree manually.
4. Source Control must contain only the sealed 26619 handoff/infrastructure paths. No live app/src/** changes are allowed in the handoff commit.
5. Commit once with: 26619 R1 monotonic guided base detail
6. Push once. The intended workflow is Build 26619 R1 Monotonic Guided Base Detail.

RUNTIME AUTHORITY
Successful 26618 R1 commit: 34dce306c8f1b333511db8e2fbdb58555e9e9bd2
Actions run: 34426075869
Artifact ID: 10132769400
Artifact: photon-26618-r1-guided-base-detail-ltm
Artifact ZIP SHA-256: 3121977d6f6064e6cd2f41e3ad913572505df2f3a892671736af8ef0db1327f1
Compiled candidate TAR SHA-256: 150e70d4b044ae8c3caa35758f5dbbffa505dd31b80ec76c535864f55645e3ea
Candidate universe: 1712 app files

VERIFICATION-MECHANICS AUTHORITY
Exact successful 26618 R1 procedure, itself inheriting successful 26614 mechanics. Ordering/isolation/compiler/NDK/patch/PRE-BUILD/assemble/invariance mechanics are not redesigned or reordered.

26619 RUNTIME INTENT
Replace the defective 26618 pre-render RGB gain with one final-owner guided base/detail composition. The guided stage publishes only a broad log tone-guide base. MotionV2Render maps that base with a strictly monotonic C1 curve, then recombines the measured local log-detail residual with one common RGB scalar. The same base field and equation are consumed by true2x CPU/cached/GPU publication.

DO NOT manually edit app/src. GitHub Actions reconstructs the exact candidate from the successful 26618 compiled artifact.

PHOTON 26864 — ONE THREE-STAGE VSCODE.DEV HANDOFF
State: PREPARED FOR GITHUB ACTIONS COMPILATION ONLY; NOT BUILD-PROVEN.

Runtime authority: successful 26863, run 39532545701, artifact 12316461434, commit eaefa4a7836a5495d82edad9538482325d9e005c.
Compiled candidate TAR SHA-256: 145752aa6f7ca75361562193d57513dd0fb39475e4511c702bad3f6c2b208510.
Verification mechanics: exact successful 26863, inherited from successful 26862, guarded 17-stage build and candidate-first authority reconstruction.
Pinned RAWR upstream: ce767e80bfce2e1641abf7dad6b1bf504d844fd9.

IMPORTANT: Work on branch experimental-clean-photon-rebuild ONLY. Do not touch dev.
Commit/push each stage only after the prior stage is committed. Never upload APKs, extracted app/ contents or intermediate candidates.

STAGE 1 — Upload the CONTENTS of STAGE_1/ to the repository root in vscode.dev, preserving directory structure (including handoff_payload_26864/app, regressions/numeric, and all manifests). This upload makes NO direct edits to live app/src or app/version.properties: the guarded Actions script reconstructs its runtime candidate from successful 26863 authority and exact replacements.
Commit message: 26864 stage 1: sealed RAWR source and guarded handoff

STAGE 2 — Upload ONLY STAGE_2/.github/workflows/build-26864-iris-rawr.yml to .github/workflows/, then commit.
Commit message: 26864 stage 2: install guarded RAWR Actions workflow

STAGE 3 — Upload ONLY STAGE_3/TRIGGER_26864.txt to repository root, then commit and push to launch the intended Actions workflow.
Commit message: 26864 stage 3: trigger guarded RAWR build

The three stages may be pushed together ONLY after all three commits are created and the runner has the sealed package, workflow and trigger. Ensure only the intended 26864 workflow runs. Actions must generate the exactly one APK and all required prebuild/postbuild proofs. Do not claim BUILD-PROVEN before Actions shows SUCCESS and its artifact/compiler reports have been inspected.

Candidate: 1,991 files, exactly 161 changes against 26863 (150 additions, 11 edits, 0 deletions; version 0.9726864 / 26864). The pinned vendor shaders are preserved as shipped upstream; narrowly audited two-slot coordinator source adaptations are source-locked separately.

COMPILER DISCLOSURE: Shader/GLES/SPIR-V, full Kotlin/Java and Android NDK/assemble have NOT run in this preparation environment. Stage-1 package/patched candidate/semantic/host numerical gates have run. Actions compilation is mandatory and may reveal issues requiring corrective handoff. No guarantee of successful APK or device behavior is made.

STRICT SECURITY/PROOF: The script fails closed if branch, prior artifact identity/hash, prior compiler proof, source manifests, 161-path allowlist, 17-stage order, inherited compiler commands, native source lock, real pinned shader compiler, SPIRV-Tools, language/NDK compilers, patch replay, prebuild proof, exactly-one APK, postbuild invariance, or final clean-extract replay fails.

No backup, ChatGPT source commit/push, or APK push is included. Device testing of full-frame tint and JPEG saving is still required after successful Actions.

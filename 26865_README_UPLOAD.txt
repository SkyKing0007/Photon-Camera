26865 — SHORT vscode.dev handoff (NO backup branch)
Branch: experimental-clean-photon-rebuild
Runtime authority: SUCCESS 26864 run 39716184395, commit a14f3b6f11bffce01ce273fdfd898203d665dc28, artifact 12399841223.

1. Upload the CONTENTS of STAGE_1/ at repository root, preserving paths (2 app replacement files plus guarded script/proofs). Commit "26865 stage 1: verified B native LSC handoff".
2. Upload STAGE_2/.github/workflows/build-26865-iris-lsc.yml to .github/workflows. Commit "26865 stage 2: inherit successful 26864 guarded Actions".
3. Upload STAGE_3/TRIGGER_26865.txt at repository root. Commit "26865 stage 3: trigger guarded build".
Push all 3 commits together to experimental-clean-photon-rebuild. Never upload any APK.
The old build-26864 workflow listens only for TRIGGER_26864.txt; 26865's new workflow listens only for TRIGGER_26865.txt.
GitHub Actions is authoritative for GLSL/SPIR-V, Kotlin, Java, both NDK architectures, PRE-BUILD SAFETY PROOF, full assemble, and final APK invariant.
No ChatGPT source push, no backup, no APK was created.

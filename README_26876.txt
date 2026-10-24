PHOTON 26876 — SINGLE-ZIP / THREE-COMMIT GUARDED VSCODE.DEV HANDOFF

STATUS: PREPARED SOURCE AND PATCH PROOF; ANDROID REAL COMPILERS/NDK/SDK/DEVICE NOT RUN LOCALLY.
THIS IS NOT A BUILD-PROVEN APK. GITHUB ACTIONS MAY FAIL A REAL COMPILER GATE.

BRANCH: experimental-clean-photon-rebuild. NO BACKUP BRANCH. NO CHATGPT COMMIT OR PUSH.
RUNTIME: Successful 26875 Actions 40054980042, commit 23c3f94222e6585690aee866277ed2ca82cca61c, artifact 12544774681; outer ZIP SHA256 afd2efb8b8512bdff721809d9a15898821c1cdd2f37c9542a8101afe528997f7.
EXACT 26875 COMPILED CANDIDATE TAR SHA256 41207fa5316469d9cd9a0f6d6844671db01ea05091322f749a49ab0a5ac5b775. 1,997 exact files.
MECHANICS: exact successful generated 26875 runner SHA256 b6c6f1db9f9910a0bff2175af756e3e92896d33eb6a82776de746eda645fa7a1, inherited 17 guarded stage order and same Kotlin/Java/NDK/assemble calls. No reordering of handoff functions.
RUNTIME CHANGED ALLOWLIST: 3 files:
app/src/main/cpp/motionv2_jpeg444_jni.cpp
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
app/version.properties
SOURCE PROTECTED: 1,994 files byte-identical. Full-index forward/rollback patch proof at 7/12/40, fuzz=0.

GOAL: B Super Res ON only. Single native true50MP Wronski burst merge (no duplicate HDRq), derived 1x tone and sensor clip guides, physical LONG luminance only, parallel same-math B-only 50MP sensor clip correction, B-owned GLES3.1 GPU final renderer supporting DCP, watermark, P3 and HDR gain; existing A renderer unchanged. No 24MP mode, no frame count change, no A fallback.
CAUTION: Actual GPU shader compile, Android Kotlin/Java/NDK compile, device image-quality/color/highlight/performance are still NOT RUN and may falsify intended equivalence. The new guide is derived from Wronski output, not guaranteed pixel-identical to old HDRq guide. No measured 10-15-second claim.

VSCODE.DEV THREE-COMMIT SEQUENCE (upload/replace all listed paths exactly):
1. Upload every ZIP path EXCEPT .github/workflows/build-26876-iris-rawr.yml and TRIGGER_26876.txt. Commit: 26876 Stage 1: Add guarded B-only 50MP Wronski performance candidate and proofs. DO NOT PUSH.
2. Upload ONLY .github/workflows/build-26876-iris-rawr.yml. Commit: 26876 Stage 2: Add inherited successful 26875 guarded build workflow. DO NOT PUSH.
3. Upload ONLY TRIGGER_26876.txt. Commit: 26876 Stage 3: Trigger strict B true50MP Wronski build. PUSH ONCE.

DO NOT upload APKs or local generated build_26876_iris_rawr.sh. Actions runs real compilers, full assemble and clean-extract checks. Any failed compiler is an enforced BLOCKER to an APK, not a reason to reduce validation.

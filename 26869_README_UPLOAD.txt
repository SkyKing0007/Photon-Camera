PHOTON 26869 R3 — PREPARED / UPLOAD READY for vscode.dev, branch experimental-clean-photon-rebuild.
Runtime authority: successful 26868 Actions 39863379652, commit 7800265e6a5909ddea770c93cfeaed244c489247; exact successful compiled-candidate 1992-file TAR sha256 7ac33dfa920060b97465e6a1815573f56cdaf5548e444abd20d9366063ec5596.
This fixes ONLY Actions 39897292954 AAPT2 invalid app:max on two AndroidX SeekBarPreference controls (use android:max=100). Exact negative fixture added to permanent 26869 regression. Other 11 runtime payloads, existing 26869 build script and workflow unchanged. Candidate-first allowlist remains exactly 12; protected 1984 unchanged; exact 17-stage successful 26868 mechanics retained.
S1: upload/replace every file beneath S1/ at its exact repository-relative path, commit and push.
S2: EMPTY, SKIP upload and commit because workflow YAML is byte-identical to committed R2.
S3: upload/replace TRIGGER_26869.txt ONLY AFTER S1, commit and push to trigger Actions exactly once.
Do not upload S1/S2/S3 folder names. Do not place handoff_payload_26869/app into live app/src directly. No APK included. No backup, no source push made here. Real Android AAPT2, pinned GLSL, Kotlin/Java/NDK/full assemble NOT RUN locally; GitHub Actions decides build success.

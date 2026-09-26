PHOTON 26711 — Locked Reference Lifecycle

Runtime authority: successful 26710 commit 38db48d5762d1ea1f44601b2b404271eb29e855b, Actions run 36251104057, artifact 10909395982.
No backup created. Runtime allowlist: exactly 3 files.

Two-step vscode.dev upload:
1) Upload every path in 26711_UPLOAD_PATHS.txt EXCEPT .github/workflows/build-26711-locked-reference-lifecycle.yml, then commit.
2) Upload only .github/workflows/build-26711-locked-reference-lifecycle.yml, then commit to activate Actions.

26711 preserves the successful 26710 Actions stage order. Before Actions success it is prepared/upload-ready only.

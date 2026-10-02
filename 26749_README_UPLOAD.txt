PHOTON 26749 — BOUNDED PROPRIETARY RESOLVESABRE CFA REFERENCE

Upload/extract this handoff into the repository root on branch experimental-clean-photon-rebuild, preserving paths and replacing same-path 26749 files if prompted. Do not copy any APK.

This handoff does NOT replace live repository app/src directly. The four intended runtime replacement files are sealed under handoff_payload_26749/. GitHub Actions reconstructs the exact successful 26748 compiled-candidate authority, overlays only those four files candidate-first, proves the candidate/patches/invariants, then installs the frozen candidate for real compilers and full assemble.

After upload in vscode.dev:
1. Confirm only the files listed in 26749_UPLOAD_PATHS.txt are new/changed for this handoff.
2. Commit those handoff files to experimental-clean-photon-rebuild.
3. Push once. The path-scoped workflow Build 26749 Bounded ResolveSabre CFA Reference should run.
4. Final authority exists only if that Actions run succeeds. Do not treat this local handoff as build-proven.

No backup branch was created. No source/APK was committed or pushed by ChatGPT.

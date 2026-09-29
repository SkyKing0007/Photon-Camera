PHOTON 26733 — HIGHLIGHT-SAFE COLOR INTEGRITY

Use branch: experimental-clean-photon-rebuild
Do not upload this ZIP itself. Extract it and preserve every included path.

STAGE 1: upload/replace every file in this handoff EXCEPT:
.github/workflows/build-26733-highlight-safe-color-integrity.yml
Commit message:
26733: prepare highlight-safe color integrity

STAGE 2: upload only:
.github/workflows/build-26733-highlight-safe-color-integrity.yml
Commit message:
26733: activate highlight-safe color integrity

The Stage 2 workflow is the single intended Actions trigger.
26733 is prepared/upload-ready until that Actions run passes all real compiler/build/post-build gates.

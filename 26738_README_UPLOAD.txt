PHOTON 26738 — WRONSKI RAW RGB + UNIVERSAL CFA + SEAM INTEGRITY

Use branch: experimental-clean-photon-rebuild
Do not upload this ZIP itself. Extract it and preserve every included path.

STAGE 1: upload/replace every file in this handoff EXCEPT:
.github/workflows/build-26738-wronski-raw-rgb-seam-integrity.yml
Commit message:
26738: prepare Wronski RAW RGB seam integrity

STAGE 2: upload only:
.github/workflows/build-26738-wronski-raw-rgb-seam-integrity.yml
Commit message:
26738: activate Wronski RAW RGB seam integrity

The Stage 2 workflow is the single intended Actions trigger for 26738.
26738 is prepared/upload-ready until that Actions run passes all real compiler/build/post-build gates.

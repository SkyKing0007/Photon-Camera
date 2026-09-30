PHOTON 26736 — WRONSKI PHASE INTEGRITY

Use branch: experimental-clean-photon-rebuild
Do not upload this ZIP itself. Extract it and preserve every included path.

STAGE 1: upload/replace every file in this handoff EXCEPT:
.github/workflows/build-26736-wronski-phase-integrity.yml
Commit message:
26736: prepare Wronski phase integrity

STAGE 2: upload only:
.github/workflows/build-26736-wronski-phase-integrity.yml
Commit message:
26736: activate Wronski phase integrity

The Stage 2 workflow is the single intended Actions trigger for 26736.
26736 is prepared/upload-ready until that Actions run passes all real compiler/build/post-build gates.

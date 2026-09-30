PHOTON 26737 — WRONSKI PHASE + CHROMA INTEGRITY

Use branch: experimental-clean-photon-rebuild
Do not upload this ZIP itself. Extract it and preserve every included path.

STAGE 1: upload/replace every file in this handoff EXCEPT:
.github/workflows/build-26737-wronski-phase-chroma-integrity.yml
Commit message:
26737: prepare Wronski phase chroma integrity

STAGE 2: upload only:
.github/workflows/build-26737-wronski-phase-chroma-integrity.yml
Commit message:
26737: activate Wronski phase chroma integrity

The Stage 2 workflow is the single intended Actions trigger for 26737.
26737 is prepared/upload-ready until that Actions run passes all real compiler/build/post-build gates.

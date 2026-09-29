PHOTON 26735 — NEUTRAL CHROMA / DIGITAL LUMA / NORMAL RETRY

Use branch: experimental-clean-photon-rebuild
Do not upload this ZIP itself. Extract it and preserve every included path.

STAGE 1: upload/replace every file in this handoff EXCEPT:
.github/workflows/build-26735-neutral-chroma-digital-luma-retry.yml
Commit message:
26735: prepare neutral chroma digital luma retry

STAGE 2: upload only:
.github/workflows/build-26735-neutral-chroma-digital-luma-retry.yml
Commit message:
26735: activate neutral chroma digital luma retry

The Stage 2 workflow is the single intended Actions trigger for 26735.
26735 is prepared/upload-ready until that Actions run passes all real compiler/build/post-build gates.

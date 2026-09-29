PHOTON 26732 — upload instructions

Target branch: experimental-clean-photon-rebuild
Do not upload this ZIP itself. Extract it and preserve all paths.
No backup branch is required or created.

STAGE 1: upload/replace every file from this handoff EXCEPT:
.github/workflows/build-26732-chroma-integrity-high-zoom.yml
Commit message:
26732: prepare chroma integrity and high zoom hardening

STAGE 2: upload only:
.github/workflows/build-26732-chroma-integrity-high-zoom.yml
Commit message:
26732: activate chroma integrity and high zoom hardening

Only the new 26732 workflow is path-triggered by these files. GitHub Actions performs the authoritative real compiler/build proof.
26732 is prepared/upload-ready, not build-proven, until that workflow succeeds.

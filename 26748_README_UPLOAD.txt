PHOTON 26748 — TEMPORAL RAW CHROMA PROVENANCE

Do NOT upload the ZIP itself. Extract it and preserve paths.
No backup branch is required or requested.

STAGE 1
Upload/replace everything in this handoff EXCEPT:
.github/workflows/build-26748-temporal-raw-chroma-provenance.yml

Commit message:
26748: prepare temporal RAW chroma provenance

Push and confirm no 26748 workflow starts yet.

STAGE 2
Upload only:
.github/workflows/build-26748-temporal-raw-chroma-provenance.yml

Commit message:
26748: activate temporal RAW chroma provenance

Push. The 26748 Actions workflow is the authoritative real compiler/build proof.

Expected runtime changed files are exactly the four paths in 26748_RUNTIME_CHANGED_PATHS.txt.
Do not modify any payload, validator, manifest, build script or workflow after extraction.

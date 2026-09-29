PHOTON 26734 R1 — VERIFICATION REPAIR, RUNTIME UNCHANGED

Use branch: experimental-clean-photon-rebuild
Do not upload this ZIP itself. Extract it and preserve every included path.

IMPORTANT: R1 filenames are intentionally distinct so the failed 26734 workflow does not trigger during Stage 1.

STAGE 1: upload/replace every file in this handoff EXCEPT:
.github/workflows/build-26734r1-all-digital-zoom-achromatic-sr.yml
Commit message:
26734 R1: repair inherited shader verification

STAGE 2: upload only:
.github/workflows/build-26734r1-all-digital-zoom-achromatic-sr.yml
Commit message:
26734 R1: activate repaired verification build

The Stage 2 R1 workflow is the single intended Actions trigger.
26734 R1 is prepared/upload-ready until that Actions run passes all real compiler/build/post-build gates.

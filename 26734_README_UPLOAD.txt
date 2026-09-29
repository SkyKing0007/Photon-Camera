PHOTON 26734 — ALL-DIGITAL-ZOOM ACHROMATIC + SR INTEGRITY

Use branch: experimental-clean-photon-rebuild
No backup branch is required or created.
Do not upload this ZIP itself. Extract it and preserve every included path.

STAGE 1: upload/replace every file in this handoff EXCEPT:
.github/workflows/build-26734-all-digital-zoom-achromatic-sr.yml

Commit message:
26734: prepare all-digital zoom achromatic sr integrity

STAGE 2: upload only:
.github/workflows/build-26734-all-digital-zoom-achromatic-sr.yml

Commit message:
26734: activate all-digital zoom achromatic sr integrity

The Stage 2 workflow is the single intended Actions trigger.
26734 is prepared/upload-ready until that Actions run passes pinned glslang 16.5.0, real Kotlin/Java, both NDK ABIs, full :app:assembleDebug, one-APK proof, post-build invariance, deterministic patches and final candidate export.

PHOTON 26750 — SOURCE-PROVEN FINE COLOR FROM CLEAN 26728 RUNTIME

Use branch: experimental-clean-photon-rebuild
Do not upload this ZIP itself. Extract it and preserve every included path.
No backup branch.

STAGE 1
Upload/replace every file listed in 26750_UPLOAD_PATHS.txt EXCEPT:
.github/workflows/build-26750-source-proven-fine-color.yml
Commit message:
26750: prepare source-proven fine color

STAGE 2
Upload only:
.github/workflows/build-26750-source-proven-fine-color.yml
Commit message:
26750: activate source-proven fine color

The Stage 2 workflow is the single intended Actions trigger for 26750.
26750 is prepared/upload-ready until that Actions run passes pinned real GLSL, Kotlin, Java, both NDK ABIs, full assemble, one-APK proof and post-build invariance.

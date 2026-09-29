PHOTON 26730 — Validity-Owned Chroma Containment
Upload extracted handoff contents to the root of experimental-clean-photon-rebuild; do not upload this ZIP itself.
Normal two-stage commit flow:
1) upload/replace every handoff file except .github/workflows/build-26730-validity-owned-chroma-containment.yml
   commit: 26730: prepare validity-owned chroma containment
2) upload the workflow file alone
   commit: 26730: activate validity-owned chroma containment
Do not upload APKs. Do not modify live app/src manually; Actions reconstructs the exact candidate from successful 26729 authority plus the sealed 2-file payload.
26730 is prepared/upload-ready only until GitHub Actions passes pinned GLSL, Kotlin, Java, both NDK ABIs, full assemble, one-APK proof, and post-build invariance.

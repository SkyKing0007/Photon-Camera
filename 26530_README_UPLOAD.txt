Photon Camera 26530 V1.2 — upload/build instructions
=====================================================

IMPORTANT
---------
This V1.2 replaces the failed 26530 V1.1 handoff infrastructure only.
Do NOT advance the build number. Target remains 0.9726530 / 26530.
The runtime SR/luma forward patch is byte-identical to V1.1.
No backup branch is required for this incremental correction.

Why V1.1 stopped
----------------
The 26530-only GLSL preflight failed before Gradle because its extractor preserved the
leading newline of a Kotlin triple-quoted shader. Khronos requires #version to be the
first shader token. Successful 26529 already handled this correctly by stripping Kotlin
formatting whitespace. V1.2 restores that procedure and also restores the inherited
pre/post-build shader/native/DNG gates that V1.1 omitted.

Upload/replace every file in this ZIP at its shown repository-relative path on:
  experimental-clean-photon-rebuild

The old V1.1 file 26530_BASE_26529_ARTIFACT.txt may remain in the repository; V1.2 does
not use it as authority. V1.2 uses 26530_BASE_26529_HEAD.txt and exact successful-26529
workflow/artifact identity.

Expected workflow
-----------------
.github/workflows/build-26530-gcam-luma-motion-safe-superres.yml
Workflow display name: Build 26530 V1.2 GCam Luma Motion Safe SuperRes

Expected artifact
-----------------
photon-26530-gcam-luma-motion-safe-superres-v1-2

Expected APK
------------
IrisCamera-0.9726530-26530-gcam-luma-motion-safe-superres-debug.apk

Runtime patch identity retained from V1.1
-----------------------------------------
26530_RUNTIME_DELTA_FROM_SUCCESSFUL_26529.patch
SHA-256: b971932bf71622d8966f45bb1a2b93297a0b0e1ecd538c5d09990cafb1b4f6a3

26530_RUNTIME_ROLLBACK_TO_SUCCESSFUL_26529.patch
SHA-256: b509cc5ad9ba16a3d8df4f44f98bc193efa979907146d759017d75682c35a314

Strict predecessor
------------------
Successful 26529 V3 handoff HEAD:
  dae32a760a31a7f9f8d80c612e8b58be4519e637
Workflow:
  build-26529-manual-30x-iris-spatial-rgb-v3.yml
Artifact:
  photon-26529-manual-30x-iris-spatial-rgb-v3
Candidate tar SHA-256:
  1c5662b8c356bc84ee98431d4d020e6e26fd8b003dc275476f81321954950b92
Candidate manifest SHA-256:
  b6bb4360ccb00af8bf353bb6be0bbacfde84ee1091268deff7c0eb3f7f851c21

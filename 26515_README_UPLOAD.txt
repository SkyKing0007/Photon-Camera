26515 V4 — DIRECT TESTED-26514 SOURCE -> SHORT/BENTO EXPOSURE-DOMAIN FIX
=======================================================================

IMPORTANT
---------
This v4 supersedes v1/v2/v3. Do not use the earlier 26515 constructor packages.

Why v4 exists
-------------
The earlier 26515 handoffs recreated 26514 through older 26512/26513 constructors. That was
reproducible, but it violated the agreed working rule: when the previous tested build is good,
continue directly from that previous build rather than rebuilding from an older checkpoint.

v4 fixes the BUILD LINEAGE, not the 26515 image-math change.

Direct baseline used by v4
--------------------------
1. Exact successful 26514 handoff/fix HEAD:
   e9855a3af7a79801a762ec3f99b441474926f009
2. Exact existing backup:
   backup-26514-before-26515-short-bento-fix-20260820
3. The workflow locates the successful 26514 GitHub Actions run at that exact HEAD.
4. It downloads artifact: photon-26514-iris-profiles-controls
5. It extracts and manifest-verifies the ACTUAL 26514_candidate_app_source.tar.gz emitted by
   that successful build.
6. That tested source snapshot is the sole Iris/Photon runtime base for 26515.
7. No 26512 or 26513 runtime constructor is executed or referenced by the v4 builder.

The source snapshot intentionally omitted the large JPEG/UHDR vendor copies. v4 rehydrates ONLY
those exact vendor trees from pinned bjzhou commit 09c76e57e8f01a5a8fc536ab41fc80ba642d4042
and verifies them with the existing 26507_BJZHOU_NATIVE_DEPENDENCIES.sha256 manifest. This does not
reconstruct any older Iris runtime source.

26515 runtime change (unchanged from v3)
----------------------------------------
Accepted Short/Bento recovery remains enabled. MGC BaselineExposure is separated into:
- MGC source-domain restoration gain, consumed after MGC full-resolution denoise in the existing
  DisplayExposure linear pass; and
- Photon's normal reference display gain, which alone owns MotionV2Render sceneWhite/highlight
  shoulder authority.

The linear pixel product remains equivalent; the incorrect Short-dependent sceneWhite authority is
removed. UHDR retains the prior Short-dependent gain-map capacity.

Frozen in this build
--------------------
MGC/Bento threshold and acceptance logic, MGC alignment/rejection, Short capture exposure, Long,
Spatial RGB math, 26513 1.10/0.40 Spatial detail tuning, MGC noise propagation, luma/chroma denoise
controls, Iris tone controls, color transform, display shader, render shader, UHDR shader, JPEG 4:4:4,
and Camera2/AE capture authority are not changed by 26515.

Upload instructions
-------------------
Extract this ZIP and upload/replace all 8 files on experimental-clean-photon-rebuild, preserving
.github/workflows/build-26515-short-bento-domain.yml.
Do NOT upload the ZIP itself.
Do NOT create another backup; the existing exact 26514 backup is the correct backup for this source
modification cycle.

Suggested commit message:
26515: build directly from tested 26514 source

Expected APK:
IrisCamera-0.9726515-26515-short-bento-domain-fix-debug.apk

The successful proof bundle also emits 26515_candidate_app_source.tar.gz and its manifest so the
NEXT incremental build can again work directly from the successful previous build.

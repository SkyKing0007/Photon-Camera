PHOTON / IRIS 26672 R1 — HEIC GOOGLE-V2 PUBLICATION + CAMERA UI POLISH

STATUS AT HANDOFF CREATION
  Prepared/upload-ready only. Real GLSL/Kotlin/Java/NDK/full Android assemble proof is Actions-only.
  Final successful Actions authority remains 26671 until the 26672 workflow succeeds.
  No backup branch was created, by explicit request.

RUNTIME AUTHORITY
  Successful 26671 commit: 4d98d23e43945c4384f862ce6ffd56cec02e9796
  Actions run: 35457074884
  Artifact: 10588329184 photon-26671-r1-highlight-separation-histogram
  Artifact SHA256: ccf8d8c758f3a07f7f6e14e2ad3bb51b794f66685c7b01145c505bfc9d03a7d8
  Compiled candidate TAR SHA256: 566dd4e51d68f556f71147ac28c721cdbba9ec8190ce1661856e2095a3dfbb69
  Exact authority universe: 1725 files.

VERIFICATION-MECHANICS AUTHORITY
  Successful 26671 build script blob: 145c7d98812ffc0ad4371574812d06fe17aa079e
  Successful 26671 workflow blob:     777126a3f3cc9b44e9a64325837725a99e3dc42c
  Functional mechanics delta: ZERO.

RUNTIME SCOPE — EXACTLY 4 PATHS
  MODIFIED app/src/main/cpp/iris_heic_jni.cpp
  MODIFIED app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java
  ADDED    app/src/main/res/drawable-anydpi/iris_flip_arrows.xml
  MODIFIED app/version.properties
  No runtime deletions.

26671 HARDLOCK
  Everything outside those four paths is byte-identical to the successful 26671 compiled candidate.
  This includes JPEG/JPEG-R, render.glsl, gainmap.glsl, 26671 highlight separation, SHORT/NORMAL/LONG,
  Motion/Sabre, temporal rejection/alignment, denoise/noise, Local-Laplacian, viewfinder/Camera2,
  histogram behavior/pill, manual touch ownership, DNG and all unrelated UI.

HEIC ULTRA HDR TARGET
  The normal 1x HEIC path continues to consume the exact completed Iris SDR base + existing Iris gain
  map + existing ISO 21496 metadata. It does NOT recompute gain values or HDR rendering.
  Publication is corrected toward Google libultrahdr v2.0.0 HEIF semantics:
    - Display-P3 base ICC plus NCLX, with BT.709 transfer signalling / BT.601 matrix / full range;
    - monochrome gain-map item with unspecified primaries/transfer, BT.601 matrix, full range;
    - tmap color properties describe Iris' extended-linear Display-P3 HDR intent;
    - gain pixels and min/max/gamma/offset/capacity/use-base metadata remain exact upstream values.
  The Super-Res HEIC native path is byte-identical to successful 26671.
  This build prepares the publication correction; actual Google Photos brightness-pop parity remains a
  Xiaomi/Android 16 device-runtime verification and is NOT claimed before testing.

MANUAL MODE POSITION
  The successful 26671 on-screen position, including its existing +12px translation, is the baseline.
  The slider rectangle remains at its exact successful-26671 visual Y. Only the Focus/Shutter/ISO/EV
  row moves, and its center is placed halfway between the current slider bottom and the upper point of
  the chevron after opening. Inflated pixel geometry is used so the relation scales with density/device.

FRONT CAMERA SWITCH ICON
  The existing switch button layout is byte-identical: same 48dp circle, position, padding, tint,
  touch target and behavior. The old nodpi bitmap remains untouched as fallback. A drawable-anydpi
  vector with the same iris_flip_arrows resource name provides clean thin rounded two-arrow artwork
  with approximately the same visible 128x128 footprint / ~36dp apparent size on the Xiaomi target.

MANIFEST / PATCH PROOF
  1725 base / 1726 candidate / 1722 protected / 806 native-protected / 778 vendor / 7 DNG.
  257 standalone shaders and all 12 runtime-expanded variants are unchanged from successful 26671.
  Deterministic full-index forward/rollback patches must match at core.abbrev 7/12/40, fuzz=0.
  Forward patch creates exactly one vector file; rollback removes it exactly.

UPLOAD
  Extract this handoff at repository root in vscode.dev on experimental-clean-photon-rebuild.
  Upload/replace the complete handoff set only; do not manually copy payload files into live app/src.
  Source Control must match R1_26672_UPLOAD_PATHS.txt exactly before commit.

SUGGESTED COMMIT MESSAGE
  26672 R1: HEIC HDR publication and camera UI polish

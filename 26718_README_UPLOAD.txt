PHOTON 26718 R1 — KOTLIN COMPILER REPAIR

Runtime authority remains successful 26717 commit cc158368bf8bd1303a164d85457e396840ddb16e; Actions run 36286961631; artifact 10921015621; artifact SHA-256 6e8741ee0c49826bdf73faeaa2acb049092a73987bbcb630da9a31f294ef8a77; candidate TAR SHA-256 8bae03a6a74fd71b048511b2c19c0c1e65ae4ab3853b7611099446500b24d759.
Verification-mechanics authority: exact successful 26717 sequence. No backup. No stage reordering. Workflow/build script are unchanged from the failed 26718 handoff and preserve the successful-26717 compiler/build order.

Repair only:
  * import the existing com.particlesdevs.photoncamera.util.MotionTrace API in PhotonMotionMgc1271Bridge.kt.
  * match ImageFrame using mgcBase.motionV2FrameNumber instead of the nonexistent mgcBase.frameNumber.
  * add permanent packaged regression assertions for the exact three Kotlin compiler failures from Actions run 36330256385.

The 20x high-zoom architecture, 12-file runtime allowlist, shaders, native Sabre/VGN RGB ownership, all-NORMAL evidence policy, SDR/UHDR shared detail geometry, DNG/native/vendor/capture/logging behavior and version 0.9726718/26718 are otherwise unchanged.

UPLOAD: the 26718 workflow is already active on the branch. Replace the files from this ZIP in one commit; no second workflow-activation commit is needed.
Suggested commit: 26718 R1: repair Kotlin compiler references

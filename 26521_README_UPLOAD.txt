26521 — Sibling A/B: 26520 stacked DNG + Iris-owned RGB rewrite

Base: 9b59a27235747733bacdde68bf6a888ebffefa18
Required dedicated backup: backup-26519-before-26521-iris-rgb-rewrite\nIt must point to the same exact 26519 commit.

26520 and 26521 are siblings from the same successful 26519 source artifact.

26520:
- explicit one-normal-frame fix
- same shutter-frozen normal batch for JPEG/DNG
- normal-only Wronski Bayer stacked DNG
- released c4ff Spatial RGB remains JPEG RGB owner

26521:
- imports the exact same 26520 one-frame + DNG transform
- Wronski alignment/rejection is byte-frozen
- disables active calls to the old per-frame Spatial RGB helpers
- replaces final JPEG RGB reconstruction with a new Iris shader:
  motionv2/iris_fused_bayer_rgb_26521

New Iris RGB math:
- measured green is preserved at green CFA sites
- missing green uses horizontal/vertical edge evidence
- red/blue use local color-minus-green residual interpolation
- extended-linear values above 1.0 are preserved
- Camera2 lens shading is applied after RGB reconstruction

The new shader contains no c4ff opponent-color accumulator, covariance RGB kernel,
Spatial-RGB thresholds/constants, GlesMgc calls, or mfsr_spatial_rgb shader code.

Short/Long/Bento remain separate JPEG HDR/Bayer evidence. The DNG branch is already
frozen from the normal-only Bayer accumulator before JPEG RGB reconstruction.

Important:
This is an independently authored ACTIVE-PATH replacement, not a legal certification
of clean-room development, because the project has previously inspected bjzhou source.
Dormant old Spatial-RGB helper source is retained only for rollback/audit and validators
forbid MotionV2CfaReconstruction.Run() from calling it. If the A/B test succeeds, a
follow-up source-tree cleanup can physically remove those dormant files/assets.

Artifact: photon-26521-iris-rgb-rewrite-v1
APK: IrisCamera-0.9726521-26521-iris-rgb-rewrite-debug.apk

V3 exact-26519 procedure correction
-----------------------------------
- The successful 26519 V2 Actions artifact is the sole runtime source authority.
- Both the shared 26520 transform and the 26521 RGB transform are proven in memory against that exact artifact before candidate writes.
- Repository app/src is never substituted for the tested 26519 artifact.
- No new runtime architecture change versus the original 26521 sibling experiment.

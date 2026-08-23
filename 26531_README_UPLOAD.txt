26531 V1.1 latest-MGC Spatial / zero-luma / corrected-FOV handoff

V1.1 infrastructure correction: removes accidental backup-branch creation from the first 26531 handoff. Runtime forward/rollback patches are byte-identical; build/version remain 0.9726531 / 26531.

Upload the CONTENTS of this ZIP to the root of branch:
  experimental-clean-photon-rebuild

Do not place the files inside an extra folder.
Do not modify app/src manually.
Do not push to dev.

The new workflow is:
  Build 26531 Latest MGC Spatial Zero Luma FOV

Expected Actions artifact:
  photon-26531-latest-mgc-spatial-zero-luma-fov

Expected APK:
  IrisCamera-0.9726531-26531-latest-mgc-spatial-zero-luma-fov-debug.apk

The workflow does not use repository app/src as runtime authority. It locates the successful 26530 V1.2 workflow at exact HEAD 8e847de9841b5ed3522970a1106f2b53cb3f7eb1, downloads its exact candidate-source artifact, verifies the tar/manifest hashes, regenerates the certified forward+rollback patches before candidate writes, validates the exact seven-file runtime scope, runs all new and inherited shader/native/DNG preflights, prints PRE-BUILD SAFETY PROOF PASSED, then increments to 0.9726531/26531 and builds in that same guarded block.

Backup policy:
No backup branch is created or required. The workflow remains on experimental-clean-photon-rebuild and uses the exact successful 26530 V1.2 candidate artifact plus certified forward/rollback patches for recovery.

Sabre handling:
Sabre source is allowed to exist, so old blanket grep gates cannot fail merely because the word SABRE is present. The validator instead fails if the active Motion bridge selects Sabre, if the active denoise pass becomes SABRE_DEFAULT, or if any protected Sabre owner changes.

Primary on-device checks after a successful build:
1. 4.1x optical baseline and ~8.2x versus the same GCam framing.
2. 4.1x lens at local 30x (~123x displayed) versus GCam 120x: FOV should match closely again.
3. Inspect 400–800%: fine luma texture/grain should survive better with effective MGC luma=0 while chroma remains controlled.
4. Moving people/cars/leaves/hair/branches at >=8x: no new clumping, zippering, ghosting, or colored blocks.
5. Harsh highlights/text edges: no pink/magenta/green line/dot/block recurrence.
6. Keep DNG and logs; telemetry should show requestedLuma, effectiveMgcLuma=0.0, chroma, srScale, requestedLocalZoom, finalFovZoom, finalRenderLocalZoom, pass=SPATIAL_DEFAULT, sabreSelected=false.

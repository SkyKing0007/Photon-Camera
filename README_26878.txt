PHOTON CAMERA / IRIS 26878 — VERIFIED ROOT-ONLY VSCODE.DEV HANDOFF

STATUS: PREPARED / UPLOAD-READY FOR GITHUB ACTIONS PROOF; NOT BUILD-PROVEN.
NO 26878 APK, Kotlin/Java compilation, formal PRE-BUILD SAFETY PROOF, or
Android :app:assembleDebug has been run in this development session.

AUTHORITIES
  Branch: experimental-clean-photon-rebuild; verified prior successful HEAD
      42bbcd628f80c1bd9a0a80e7b1d4b7fee8fabf85
  Successful build 26877: Actions 40137408646 / artifact 12577917317
  Exact compiled artifact SHA256:
      f9777891ec0a6476e4bbd3c56b755b050e15bc5270309eb97f1463b015768a98
  Exact 2001-file compiled candidate TAR SHA256:
      375f8a4a4f79e16d4b47a3191525b83b811e17406fdf6cae5d1fb53e61ee84b4
  Last successful generated verification runner SHA256:
      bbda162004a0aa4b262a3df3547c47601df5ccb93cfb966a2dbd0a78a09e7dff

MANUAL VSCODE.DEV DELIVERY — USE ONE COMMIT AND ONE PUSH
1. Open SkyKing0007/Photon-Camera at experimental-clean-photon-rebuild.
2. Extract this ZIP locally. Replace/upload all root-level files into the
   repository ROOT, NOT into app/src. The sole nested file is the workflow:
   .github/workflows/build-26878-iris-rawr.yml — preserve that exact path.
3. Do not upload an APK, do not modify dev, and do not add a backup branch.
4. Commit the intended files once and push once. The ONLY workflow trigger
   added/changed for 26878 is TRIGGER_26878.txt. Do not manually run a
   second historical or workflow_dispatch build concurrently.
5. The workflow first hashes every file, stages the five root source files
   into handoff_payload_26878/, and migrates the ORIGINAL successful 26877
   validator root->regressions/ using its exact pinned SHA256. It then
   reproduces the exact prior 26877 runner and generates the 26878 successor.
6. GitHub Actions must prove the real pinned GLSL, Kotlin, Java, NDK/ABIs,
   PRE-BUILD SAFETY PROOF, full assemble, one APK, post-build invariance,
   and clean-extract replay. Failed Actions = NOT SUCCESSFUL 26878.

RUNTIME SCOPE (2001 FILES TOTAL, EXACTLY FIVE CHANGED)
  FrameGeometrySnapshot.kt: Spektra-only full-active RAW preview geometry
  RawVulkanPreviewController.kt: Spektra-only physical viewport surface refresh
  PhotonMotionMgc1271Bridge.kt: B Super Res-only 1x GPU guide failure repair
  ImageSaver.java: B Super Res-only EXIF-complete JPEG publication
  app/version.properties: 0.9726878 / 26878
  All other 1996 compiled runtime files, including 26877 A/Motion/Night/LONG,
  protected native/GLSL/DNG/vendor and the original Wronski 2x producer,
  are byte-identical.

LIMITATIONS
The original late five-file draft was lost; this is a new authority-seeded
reconstruction. It reuses the historically proven B bridge and ImageSaver
bytes but reconstructs the two narrow Spektra Kotlin changes from the latest
saved specifications. A Spektra-only crop/surface correction is NOT a complete
UnspektrAwesome 1.2.5 port. Actual viewfinder FOV, native surface refresh,
50MP B-only JPEG save and HEIC/UHDR behavior remain device-test dependent.

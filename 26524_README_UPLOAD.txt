26524 CONTINUOUS ZOOM — VSCODE.DEV / GITHUB ACTIONS UPLOAD
============================================================

IMPORTANT
- Correct branch: experimental-clean-photon-rebuild
- Do NOT use experimental-effective-stack.
- Backup already created and verified:
  backup-26523-v1.1-before-26524-zoom

WHAT TO UPLOAD
Upload the files from this ZIP to the SAME relative paths in
experimental-clean-photon-rebuild.

Repository root:
- apply_26524_continuous_zoom.py
- validate_26524_continuous_zoom.py
- preflight_26524_zoom_shaders.py
- build_26524_continuous_zoom.sh
- 26524_BASE_26523_HEAD.txt
- 26524_SCOPE_PROVENANCE.txt
- 26524_README_UPLOAD.txt
- 26524_HANDOFF_HASHES.sha256

Workflow path:
- .github/workflows/build-26524-continuous-zoom.yml

DO NOT EDIT
- Do not edit app/src manually.
- Do not change app/version.properties manually.
- Do not upload an APK to the repository.

EXPECTED ACTION
Build 26524 Continuous Zoom

EXPECTED SUCCESS ARTIFACT
photon-26524-continuous-zoom-v1

IMPORTANT MODE SCOPE
The new continuous pinch zoom is intentionally authoritative in MOTION mode first.
PHOTO/NIGHT/VIDEO keep their existing optical lens behavior in 26524 so they cannot
show a digital-zoom preview that their separate output pipeline does not reproduce.

FIRST TEST PLAN AFTER APK BUILDS
1. Launch Motion at 1x and capture a control photo.
2. Pinch 1x -> 0.6x and confirm the live value moves in the 0.6x button.
3. Pinch 0.6x -> 1x -> 3x -> 4.1x and confirm ownership crosses buttons.
4. Continue beyond 4.1x to 10x, 20x and 50x.
5. At several zooms, tap-focus center and near each edge.
6. Long-press AF lock at a zoomed view, capture, then verify lock survives.
7. Capture JPEG + DNG near 50mm-equivalent and at high zoom.
8. Verify JPEG pixel dimensions remain the active lens' normal binned dimensions.
9. Verify DNG remains full native/binned dimensions.
10. Upload the JPEG/DNG + log + motion trace for audit. The log should include IRIS_26524_ACTUAL_HAL_ZOOM entries so requested versus actual device zoom can be verified.

NOTE
26524 intentionally does NOT include the temporal-support/noise fix. Once zoom
is proven independently, the next build can address the ~3-4 frame-equivalent
support issue without mixing two root-level changes.

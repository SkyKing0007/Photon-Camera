PHOTON 26771 — UI ORIENTATION + USER-SELECTED STORAGE OWNERSHIP
STATUS: PREPARED / UPLOAD-READY. NOT ACTIONS-PROVEN YET.

RUNTIME AUTHORITY
- Branch: experimental-clean-photon-rebuild
- Successful 26770 commit: 0520e6a6f125fa5ff2ebf460d3d379cf9a7a9572
- Actions run: 37361885012
- Artifact: 11367536491 / photon-26770-foliage-chroma-midtone-trim
- Artifact SHA-256: ec923c2d021dd2f6d31bfed76c30849b0a092834bc913fb5fa9085137f5fdcd1
- Candidate TAR SHA-256: 57d5adc035132ab9d1d67c45f0bc7fd5532cc45f3e661ac2cb67cc09ba10a47d

VERIFICATION-MECHANICS AUTHORITY
- Successful 26770 build/handoff sequence, inheriting successful 26752 mechanics unchanged.
- 26752 commit: 69d5cb14f950d6fe5309441f7abf29d96631ab02 / run 37075896367.
- Core stage order/toolchain/mechanics delta: ZERO.

NO BACKUP BRANCH.
DO NOT MODIFY OR PUSH dev.
DO NOT UPLOAD ANY APK.
DO NOT COPY payload files directly into live app/src in vscode.dev; Actions reconstructs the canonical candidate from the exact successful 26770 compiled artifact.

INTENDED RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 30 PATHS
- 29 existing runtime paths modified.
- 1 intended addition: app/src/main/res/values-v31/styles.xml
- 0 deletions.
See 26771_RUNTIME_CHANGED_PATHS.txt for the exact complete list.

RUNTIME CHANGE
LAUNCH / UI
- Remove the app-owned branded SplashActivity launcher path. CameraActivity becomes the direct portrait launcher.
- API 31+ system launch surface is black with transparent splash icon and zero animation duration; Android's mandatory system launch transition itself remains system-owned.
- Physical UI orientation no longer depends on Android Auto Rotate. CameraActivity stays portrait-locked while eligible controls rotate from physical orientation.
- Mode pill and JPG/photo-format pill remain fixed.
- Front-camera physical rotation belongs to camera_switch_container; existing flip_camera_button rotationBy(180) tap animation remains untouched.
- iris_live_histogram and spektra_live_histogram use measured-size bottom-corner pivots: -90 hangs down from bottom-right; +90 hangs down from bottom-left, preventing rotation into timer/flash/settings controls.
- All lens labels use one common 9sp font inside the existing invisible circular button bounds so long live zoom labels remain contained.

STORAGE
- User prompt is “Storage Access” with: “Access to the storage folder is required for saving RAW video files and reading device custom configs.”
- Picker is unrestricted to a user-selected device-storage folder; no DCIM initial path or DCIM/PhotonCamera acceptance gate remains.
- Selected tree persists and owns Iris Camera/Tuning, Iris Camera/Spektra and Iris Camera/Raw.
- Photon FileManager.CreateFolders() ownership is removed. Historical Photon-named FileManager fields remain compatibility aliases only.
- Tuning/device/sensor/customCCT/settings/Spektra/RAW/DNG transport call sites are redirected to the selected Iris root as required.
- System DCIM/Camera remains independent and unchanged.
- Stale DCIM/PhotonCamera runtime literals are forbidden.
- Existing Iris Log.java and MotionTrace.java writer bytes and their current independent MediaStore/Downloads ownership/location remain unchanged; logs are NOT forced through SAF.

DNG SAFETY
- DNG domain remains complete at 6 files.
- Five DNG owners are byte-identical to 26770.
- IrisSabreSuperResDngWriter.java changes only output/delete/size transport to selected-root SAF.
- ImageSaver DNG publication changes only output stream transport.
- DNG serialization, tags, color metadata, dimensions, payload generation and math remain unchanged.

PROTECTED 26770 BEHAVIOR
- CaptureController/Motion admission, VGN/frozen containment, 26770 foliage safety, midpoint trim, MotionV2 render/gainmap, Sabre/Plan-B/Super-Res, alignment, exposure, UHDR HDR target, matrices/ACR3/saturation/sharpening/residual-chroma and full 271 asset-shader universe are protected unchanged unless listed solely as a storage transport consumer above.

UPLOAD WITH vscode.dev — TWO STAGES
STAGE 1 — upload all sealed handoff files EXCEPT the workflow file
1. Open branch experimental-clean-photon-rebuild in vscode.dev.
2. Upload/replace every file/folder from this ZIP EXCEPT:
   .github/workflows/build-26771-ui-storage-ownership.yml
   Keep handoff_payload_26771 exactly under the repository root.
3. Confirm Source Control shows NO live app/src or app/version.properties changes.
4. Commit and push the uploaded 26771 handoff files.
   Commit message: 26771: prepare UI orientation and storage ownership
5. Do not create a backup branch.

STAGE 2 — trigger exactly the intended 26771 workflow
1. Upload only:
   .github/workflows/build-26771-ui-storage-ownership.yml
2. Commit and push.
   Commit message: 26771: trigger UI storage ownership build
3. The intended workflow is “Build 26771 UI + Storage Ownership”.
4. Do not manually run historical workflows.

EXPECTED ACTIONS ORDER
sealed hashes/syntax -> exact 26770 artifact/candidate + manifests -> deterministic candidate reconstruction x2 -> semantic/ownership/domain checks -> complete unchanged shader-universe proof + pinned real glslang 16.5.0 inherited shader checkpoint -> frozen candidate byte equality -> real Kotlin/Java -> post-language frozen-candidate byte equality -> both-ABI native -> deterministic full-index forward/rollback patches core.abbrev 7/12/40 fuzz=0 -> PRE-BUILD SAFETY PROOF -> full :app:assembleDebug -> exactly one APK -> authority/protected/native/vendor/DNG/shader post-build invariance -> final candidate export.

SUCCESS ARTIFACT NAME
photon-26771-ui-storage-ownership

SUCCESS APK NAME
IrisCamera-0.9726771-26771-ui-storage-ownership-debug.apk

Do not call 26771 build-proven until that Actions run is successful and its artifact/candidate hashes are verified.

PHOTON 26761 — MEASURED-SNR ADAPTIVE CHROMA
STATUS: PREPARED / UPLOAD-READY ONLY — NOT ACTIONS-PROVEN YET

DO NOT CREATE A BACKUP BRANCH.
DO NOT MODIFY dev.
DO NOT UPLOAD OR COMMIT AN APK.
DO NOT EDIT THE SEALED FILES.
Branch: experimental-clean-photon-rebuild
Runtime authority before 26761: exact successful 26760 compiled candidate, commit c83ac4d417db537631b6ad15e4918754bd95e9e2, run 37167617673, artifact 11290197288.
Verification mechanics: exact successful 26752 procedure unchanged.

26761 runtime scope (exactly 5 existing files, 0 additions/deletions):
1. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
2. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
3. app/src/main/java/com/hinnka/mycamera/processor/MgcSabreKernelTuning.kt
4. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
5. app/version.properties

Behavior:
- One shared measured-output-SNR chroma permission policy: SNR <=10 => 1.00; SNR >=20 => 0.50; 10..20 linear.
- SNR is the propagated measured RAW/calibrated noise/Sabre merge SNR; ISO is NOT a scene-brightness switch.
- Normal Motion Auto residual chroma uses the shared policy while inherited local support/outlier/VGN/protected-floor logic remains owner.
- Night and Custom Exact remain unchanged.
- Super Res native Sabre/VGN remains sole RGB/chroma/highlight source; direct CFA remains luma/detail only.
- The existing 26760 same-material 3x3 SR chroma consensus is unchanged except its maximum blend now uses the shared measured-SNR permission; material/hue/coherent-color protections still gate locally.
- Ordinary zoom static GLSL, luma/detail, alignment, routing, frame count, highlight safety, UHDR/DNG, native/JNI/vendor remain protected.

TWO-STAGE vscode.dev UPLOAD

STAGE 1
Upload/replace EVERY path from this ZIP EXCEPT:
.github/workflows/build-26761-measured-snr-chroma.yml

Commit and push exactly:
26761: prepare measured-SNR adaptive chroma

STAGE 2
Upload ONLY:
.github/workflows/build-26761-measured-snr-chroma.yml

Commit and push exactly:
26761: activate measured-SNR adaptive chroma build

Expected single intended workflow:
Build 26761 Measured SNR Chroma
Expected artifact:
photon-26761-measured-snr-chroma
Expected APK inside Actions artifact only:
IrisCamera-0.9726761-26761-measured-snr-chroma-debug.apk

After Stage 2, inspect the single intended run. It must pass pinned glslang 16.5.0, Kotlin, Java, JNI, both NDK ABIs, deterministic patch proof, PRE-BUILD SAFETY, full assemble, exactly one APK, and post-build authority/protected/DNG/native/vendor invariance. Only then may 26761 become runtime authority.

# 26544 V1.3 upload instructions

**V1.3 is a build-procedure-only correction. The six-file 26544 runtime patch, version `0.9726544 / 26544`, Night logic, and all image-processing code are byte-identical to V1.**

The failed V1 run reached and passed real GLSL, Kotlin, and Java compilation, then failed at native CMake configuration with `26507 pinned libjpeg-turbo source missing`. V1.1 restored the exact successful-26543 bjzhou native bootstrap (`09c76e57e8f01a5a8fc536ab41fc80ba642d4042`) before Gradle assemble and adds a permanent pre-assemble regression gate for both `libjpeg-turbo` and `libultrahdr`.


Target: **0.9726544 / 26544**

This build addresses the complete Night failure sequence discussed after 26543, without changing Night image-quality math.

## What the source comparison proved

The latest 26543 regression and the older “DNG saves but JPEG never appears” issue are **different failure layers**.

### New 26543 capture regression

The exact tested 26543 V1.4 source creates the fresh non-ZSL RAW `ImageReader` with `maxImages = 3`, then its new Night spool can retain three live Camera2 RAW `Image` objects on asynchronous disk workers. Android defines an acquired `Image` as outstanding until `Image.close()`, and reaching `maxImages` can stall the producer or make the next acquire throw.

Original Photon’s working RAW ownership instead deep-copies/consumes the RAW while the Camera2 `Image` is valid and closes the `Image` immediately. 26544 restores that **ownership discipline only**:

- SHORT reference: app-owned copy, then Camera2 `Image.close()` before callback return;
- all other Night RAWs: synchronously write into Iris’s bounded disk-backed spool while the Camera2 `Image` is valid, then close it before callback return;
- no live Camera2 `Image` is handed to an executor;
- Iris still keeps only one persistent in-memory reference RAW plus disk-backed auxiliaries.

### Longstanding post-RAW/JPEG failure

26544 does **not** assume the RAW fix automatically solves the older failure. The same APK adds durable checkpoints through:

`Night batch -> MGC begin/end -> DNG begin/end -> PostPipeline begin/end/close -> base JPEG begin/end -> Jin begin/end -> final JPEG begin/end -> saved notification -> processing complete`

Those checkpoints are synchronously flushed/fsynced. Android 11+ `ApplicationExitInfo` is read on the next process start, and `ActivityManager.setProcessStateSummary()` records the last major Night stage in the OS exit record.

Therefore, if Night still reaches DNG but fails before JPEG, this build must tell us **which exact stage killed the process and Android’s exit reason** rather than giving another silent failure.

## What 26544 deliberately does NOT change

It does **not** restore original Photon Night processing. Iris remains owner of:

- fresh 12 SHORT + 3 LONG Night policy;
- shutter-frozen Iris exposure/frame decisions;
- exact per-frame Camera2 metadata;
- immutable `IrisNightBatch`;
- MGC Spatial-RGB reconstruction;
- Iris Night PostPipeline/tone/color path;
- base-JPEG-before-Jin policy;
- optional Jin final enhancement;
- DNG semantics.

No GLSL or Kotlin source changes. No MGC math, Figure-7 math, RCD/Spatial-RGB math, denoise strength, tone, sharpening, or Motion processing changes.

## Cold-start / post-crash correction

Every **new Android process** now forces `CameraMode.MOTION` before `Settings` and camera UI/session state are constructed. A crash in Night therefore cannot make the next process restore stale Night as the startup mode. Normal mode switching during the same healthy process remains unchanged.

The private lifecycle logger is initialized at `Application.onCreate`, before ordinary PhotonLog storage setup. Once normal storage access exists, the private crash-session logs are mirrored into the exported PhotonLog folder.

## Exact runtime scope

Exactly six runtime files differ from the user-tested 26543 V1.4 candidate:

1. `app/src/main/java/com/particlesdevs/photoncamera/app/PhotonCamera.java`
2. `app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java`
3. `app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java`
4. `app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java`
5. `app/src/main/java/com/particlesdevs/photoncamera/util/Log.java`
6. `app/version.properties`

## Exact 26543 authority

26544 does not trust repository `app/src` as runtime authority. Actions downloads the exact successful user-tested 26543 V1.4 artifact:

- commit: `7c6fa593abf9c50464e6093a1af75e92c2685705`
- run: `32927284550`
- artifact ID: `9592028495`
- artifact ZIP SHA-256: `8116403e8a7f21672e194294e359c5b289d424ef6bf47cbc06ebbbb6dbc4437b`
- exact candidate TAR SHA-256: `18e380899a2d1817ccdcc840f30ba69290b3a1c6541d9083796062f22d229c48`
- exact source manifest: **967/967**

It applies the 26544 patch only after all three pins pass.

## Safety / compiler gates

The workflow must prove, in order:

- exact 26543 artifact/TAR/967-file authority;
- exact six-file changed scope;
- 26543 async live-`Image` ownership removed;
- Iris Night ownership preserved;
- crash-durable post-RAW/JPEG checkpoints present;
- Motion cold-start authority occurs before `Settings` construction;
- prior 26540/26543 compiler-regression contracts preserved;
- real pinned **glslangValidator 16.5.0** regression compile;
- canonical full-index forward/rollback patch byte-identical under Git `core.abbrev=7`, `12`, and `40`;
- forward patch `fuzz=0` gives exact 26544 candidate;
- rollback `fuzz=0` gives exact 26543;
- `PRE-BUILD SAFETY PROOF PASSED`;
- real `:app:compileDebugKotlin`;
- real `:app:compileDebugJavaWithJavac`;
- real `:app:assembleDebug`;
- source manifest unchanged after Gradle;
- exactly one debug APK.

No additional backup branch is required from you for this handoff. The 26544 preparation used a local pre-change safety branch/patch and the package includes a proven exact rollback patch to 26543. The Actions workflow never commits transformed `app/src` back to GitHub.

## Upload

Extract this ZIP and upload **all contents** to the root of `experimental-clean-photon-rebuild`, preserving the `.github/workflows/` folder. Do not manually edit `app/src`.

Suggested commit message:

`26544: fix Night capture ownership and root-cause lifecycle`

Expected Actions artifact:

`photon-26544-night-rootcause-lifecycle`

Expected APK:

`IrisCamera-0.9726544-26544-night-rootcause-lifecycle-debug.apk`

## Phone acceptance sequence

Use the exact sequence that has been failing:

1. Launch Photon. It must open in **Motion**.
2. Take one Motion photo and wait until its JPEG appears.
3. Switch to Night.
4. Press Night shutter and allow the ring/capture to finish.
5. Night must capture its full fresh 12+3 set.
6. If RAW/DNG saving is enabled, verify the DNG.
7. Verify the Night JPEG appears and the app remains alive.
8. Close/relaunch Photon: it must start in **Motion**.
9. Take another Motion shot: normal ring/animation and JPEG must both work.

If Night still exits, immediately reopen Photon once before exporting PhotonLog. The export should then contain both the failed process’s final `IRIS_26544_NIGHT_*` breadcrumb and `IRIS_26544_PREVIOUS_PROCESS_EXIT ... processState=...` from the new process.

That result will distinguish capture/HAL failure, MGC/native/GPU failure, PostPipeline failure, memory kill, Java crash, JPEG publication failure, or Jin failure without another speculative build.


## V1.2 post-build validation correction

V1.2 changes **handoff/build validation only**. The 0.9726544 / 26544 runtime patch is byte-identical to V1/V1.1.

The V1.1 Actions run proved real glslang, Kotlin, Java, native CMake for both ABIs, and `:app:assembleDebug` all PASS. It then falsely failed because the strict 967-file application candidate validator was run against the live tree after the pinned 26507 native vendor subtree had been restored, producing 1744 files.

V1.2 permanently separates those authorities after Gradle:

- audited Iris/application source is compared with the vendor-excluding manifest and must remain unchanged;
- the exact pinned `third_party_26507` vendor tree is independently rechecked against `26507_BJZHOU_NATIVE_DEPENDENCIES.sha256`;
- a clean vendor-stripped post-build copy must contain exactly 967 files and pass the original 26544 runtime validator;
- exactly one Gradle debug APK must exist.

Permanent regression: never compare the pre-vendor 967-file application manifest against the post-vendor augmented source tree.


## V1.3 canonical post-build proof correction

V1.3 makes **no runtime-source or version change**. It removes the V1.2 attempt to recreate a 967-file authority from the Gradle-mutated build tree.

After `:app:assembleDebug` passes, V1.3 follows the 26543 V1.4 authority model:

- re-hash the untouched frozen 967-file candidate and require byte-identical equality with its pre-build manifest;
- rerun the 26544 runtime contract directly on that frozen candidate;
- compare the live vendor-excluding Iris source domain against the frozen candidate;
- verify `third_party_26507` independently against `26507_BJZHOU_NATIVE_DEPENDENCIES.sha256`;
- require exactly one Gradle debug APK and hash/copy it.

Permanent regressions:

1. Never compare the pre-vendor 967-file application manifest against a vendor-augmented worktree.
2. Never reconstruct authoritative source invariance from a Gradle-mutated worktree.
3. The frozen candidate, pinned vendor manifest, and produced APK are separate authorities and are validated separately.

26531 V1.3 Iris Spatial / zero-luma / corrected-FOV / Kotlin compile-fix handoff

V1.3 is a compile-correction revision. It preserves the intended 26531 image math and keeps build/version at 0.9726531 / 26531.

Upload the CONTENTS of this ZIP to the root of branch:
  experimental-clean-photon-rebuild

Do not place the files inside an extra folder.
Do not modify app/src manually.
Do not push to dev.

The workflow display name is:
  Build 26531 V1.3 Iris Spatial Zero Luma FOV Compile Fix

Expected Actions artifact:
  photon-26531-v1-3-iris-spatial-zero-luma-fov

Expected APK:
  IrisCamera-0.9726531-26531-iris-spatial-zero-luma-fov-debug.apk

V1.3 compile corrections:
1. The SHADOW_LONG clipping-mask shader keeps its original dense flow input:
     flowTexture = prepared.flowTexture
   Final Bayer alignment is used only by the Spatial strength/noise capture path.
2. Iris BayerKernelTuning now declares and initializes the reference green shot-noise and read-variance fields consumed by expectedMergeWeight.
3. New preflight_26531_iris_kotlin_api_contracts.py checks both API contracts before handoff and includes a focused kotlinc compile when kotlinc is available.
4. The guarded Android build now runs :app:compileDebugKotlin and :app:compileDebugJavaWithJavac as explicit gates before :app:assembleDebug.
5. The Python-cache manifest guard from V1.2 remains active.

The workflow does not use repository app/src as runtime authority. It recovers the exact successful 26530 V1.2 candidate artifact at HEAD 8e847de9841b5ed3522970a1106f2b53cb3f7eb1, verifies its deterministic tar/manifest hashes, regenerates forward+rollback patches before candidate writes, validates exact seven-file runtime scope, runs Iris Kotlin API + shader/native/DNG preflights, prints PRE-BUILD SAFETY PROOF PASSED, increments to 0.9726531/26531, runs real Android Kotlin/Java compile gates, then assembles exactly one APK.

Sabre handling:
Sabre source is allowed to exist, but it remains dormant. The validator fails if the active Motion bridge selects Sabre, if the active denoise pass becomes SABRE_DEFAULT, or if a protected Sabre owner changes. There is no repository-wide word-ban gate that can falsely fail just because dormant Sabre source exists.

Primary on-device checks after a successful build:
1. 4.1x optical baseline and ~8.2x versus the same GCam framing.
2. 4.1x lens at local 30x (~123x displayed) versus GCam 120x: FOV should match closely again.
3. Inspect 400–800%: fine luma texture/grain should survive better with effective Iris luma=0 while chroma remains controlled.
4. Moving people/cars/leaves/hair/branches at >=8x: no new clumping, zippering, ghosting, or colored blocks.
5. Harsh highlights/text edges: no pink/magenta/green line/dot/block recurrence.
6. Keep DNG and logs; telemetry should show requestedLuma, effectiveMgcLuma=0.0, chroma, srScale, requestedLocalZoom, finalFovZoom, finalRenderLocalZoom, pass=SPATIAL_DEFAULT, sabreSelected=false. (The legacy telemetry key is retained for this build to avoid mixing a namespace refactor into the compile fix.)

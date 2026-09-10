PHOTON 26622 R1 — LOCAL-LAPLACIAN TELEMETRY LIFETIME REPAIR

UPLOAD TARGET
- Branch: experimental-clean-photon-rebuild
- Expected parent HEAD: 13073d0f358e9098e4288e60b3920bc208e8838b
- Upload/extract every file in this handoff to the repository ROOT, preserving paths.
- Do NOT manually copy handoff_payload_26622_r1/app/** into live app/**.
- Commit once and push once.
- Suggested commit message: 26622 R1 local laplacian telemetry lifetime repair

RUNTIME AUTHORITY
- Successful 26621 R1 commit: 13073d0f358e9098e4288e60b3920bc208e8838b
- Actions run: 34476774939
- Artifact ID: 10151935955
- Artifact: photon-26621-r1-new-simplified-local-laplacian
- Artifact ZIP SHA-256: ecd9c7ac803f484297bafabb3ffd8bff1e14cbdfbfe0b1d2b13c1a60cbff4097
- Exact compiled candidate TAR SHA-256: d5554aa30bd763ce725bec5eea1dc8165e9e898cc698f00061ea2aaa563176ae
- Successful 26621 APK SHA-256: f4dec503de633daa5342af1bf986262718877fbd15951198f2d9ae5b6895a3ba

VERIFICATION-MECHANICS AUTHORITY
- Exact successful 26621 R1 build procedure, which inherited successful 26620 ordering.
- No backup.
- No APK is included in this handoff.
- No source or APK is pushed automatically.

DEVICE FAILURE BEING REPAIRED
Both supplied Motion captures fail after Local-Laplacian reconstruction with:
java.lang.NullPointerException: Attempt to read from field
'android.graphics.Point com.particlesdevs.photoncamera.processing.opengl.GLTexture.mSize'
on a null object reference in
MotionV2Render.iris26621BuildLocalLaplacianTone(MotionV2Render.java:416).

Root cause:
- 26621 releases/closes guide[] textures and sets guide[level] = null.
- A later telemetry Log.i() reads guide[last].mSize for the coarsest dimensions.
- The telemetry dereference throws before keepFinal=true, so finally closes the completed finalTone and the Motion capture aborts.

RUNTIME DELTA
Exactly two paths versus the successful 26621 compiled candidate:
1. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
2. app/version.properties

The Java repair snapshots coarsestWidth/coarsestHeight while the guide texture is alive, before release, and telemetry later logs only those primitive integers.
No 26621 global-tone equation, Local-Laplacian shader, scale/reference constant, RGB scalar, UHDR logic, true-2x math, SHORT/CFA/Sabre/merge/VGN/denoise/color/DNG behavior is changed.

TARGET
VERSION_NAME=0.9726622
VERSION_BUILD=26622

STATUS BEFORE ACTIONS
Prepared/upload-ready only. Real Java/Kotlin, NDK, full assemble and post-build invariance require GitHub Actions.

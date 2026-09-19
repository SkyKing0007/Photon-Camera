PHOTON / IRIS 26673 R1 — ANDROID16 HEIC UHDR + FIXED MANUAL MIDPOINT

Upload/extract the entire ZIP at the repository root in vscode.dev on branch experimental-clean-photon-rebuild, replacing matching files. Do not move handoff_payload_26673 files into app/src manually: the guarded Actions build reconstructs the exact successful 26672 compiled-candidate authority and overlays only the sealed payload after all authority checks.

Runtime authority:
- successful 26672 commit 2b6c3ef726cc8532ebfa5e4499bde6ab79bdbc14
- Actions run 35471368787
- artifact 10593065124 / photon-26672-r1-heic-google-v2-ui-polish
- artifact SHA256 a8230bc9ff9e46bd8ad4d2688dd152542386dda22576a577d07b132c5aaba95c
- compiled candidate TAR SHA256 b82a82930a507698fa3aaedc458c9dd4721dea8f139333cdcdb398a7adc50d86

Runtime changed-file allowlist: exactly 3 modifications, 0 additions, 0 deletions:
1. app/src/main/cpp/iris_heic_jni.cpp
2. app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java
3. app/version.properties

26673 targets only:
- Normal 1x HEIC Ultra HDR publication: explicit Display-P3 full-range YUV420 carrier and Android16/AOSP-style P3+sRGB+matrix-unspecified base/tmap plus unspecified gain-map color aspects. Existing Iris SDR pixels, gain-map pixels, ISO 21496 metadata, Android readback/numerical proof, and hardware HEVC owner stay inherited; Super-Res HEIC is exact 26672.
- Manual buttons: establish one fixed Y position from the exact final successful-26672 coded visible geometry so row center is halfway between slider outer bottom and activated chevron visible upper tip. Slider and chevron do not move. Chevron close/open only hides/shows the row; it never changes row Y after establishment.
- Version 0.9726673 / build 26673.

Everything else is hardlocked to successful 26672, including JPEG/JPEG-R, render/gainmap shaders, highlight separation, SHORT/NORMAL/LONG, Motion/Sabre, alignment, temporal rejection, noise/denoise, Local-Laplacian, color, viewfinder, histogram, manual-slider touch ownership, front-switch vector, DNG, native/vendor protected files.

No backup created, by request.
Real GLSL/Kotlin/Java/NDK/full assemble are not claimed by the handoff itself; GitHub Actions is the authoritative compiler/build proof.

Suggested commit message:
26673 R1: Android 16 HEIC Ultra HDR publication and fixed manual midpoint

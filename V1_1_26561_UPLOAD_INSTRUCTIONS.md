# Photon 26561 V1.1 upload instructions

Target branch: `experimental-clean-photon-rebuild`

Upload/commit **only the files in this V1.1 handoff ZIP**. Do not edit `app/src`, do not upload an APK, and do not modify `dev`.

V1.1 is an infrastructure-only correction to the failed 26561 V1 handoff. It makes **zero runtime-candidate changes**. Runtime authority remains the exact successful compiled 26560 Actions artifact, and the 26561 runtime transform/manifests/patches remain identical to V1.

The V1 Actions run `33267796720` passed exact authority reconstruction, candidate transform/ownership, runtime-expanded GLSL hashes, reserved-identifier scan, deterministic patch proof, and pinned real `glslangValidator 15.1.0`. It then failed before Kotlin/Java/Gradle because V1 incorrectly compared stale repository native/vendor state against the 26560 artifact vendor pin before installing the frozen candidate.

V1.1 permanently corrects that ordering:
1. record repository pre-install runtime/vendor state for diagnostics only;
2. install the exact frozen 26561 candidate reconstructed from the successful 26560 artifact;
3. compare the installed runtime and installed native/vendor bytes to the frozen candidate/authority pins;
4. only then run real Kotlin/Java, full `:app:assembleDebug`, exactly-one-APK, and post-build invariance.

The V1.1 package names use the `V1_1_26561_*` prefix and distinct V1.1 script/workflow filenames so the failed V1 workflow is not retriggered by the V1.1 commit.

Expected parent commit for the V1.1 handoff commit:
`1dd9907234e82235dc9f418418e36fbad2b97221`

Suggested commit message:

`26561 V1.1 fix pre-install authority gate`

Do not call 26561 build-proven until the V1.1 Actions run completes successfully and produces the `photon-26561-v1-1-sabre-native-super-res-adaptive-color` artifact.

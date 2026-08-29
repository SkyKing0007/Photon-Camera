# Photon 26561 V1 upload instructions

Target branch: `experimental-clean-photon-rebuild`

Upload/commit **only the files in this handoff ZIP**. Do not edit `app/src`, do not upload an APK, and do not modify `dev`.

The workflow is path-scoped to the 26561 package names and reconstructs runtime from the exact successful compiled 26560 Actions artifact. It applies the 26561 transform candidate-first, compiles exact runtime-expanded GLSL with pinned glslangValidator 15.1.0, then runs real Kotlin/Java and full `:app:assembleDebug`.

Suggested commit message:

`26561 Add Sabre-native Super Res and adaptive color`

Do not call 26561 build-proven until the Actions run completes successfully and produces the `photon-26561-v1-sabre-native-super-res-adaptive-color` artifact.

PHOTON 26690 R1 — UNSPEKTRAWESOME JNI STARTUP CONTAINMENT

Purpose
- Fix the successful-26689 R1.2 device startup SIGABRT caused by the exact Unspektrawesome 1.1.2 native JNI_OnLoad requiring com.unspektrawesome.diagnostics.InternalLogRecorder while the APK omitted that class.
- Prevent dormant Spektra native initialization from being part of ordinary Iris Photo startup. The original Unspektrawesome RawVulkanPreviewController is created only when Spektra is activated.

Runtime authority
- commit 356871e584bb2712ab40c2182a0bb49f6de6f021
- run 35880887000
- artifact 10761062729
- artifact ZIP SHA-256 6330f4ff9c88e5be18ad9de4c1bd9bbaec9c11fc0de4f3a39538ac81230594c3
- compiled candidate TAR SHA-256 ba23624e1644fad682b6bda33546ae63d2b566663467e300ef0f7fd24f94a223

Verification-mechanics authority
- exact successful 26689 R1.2 sequence
- build blob cbdbd6e9b19316168909f5dd619cb09415859cca
- workflow blob e13da2dd63706054812b0c95637c4b53dbdb4ffc

Runtime changed-file allowlist (exactly 3)
- app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java
- app/src/main/java/com/unspektrawesome/diagnostics/InternalLogRecorder.java
- app/version.properties

Candidate counts
- base 1819 files
- candidate 1820 files
- protected unchanged 1817 files
- native 819 / 819 byte-invariant
- vendor 778 / 778 byte-invariant
- DNG 7 / 7 byte-invariant
- asset shaders 271 / 271 byte-invariant

Delivery
Upload every file/folder in this handoff ZIP to the root of experimental-clean-photon-rebuild in ONE commit. The 26690 workflow is new and activates only after that complete commit exists.
Suggested commit message:
26690 R1: contain Unspektrawesome JNI startup and restore native callback contract

Status before upload
- deterministic candidate reconstruction: local PASS
- semantic/ownership/runtime-crash regressions: local PASS
- deterministic full-index forward/rollback patch proof at core.abbrev 7/12/40: local PASS
- exact successful 26689 R1.2 artifact/candidate replay: required before final packaging
- real project GLSL/Kotlin/Java/NDK/full assemble/final APK JNI proof: NOT RUN locally; GitHub Actions is authority

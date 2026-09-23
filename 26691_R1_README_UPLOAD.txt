PHOTON 26691 R1 — SPEKTRA CAPTURE + NATIVE HISTOGRAM

Purpose
- Fix the successful-26690 device behavior where Spektra preview streams correctly and shutter reaches the hosted controller, but capture remains IDLE because RawVulkanPreviewController requires a cached preview lens-shading map before issuing the still request.
- Restore a Spektra-only live histogram using the exact hosted Unspektrawesome VulkanRenderer.histogramPixels/native ViewfinderHistogram path.
- Preserve every non-Spektra Iris histogram path unchanged.

Runtime authority
- commit a0aab18288222675dddb0fa0c53be46101cf539f
- run 35887882502
- artifact 10763587705 / photon-26690-r1-unspektrawesome-jni-startup-containment
- artifact ZIP SHA-256 bd418d6e1271c20271a245c09869301bdb9988ed51b603f42417cf15cc99644d
- compiled candidate TAR SHA-256 860bf89b34fb1a9cbb5e5f8d49457ef8b99dfa1ab1da6f6a68388884a7fde40d

Verification-mechanics authority
- exact successful 26690 sequence
- build-script Git blob f7b1c768d1a92205f9379a3b6b45a629a217bbec
- workflow Git blob 5fe2551f3467ba2cf279efdb1bba17559ef58acc

Runtime changed-file allowlist (exactly 7 = 5 modified + 2 added)
- app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java
- app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java
- app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/SpektraLiveHistogramView.java (added)
- app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt
- app/src/main/res/drawable/ic_spektra_histogram.xml (added)
- app/src/main/res/layout/camera_fragment.xml
- app/version.properties

Candidate counts
- base 1820 files
- candidate 1822 files
- protected unchanged 1815 files
- native 819 / 819 byte-invariant
- vendor 778 / 778 byte-invariant
- DNG 7 / 7 byte-invariant
- asset shaders 271 / 271 byte-invariant

Behavioral contract
- Shutter may never be rejected solely because no cached preview lens-shading map exists.
- Still-frame LSC is preferred; same-route preview LSC is fallback; no valid LSC remains a supported capture case.
- Spektra histogram reads only the active Spektra renderer's native 128x128 histogram image.
- Spektra histogram is off by default and uses a Spektra-only top toggle, matching the supplied Unspektrawesome reference behavior.
- Existing Iris live histogram implementation is not modified and is restored when Spektra presentation exits.
- Working 26690 Spektra startup/viewfinder/mode switching and exact 1.1.2 native library are preserved.

Delivery
Upload every file/folder in this handoff ZIP to the root of experimental-clean-photon-rebuild. If the hidden .github workflow cannot be uploaded with the rest, commit the visible payload/proofs first and upload the single 26691 workflow second; the 26691 workflow does not exist until that final upload and therefore cannot run against the incomplete first commit.
Suggested payload commit message:
26691 R1 payload and proofs
Suggested workflow activation commit message:
26691 R1: activate Spektra capture and native histogram build

Status before upload
- exact successful 26690 Actions artifact/candidate replay: required and performed by packaged local-prebuild before final sealing
- deterministic candidate reconstruction / semantic / ownership / regressions / authority: local gates
- deterministic full-index forward/rollback patch proof at core.abbrev 7/12/40: local gate
- real project GLSL/Kotlin/Java/NDK/full assemble/final APK proof: NOT RUN locally; GitHub Actions is authority

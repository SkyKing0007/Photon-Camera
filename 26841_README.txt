PHOTON 26841 — HDR PREVIEW + WARM MIDTONE

UPLOAD TO BRANCH: experimental-clean-photon-rebuild
NO BACKUP BRANCH.
DO NOT upload any __pycache__ folder or .pyc file. None is included in this handoff.

Stage 1: upload every file/folder from folder 1 to repository root. Commit:
26841 hdr preview warm runtime

Stage 2: upload folder 2/.github/workflows/build-26841-hdr-preview-warm.yml to .github/workflows/. Commit:
26841 exact 26840 build workflow

Stage 3: upload folder 3/26841_HANDOFF_HASHES.sha256 and folder 3/TRIGGER_26841.txt to repository root. Commit together:
26841 handoff hashes and trigger

The Stage-3 commit triggers GitHub Actions. Do not trigger before all three stages are committed.

Runtime authority: successful 26840 run 38779952106, commit c641816db971b7059c2fd511745154f7dc1f4f36, artifact 11994964129, artifact SHA-256 a90f2e8b999ed9f263064e7b0cb31224cbe9ad13aac7c1ce2eb155b0b0f853bf.
Verification mechanics: exact successful 26840 17-stage procedure, unchanged.
Runtime changed-file allowlist: exactly 3 files — CaptureController.java, motionv2/color_transform.glsl, app/version.properties.
Infrastructure procedure delta from successful 26840: zero.
Local status: prepared/upload-ready only. Real pinned glslang, project Kotlin/Java, both-ABI native/NDK and full assemble are authoritative in Actions.

PHOTON 26837 — DEVICE-SAFE FINAL CLIP-ZONE CHROMA

Runtime authority: successful 26836 Actions run 38676628346, commit 4ccde11921e28b8fd3bd394d3d768d0fca37f8b9, artifact 11946549086.
Verification mechanics authority: exact successful 26836 17-stage build/handoff procedure; zero procedural delta.
No backup branch.

Runtime change: exactly 3 files. 26836 Claude WB-linear math, NORMAL-only mask, post-residual/post-26728 insertion, SR bilinear-mask chroma handoff, LONG luminance-only, DNG, high-zoom, tone/UHDR are preserved. 26837 only replaces the crashing final compute image-store execution with Iris's proven immutable GLES3 texture/FBO fragment mechanics. The fragment shader mirrors the exact 26836 per-pixel equations; output is pre-copied and M==0 uses discard, preserving the no-op pixels.

Permanent regression from device failure: the active final chroma owner may not use glBindImageTexture, glDispatchCompute, SSBO, or mutable glTexImage2D storage.

Upload in order:
1. Upload/replace everything in folder 1 and commit.
2. Upload folder 2 workflow and commit.
3. Upload folder 3 hash manifest + trigger and commit/push. Only step 3 should trigger Actions.

Before Actions success this handoff is PREPARED / UPLOAD-READY only.

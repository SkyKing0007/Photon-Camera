PHOTON 26727 — RGBA16F HALF-FLOAT UPLOAD REPAIR

Upload exactly like 26726 on branch experimental-clean-photon-rebuild.
1. Extract this ZIP. Do NOT upload the ZIP itself.
2. Upload/replace every path listed in 26727_UPLOAD_PATHS.txt EXCEPT the workflow YML; preserve folders. Commit and push.
3. Then upload only .github/workflows/build-26727-rgba16f-half-float-upload.yml. Commit and push.
4. Only the intended 26727 workflow should trigger.

Runtime change: universal 26726 RGBA16F carrier remains intact. 26727 adds an explicit GL_HALF_FLOAT client upload for the exact 8-Bpp Motion/Night carrier so the GPU does not reinterpret half-float bytes as 32-bit GL_FLOAT. No IQ, Sabre/Wronski/VGN, capture, tone, color, UHDR, frame-count, or scheduling change is included.

Status before Actions: prepared/upload-ready, NOT build-proven.

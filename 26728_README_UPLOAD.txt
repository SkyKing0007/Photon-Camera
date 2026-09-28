PHOTON 26728 — PHYSICALLY SUPPORTED CHROMA MAGNITUDE

Upload exactly like successful 26727 on branch experimental-clean-photon-rebuild.
1. Extract this ZIP. Do NOT upload the ZIP itself.
2. Upload/replace every path listed in 26728_UPLOAD_PATHS.txt EXCEPT the workflow YML; preserve folders. Commit and push.
3. Then upload only .github/workflows/build-26728-physically-supported-chroma.yml. Commit and push.
4. Only the intended 26728 workflow should trigger.

Runtime change: VGN-cleaned hue/direction remains authoritative. Pre-VGN physical RGB supplies magnitude evidence only under strict CFA validity/topology/direction agreement and hard false-color/highlight vetoes. A compact Motion-only floor preserves proven magnitude across the existing residual chroma denoiser. No device/lens/zoom special case. Night, DNG, native/vendor, capture/flicker, global saturation/matrices/ACR3, high-zoom detail and global denoise strength remain unchanged.

Status before Actions: prepared/upload-ready, NOT build-proven.

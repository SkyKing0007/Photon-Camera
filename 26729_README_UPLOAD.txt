PHOTON 26729 — VGN CHROMA CONTAINMENT + PER-LENS RESIDUAL LEVELS

Upload exactly like successful 26728 on branch experimental-clean-photon-rebuild.
1. Extract this ZIP. Do NOT upload the ZIP itself.
2. Upload/replace every path listed in 26729_UPLOAD_PATHS.txt EXCEPT the workflow YML; preserve folders. Commit and push.
3. Then upload only .github/workflows/build-26729-vgn-chroma-containment.yml. Commit and push.
4. Only the intended 26729 workflow should trigger.

Runtime: VGN blocks chroma transport across coherent material/color boundaries even for similar-luma colors, while retaining 26728 false-color/physical hue safety. Motion adds Custom Residual Chroma Levels 1-5, each exact 0.0..5.0 with 0.1 steps and existing per-lens persistence. All five zero explicitly disables residual MGC chroma; Auto preserves 26728 SNR behavior. Night/DNG/capture/high-zoom detail/ACR3/matrices/UHDR remain unchanged.

Status before Actions: prepared/upload-ready, NOT build-proven.

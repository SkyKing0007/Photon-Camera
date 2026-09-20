PHOTON / IRIS 26676 R1 — Fast HDR WYSIWYG + Iris Watermark

Upload/extract this handoff at repository root in vscode.dev while branch experimental-clean-photon-rebuild is exactly at successful 26675 commit 2992abb5ec9ec577e7bd088811319bf402c783bb. Replace matching handoff files. Do NOT move handoff_payload_26676 into app/src manually. Commit/push the handoff files once; GitHub Actions reconstructs and compiler-proves the runtime candidate from the exact successful 26675 Actions artifact.

Runtime intent:
- Preserve successful 26675 post-shutter HDR, Manual icon alignment, SHORT admission, HEIC/UHDR, denoise/color/tone behavior.
- Restore exact 26674 settled WYSIWYG preview presentation.
- Replace only the protected-NORMAL increase cadence with one full confirmed target request; retain slow/hysteretic release.
- Block shutter freeze while a stronger protection generation is pending/not physically converged.
- Replace all original Photon watermark asset/fallback rendering with the new Iris Camera / PHOTOGRAPHY mark, controlled only by Settings > General > Watermark.
- Final-raster watermark geometry: lower-right, 14.5% width, 1.2% safe inset, normalized to final output dimensions.

Status before Actions: prepared/upload-ready only. Real GLSL/Kotlin/Java/NDK/full assemble remain Actions authority.

PHOTON CAMERA 26649 R1 — PHOTON HIGHLIGHT COMPRESSION PARITY

Upload/replace every path listed in R1_26649_UPLOAD_PATHS.txt into experimental-clean-photon-rebuild, commit once, push once.

Runtime authority is the exact successful 26648 R1.2 compiled candidate from commit 3b46a176d4d018613b17912bce30ebdb6e2fd7e7, Actions run 35053661730, artifact 10429479923, artifact SHA-256 3d88827bcd17f5361e32b448519f77fbb9b140afd6b21bafeb37deb814a5ce17, candidate TAR SHA-256 5b4bbc97b0958e7bcf68bfb39651fee051271610ffc69d8d8692eb664c1f46ca.
Runtime delta from successful 26648 R1.2: exactly 5 existing runtime files / 0 additions.

26649 is intentionally limited to the common Motion highlight-presentation owner. It reproduces Photon Highlight Compression's adaptive knee law (0.90 -> 0.55 at clipped fraction 0.10) and exact quadratic upper-range shoulder, applies it before Local Laplacian, and retires the later Iris 26635 smooth bright-base lift / 0.78 bright-residual suppression that could undo highlight separation. The existing Iris exposure/color authority is retained; the already-frozen Iris clip-population evidence drives the Photon knee so shadows/midtones/color do not inherit Photon's whole AutoExposure pipeline.

SHORT/fusion, color matrices/saturation/VGN, JPEG Ultra HDR encoder/gain-map owner, HEIC Java/native/hardware encoder path, DNG, CaptureController, UI and native code are protected byte-identical to successful 26648 R1.2. HEIC no-pop work is deliberately deferred.

No backup created. Target 0.9726649 / 26649. Do not modify dev.

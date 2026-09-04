Photon 26595 V1 — phase-coherent SHORT + Super Res handoff

Runtime authority: exact successful 26594 V1.1 compiled Actions candidate
  commit 43205d89cc9807e02b300e9f6ab9a10324bf4c75
  run 33878860474 / job 101042303061 / artifact 9939113841
  artifact ZIP SHA-256 2f6921ccb3c6b4cf71ddf2797e18f427e1dbe51204627e1278680fce90e20583

Verification mechanics: preserve successful 26593 ordering unchanged; successful 26594 inherited it and is additionally hash-audited.
Backup: none, by user request.
Runtime allowlist: exactly 3 files (two Sabre Kotlin owners + app/version.properties).

26595 correction:
- remove Sabre photometric rejection/unblocker as SHORT HDR geometry vetoes;
- expose pure local flow variation in RAW pixels without changing Sabre flow.z semantics;
- use exact subpixel same-CFA-phase SHORT interpolation for boundary radiometry/headroom;
- allow true multi-phase sensor-clipped cores to use SHORT independent of flood depth, while requiring SHORT brightness/headroom and pure flow coherence;
- keep near-clip/non-sensor-loss feathering boundary-radiometry anchored;
- count the exact full-resolution finalized SHORT mask on GPU (one uint readback);
- keep whole-RGB RGBA16F 0.90..0.98 handoff;
- Super Res keeps NORMAL-only CFA/detail evidence but consumes the exact restored native SHORT RGB/highlight guide when enabled;
- DNG remains NORMAL-only.

Normal delivery: upload this ZIP's contents to experimental-clean-photon-rebuild as one clean commit directly on successful 26594. GitHub Actions performs authoritative GLSL/Kotlin/Java/NDK/full assemble proof.

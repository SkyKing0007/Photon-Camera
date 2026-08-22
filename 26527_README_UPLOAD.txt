Photon Camera 26527 - upload/build instructions
===============================================

This is a handoff-only package. Do NOT manually edit app/src and do NOT push or modify dev.

Required branch:
  experimental-clean-photon-rebuild

Required predecessor HEAD:
  0c57e0a887a66bcc57c59d868ddf4d2f53c48130

What to do in vscode.dev
------------------------
1. Extract this ZIP into the repository root, preserving the .github/workflows folder.
2. Confirm the new root files plus:
     .github/workflows/build-26527-final-mgc-zoom-dng.yml
   are visible in Explorer / Source Control.
3. Do not modify app/src.
4. Commit these handoff files on experimental-clean-photon-rebuild.
5. GitHub Actions workflow "Build 26527 Final MGC Zoom DNG" will run automatically on the push.
   It may also be started manually with workflow_dispatch.

No separate runtime-source upload is required. The workflow downloads the successful 26526 Actions
artifact itself and requires the exact known candidate-source and manifest SHA-256 values before it
can transform anything.

Expected successful artifact
----------------------------
Artifact name:
  photon-26527-final-mgc-zoom-dng-v1

Expected APK:
  IrisCamera-0.9726527-26527-final-mgc-zoom-dng-debug.apk

The artifact also contains the proof bundle, deterministic 26527 candidate-source archive, manifest,
forward/rollback patches, temporal audit, DNG/SubIFD proof, shader preflight, postbuild validation,
and provenance needed for 26528.

Important hard-stop behavior
----------------------------
The build stops before version change / Gradle if any predecessor hash, owner hash, transform output,
rollback patch, changed-file allowlist, shader, native syntax, DNG SubIFD test, or frozen invariant
does not match. Repository app/src is never treated as the predecessor runtime authority.

What 26527 changes
------------------
- Final active-Iris Spatial/MGC alignment + rejection-domain parity correction.
- Acceptance telemetry for the temporal merge path.
- Sequential optical-anchor zoom handoff with requested/displayed separation and reverse hysteresis.
- Pinch takes exclusive gesture ownership so it cannot end as a focus tap.
- Adaptive direct-physical / logical+physical / logical-only Camera2 routing with immutable session proof.
- Covered camera restart with exact-route reveal and 1.6 second fail-safe.
- Still stacked-DNG reduced RGB SubIFD preview (tag 330) while preserving full Bayer RAW and 26525 crop.
- RawVideo preview remains disabled by default.

On-device test priorities
-------------------------
1. Static fine detail and moving cars/people/leaves: look for block seams, step-ladders, clumps, ghosting.
2. Fast 1x -> 3.2x pinch: old lens must not display the far requested zoom while waiting for handoff.
3. Continue across multiple optical anchors and reverse direction: adjacent handoffs and hysteresis should be stable.
4. Pinch while previewing/recording: no stray focus circle at gesture end.
5. Lens transition: curtain covers restart, reveals only after route proof, never remains black > fail-safe.
6. Stacked DNG in Google Photos/compatible viewer: preview should appear while the full Bayer RAW stays intact.
7. Capture logs: inspect logical/physical topology and requested/actual metadata, especially camera ID5.

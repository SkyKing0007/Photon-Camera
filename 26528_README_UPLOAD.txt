PHOTON 26528 OPTICAL HANDOFF UI-THREAD REPAIR

This is a one-owner repair for the 26527 optical-boundary crash.
Do NOT modify app/src manually. The workflow recovers the exact successful 26527 Actions candidate and transforms that artifact.

Extract this handoff into the repository root on:
  experimental-clean-photon-rebuild
Preserve:
  .github/workflows/build-26528-optical-handoff-ui-thread.yml

Commit suggestion:
  26528: restore UI-thread optical handoff restart

Expected workflow:
  Build 26528 Optical Handoff UI Thread
Expected artifact:
  photon-26528-optical-handoff-ui-thread-v1
Expected APK:
  IrisCamera-0.9726528-26528-optical-handoff-ui-thread-debug.apk

Key correction:
  remove 26527 processExecutor dispatch of restartCamera() behind the curtain;
  marshal restartCamera() through Activity.runOnUiThread instead.

Frozen:
  all MGC/Spatial/DNG image-quality math, zoom thresholds, routing policy, requested/displayed zoom behavior, pinch ownership, and curtain/fail-safe behavior.

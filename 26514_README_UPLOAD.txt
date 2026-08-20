Photon Camera / Iris 26514 handoff
=================================

Target branch:
  experimental-clean-photon-rebuild

Verified tested base handoff commit:
  3601f39b8e4d7ebd4776edbcae6e56f4514eea54

Verified required backup:
  backup-26513-success-before-26514-20260819
  -> 3601f39b8e4d7ebd4776edbcae6e56f4514eea54

Build/version:
  0.9726514 / 26514

Scope:
- Preserve exact tested 26513 reconstruction, Spatial 1.10/0.40, highlight/tone constants,
  UHDR geometry, JPEG 4:4:4/output completion and no-sharpening policy.
- Motion-only Iris UI replaces misleading legacy Motion controls.
- Existing Noise Reduction becomes the real master for post-stack MGC full-resolution denoise.
- Luma Denoise: 0.0..2.0 in exact 0.1 steps; default 1.0.
- Chroma Denoise: 0.0..2.0 in exact 0.1 steps; default 1.0.
- Custom Noise Model + SAF Import Noise Model (.c), original filename shown in the title.
- Imported .c is parsed before mutation, capped at 1 MiB, then copied to private app storage.
- Camera2 mode requires valid per-frame Camera2 SENSOR_NOISE_PROFILE on every supplied Motion frame.
- Custom mode evaluates the selected .c at each frame's actual ISO.
- No base-frame, Pixel, or cross-source noise fallback is allowed.
- Per-lens legacy JSON defaults prevent new settings/profile leakage across lenses.
- New Iris Exposure: -1.0..+1.0 EV, 0.1 step, default 0.0.
- New Iris Shadows: -1.0..+1.0, 0.1 step, default 0.0; negative opens, positive deepens.
- New Iris Contrast: -1.0..+1.0, 0.1 step, default 0.0.
- Exposure -> Shadows -> Contrast is inserted only when non-neutral, after Camera2 color and before
  the unchanged MotionV2Render common SDR/UHDR source.
- Old Photon exposure compensation is forced neutral for Motion capture only.
- Old Motion Sharpness, Saturation, Contrast, Exposure Compensation, Noise Reduction Strength,
  Noise Merge Strength, Shadows and Compressor rows are hidden in Motion only. Non-Motion modes
  retain their legacy settings.

Neutral regression condition:
  Noise Reduction ON
  Custom Noise Model OFF
  Luma 1.0
  Chroma 1.0
  Exposure 0.0
  Shadows 0.0
  Contrast 0.0
must preserve the tested 26513 image math/path (apart from strict validation that would now fail
rather than silently use a noise fallback).

Do not edit runtime source manually. Upload these handoff files and the workflow, commit them to the
experimental branch, and let GitHub Actions reconstruct tested 26513, create the rollback/audit
patch before 26514 writes, validate the exact delta, increment the version, and build one APK.

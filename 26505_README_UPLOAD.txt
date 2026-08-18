PHOTON CAMERA 26505 — PHYSICAL BRACKET + LOW-SUPPORT RCD/PPG FOUNDATION
Created: 2026-08-18

PURPOSE
26505 is the deterministic bjzhou-consistency foundation selected after the tested
26504 indoor HDR set and the windy outdoor zippering set. It does NOT add learned
HDR yet. It fixes the two physical inputs that a learned fusion model would otherwise
be forced to inherit:
  1) no reliable Long-A shadow observation in difficult HDR scenes;
  2) false-color zipper/checker reconstruction where local temporal support collapses.

REQUIRED BRANCH
  experimental-clean-photon-rebuild

CURRENT TESTED/HANDOFF COMMIT
  299731b9447a4d0cd69f0c2e521216bf307724b3
  26504: integrated quad-coherent HDR strong-clipping correction

CANONICAL TESTED RUNTIME BASE
  6118984523296945a0910e55ddaa4d3126184059
  (runtime remains tested 26502 in Git; Actions reconstructs 26503 + 26504 + 26505)

REQUIRED BACKUP BEFORE THIS ARCHITECTURAL CHANGE
  backup-26504-tested-before-26505-20260818
  -> 299731b9447a4d0cd69f0c2e521216bf307724b3

The build and workflow intentionally FAIL before any runtime transform if that exact
backup branch is missing or points somewhere else.

UPLOAD AT REPOSITORY ROOT
  apply_26505_bjzhou_consistency.py
  validate_26505_bjzhou_consistency.py
  build_26505_physical_bracket_low_support_rcd.sh
  26505_README_UPLOAD.txt
  26505_HANDOFF_HASHES.sha256

UPLOAD UNDER .github/workflows/
  build-26505-physical-bracket-low-support-rcd.yml

DO NOT MODIFY app/src/main OR app/version.properties MANUALLY.
DO NOT MODIFY OR PUSH dev.
DO NOT PROMOTE THE GENERATED CANDIDATE SOURCE AFTER BUILD.

READY-TO-PASTE COMMIT MESSAGE
26505: add physical long bracket and low-support RCD fallback

EXPECTED ACTIONS ARTIFACT
  photon-26505-physical-bracket-low-support-rcd

EXPECTED APK
  IrisCamera-0.9726505-26505-physical-bracket-low-support-rcd-debug.apk

WHAT 26505 CHANGES
A. PHYSICAL LONG-A
- Preserves the equal-exposure Wronski normal stack.
- Preserves the tested separate Short-A highlight observation.
- Requests one separate RAW-only Long-A at roughly +2.5 EV exposure energy.
- Prefers shutter up to ~10 ms (or the already-longer base shutter), then ISO.
- Uses actual CaptureResult exposure time x ISO as radiometric authority.
- Uses exact CaptureStarted/result/Image sensor timestamp ownership.
- Long-A never enters MotionBatch.frames / normal Wronski accumulation.
- The old opportunistic brighter-ZSL scavenger cannot pre-empt intentional Long-A.
- Existing Shadow-A alignment, correspondence, saturation and local-SNR gates remain.
- Host acceptance is widened to include a ~5.66x exposure-energy Long-A.
- Maximum Long-A semantic blend remains bounded at 0.35.

B. LOW-LOCAL-SUPPORT CFA RECONSTRUCTION
- Adds one GPU-only edge-directed PPG/RCD-derived reconstruction from the immutable
  Wronski reference CFA.
- At <=1.5 effective local frames, this reference reconstruction owns RGB.
- Between 1.5 and 3.5 frames, ownership transitions smoothly.
- At >=3.5 effective local frames, the current multiframe semantic RGB is unchanged.
- This is NOT a whole-photo single-frame fallback and NOT an unaligned-frame fallback.
- 26504 quad-coherent strong-highlight neutral/clipping authority still runs afterward.

WHAT 26505 PRESERVES
- Wronski normal-frame alignment/merge architecture.
- 26503 conservative Short-A boundary observability.
- 26504 quad-coherent highlight trust and post-LSC chroma exhaustion.
- 26504 actual-noise/local-support chroma sanity.
- 26504 bounded display-gain architecture.
- HAL/system AE live preview authority.
- Camera2 color stage.
- tested 26502 EXIF normalization.
- UltraHDR geometry.
- sharpening OFF and old broad ESD/ABLC/Photon denoise OFF.
- no full-resolution diagnostic readbacks restored.

WHAT 26505 DOES NOT DO
- does not implement LuckyHDR or any learned model yet.
- does not hallucinate/generate RGB.
- does not copy bjzhou's complete MGC stacker or 600KB RAW processor.
- does not replace Wronski.
- does not add PyramidAlignment.
- does not add a whole-photo single-frame fallback.
- does not modify dev.
- does not promote candidate source.

BUILD SAFETY
The same guarded workflow reconstructs tested 26502, applies the proven 26503 seed,
applies and validates 26504, then applies and validates 26505. Version remains
0.9726502 / 26502 until PRE-BUILD SAFETY PROOF PASSED. The same command block then
bumps to 0.9726505 / 26505 and runs Gradle. Exactly one APK is required.

ON-DEVICE TEST TARGETS
- repeat the large cafeteria/office-window scenes;
- windy foliage/leaf-sky edges;
- cars, pavement, white buildings and railings;
- dark interior + bright exterior;
- fluorescent/highlight clipping;
- processing time.

LOGS TO CHECK
- IRIS_26505_PHYSICAL_LONG_BRACKET
- IRIS_26505_LONG_ACTUAL_ACCEPTED
- IRIS_26505_LONG_RAW_EXACT_CALLBACK_OWNERSHIP
- IRIS_26498_V13_SHADOW_AUX_RESULT
- IRIS_26505_LOW_SUPPORT_PPG_FALLBACK
- IRIS_26487_PROCESSING_BUDGET
- IRIS_26496_SHORT_FAILURE_REASONS
- IRIS_26486_EXPOSURE_GROUP_SPAN

SUCCESS STANDARD
Difficult HDR scenes should use real Short/Normal/Long captured evidence rather than
asking late tone logic to invent dynamic range. Moving fine detail with collapsed local
support may become less detailed, but must stop producing colored Bayer-like zippering.
Unrecoverable highlights may clip cleanly; continuous surfaces must remain coherent.

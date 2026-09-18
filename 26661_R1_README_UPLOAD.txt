PHOTON 26661 R1 — Google highlight-safe ZSL reference exposure

Runtime authority: exact successful 26660 Actions compiled candidate
  commit c237df22b3f4eadf9aec7fd95866e94ca63b25af
  run 35273113260
  artifact 10519143387 photon-26660-r1-object-color-gamma
  artifact SHA-256 00c66aaa47d0e682d5513a76781a953abd3d25247df59dcbfd854ea8f091bf33
  compiled-candidate TAR SHA-256 3351f34e99d0e0b62fdcf87e64314830111f62c6f8173152d17f1b7f599db4f9

Verification-mechanics authority: exact successful 26660 build procedure. Functional build mechanics delta: ZERO.
Backup: NONE, by request.
Runtime changed-file allowlist: exactly 8, zero additions.
Version: 0.9726661 / 26661.

Runtime correction:
- Motion still uses no post-shutter HIGHLIGHT_SHORT repair frame.
- HAL AE remains ON; fresh sensor-normalized RAW evidence may add only a bounded negative compensation to the equal-exposure ZSL reference group when HDR/highlight pressure is proven.
- The reference-protection solve removes its own previously applied EV from the RAW guide before computing the next target, uses asymmetric hysteresis/cadence, and never revives the retired positive AE loops.
- The existing SHADOW_LONG frame remains extra shadow/SNR evidence in the same Sabre/Wronski accumulator and never becomes a global brightness scalar.
- Each reference frame carries the exact applied protection EV into presentation metadata.
- The live preview restores only that known capture bias in linear-light display space so highlight-safe acquisition does not simply darken the viewfinder.
- The final viewfinder-matching solve adds only the residual EV not already recovered by its existing 65% preview/candidate solve, preventing double compensation.
- 26660 render.glsl, gainmap.glsl, object-color gamma, UHDR target/pop, RGB reconstruction, color, local tone, denoise, Night, DNG, SR and HEIC publication remain protected.

Upload every path listed in R1_26661_UPLOAD_PATHS.txt at repository root on branch experimental-clean-photon-rebuild, preserving directories. Do not upload an APK and do not commit live app/src replacements; runtime source is carried only inside handoff_payload_26661 and reconstructed by Actions from the exact successful 26660 compiled artifact.

Suggested commit message:
26661 R1: adaptive highlight-safe ZSL reference exposure

Actions is authority for pinned real GLSL, Kotlin/Java, both NDK ABIs, full assembleDebug, exactly-one-APK proof and post-build invariance.

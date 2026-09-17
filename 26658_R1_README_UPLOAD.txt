PHOTON 26658 R1 — Google-style HDR+ Bracketing Role Conversion from 26653

Runtime authority: exact successful 26653 Actions compiled candidate
  commit 5031e403553928e6e9411789a2ff7deab01390ed
  run 35170004987
  artifact 10476700363 photon-26653-r1-final-highlight-tone-fine-structure
  artifact SHA-256 2cd27a12ca2339fa4e1df02b661b6f7836487deb2d9576a353d18fec8f1e2bce
  compiled-candidate TAR SHA-256 aa2febedc278945e13055cadc7fde11c8637de3bfb8ea04e47908edbd70bf369

Verification-mechanics authority: exact successful 26653 build procedure.
Functional compiler/build sequence delta: ZERO. Identity/authority/scope/semantic validation changed only.
Backup: backup-current-clean-photon-before-26653-google-hdr-bracketing at a4d4a9387cd6e4aba91fe86dbdd615e56114048b.
Runtime changed-file allowlist: exactly 6, zero additions.
Version: 0.9726658 / 26658.

Runtime architecture:
- Existing equal-exposure pre-shutter ZSL group is the structural/reference exposure group.
- Retire Motion's second post-NORMAL HIGHLIGHT_SHORT repair capture.
- Existing +EV SHADOW_LONG becomes legitimate Motion common-Sabre shadow/SNR evidence.
- Auxiliary LONG is shutter-first up to ~1/15 s and ISO-only pseudo-LONG is rejected.
- LONG retains existing alignment, motion rejection, exposure normalization and source-clipping rejection.
- Motion preserves extended HDR through VGN even when LONG is admitted.
- Stacked DNG and true-2x/SR remain NORMAL/ZSL-only; LONG cannot become DNG or high-frequency SR evidence.
- 26653 RGB reconstruction, color, edge-artifact protection, denoise and tone/render owners are byte-identical unless listed in the 6-path allowlist.
- Night architecture remains separate and retains its prior branch behavior.
- Minimal runtime proof logs post-source-clipping LONG nonzero weight without changing the production accumulator.

Upload every path listed in R1_26658_UPLOAD_PATHS.txt at repository root on branch experimental-clean-photon-rebuild, preserving directories. Do not upload an APK and do not manually replace live app/src; runtime source is carried only inside handoff_payload_26658 and reconstructed by Actions from the exact successful 26653 artifact.

Suggested commit message:
26658 R1: Google-style HDR bracketing roles from 26653

Actions remains authority for pinned real GLSL, Kotlin/Java, both NDK ABIs, full assembleDebug, exactly-one-APK proof and post-build invariance.

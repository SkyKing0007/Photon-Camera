PHOTON/IRIS 26643 R1 REPAIR — ANDROID-16 AOSP HEIC ULTRA-HDR CONFORMANCE + QUICK/LENS/MANUAL UI CLEANUP

Runtime authority:
  successful 26642 R1 commit 23ef05f61020cfd0ce412ef7ecb0bdc1064f99ba
  Actions run 34930671416
  artifact 10381088303
  artifact SHA-256 a475b50c17f1d2d4cd7da8dc0757089400335bc95a8e6a2a267bd067e667df61
  deterministic candidate TAR SHA-256 8c7fbbc120ca3150e19d98c6b2e7c6244204611482bcb638f2163ec329c63a3c

Verification-mechanics authority:
  exact successful 26642 implementation (build-script blob 2b7a9f4caeb6fba66dbf3880b7d399acb01af256; workflow blob e9df8c2f964fb4bd839885f63241187d83baf6d1), inheriting successful 26641 and preserving the successful 26639 compiler/build/patch/PRE-BUILD/assemble/postbuild ordering.

Target: 0.9726643 / 26643
Repair authority: failed 26643 R1 commit 8138cfe871acec20d4a7c02dd63e83b1616ef64c / Actions run 34987275178. The failure was deterministic: the local AOSP-contract patch targeted newer libheif layouts (context.cc and newer Box_ipma signature) instead of the pinned libheif 4a3f74bc + Google/libultrahdr v2.0.0 PR1503 layout.
Backup: none created/requested. 26643 is a localized HEIC-publication conformance + UI cleanup change.

Runtime changes: exactly 10 paths: 9 modified + 1 added. See R1_26643_RUNTIME_CHANGED_PATHS.txt and R1_26643_ADDED_PATHS_MUST_BE_ABSENT.txt.
Infrastructure changes: compiler/build ordering remains exact successful 26642. Repair-only proof delta: accept exactly one repair commit on failed 8138cfe/run 34987275178, and permanently guard the pinned-v2 PR1503 patch target/layout before native configure. Workflow is unchanged.

Implementation owners:
  A) HEIC Android-16 AOSP conformance: retain the successful 26642 matched SDR/HDR gain map, half-linear-resolution Motion gain map, and ISO 21496-1 metadata bytes. Make the HEIF publication layer internally consistent with Android 16 HeicCompositeStream/MPEG4Writer: base/tmap Display-P3+sRGB+unspecified matrix+full range, gain unspecified/full, no parallel base ICC, visible gain item, essential IPMA properties, HEIC mif1/heic/tmap brands, and no explicit requested MediaCodec color-aspect keys.
  B) Quick gear UI: remove RAW and Battery Saver rows (Exposure Bracketing remains removed) and allow remaining rows to reflow naturally. Replace selected yellow circle/background treatment with yellow icon-glyph tint only; unselected icons remain white.
  C) Lens/manual UI: remove the selected lens circle and color only the selected lens text yellow; remove the manual chevron pill/border/elevation and match the 35dp/13sp lens-label visual scale.

Frozen successful 26642 behavior:
  matched SDR/HDR UHDR quotient, half-resolution Motion gain map and measured range, shared GL, SHORT/Sabre, color/denoise/Local-Laplacian/highlight, capture routing, DNG, Prefix Name, visible Photo/internal Motion routing, settings cleanup and all 257 asset shaders remain byte-identical unless explicitly listed in the 10-path runtime allowlist.

Upload workflow:
  Extract this ZIP locally.
  In vscode.dev on branch experimental-clean-photon-rebuild at failed 26643 commit 8138cfe..., upload/replace every path in this repair ZIP.
  Because the original 41-file handoff is already committed, Source Control will show only the repair files whose bytes changed; the workflow verifies the cumulative diff from successful 26642 is still exactly the sealed 41-path upload scope and contains no live app/ path.
  Commit the repair once and push. Do not manually edit runtime source.
  The 26643 workflow reconstructs from the successful 26642 Actions artifact and runs the exact inherited guarded compiler/build sequence.

Before Actions, this handoff is PREPARED / UPLOAD-READY only. Real Kotlin/Java, both NDK ABIs, full assemble, one-APK proof and post-build invariance become authoritative only after the 26643 Actions run succeeds. Real GLSL is not applicable because all 257 asset shaders are byte-identical to successful 26642.

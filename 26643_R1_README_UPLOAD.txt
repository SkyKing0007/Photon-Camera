PHOTON/IRIS 26643 R1 — ANDROID-16 AOSP HEIC ULTRA-HDR CONFORMANCE + QUICK/LENS/MANUAL UI CLEANUP

Runtime authority:
  successful 26642 R1 commit 23ef05f61020cfd0ce412ef7ecb0bdc1064f99ba
  Actions run 34930671416
  artifact 10381088303
  artifact SHA-256 a475b50c17f1d2d4cd7da8dc0757089400335bc95a8e6a2a267bd067e667df61
  deterministic candidate TAR SHA-256 8c7fbbc120ca3150e19d98c6b2e7c6244204611482bcb638f2163ec329c63a3c

Verification-mechanics authority:
  exact successful 26642 implementation (build-script blob 2b7a9f4caeb6fba66dbf3880b7d399acb01af256; workflow blob e9df8c2f964fb4bd839885f63241187d83baf6d1), inheriting successful 26641 and preserving the successful 26639 compiler/build/patch/PRE-BUILD/assemble/postbuild ordering.

Target: 0.9726643 / 26643
Backup: none created/requested. 26643 is a localized HEIC-publication conformance + UI cleanup change.

Runtime changes: exactly 10 paths: 9 modified + 1 added. See R1_26643_RUNTIME_CHANGED_PATHS.txt and R1_26643_ADDED_PATHS_MUST_BE_ABSENT.txt.
Infrastructure changes: 26643 identity/authority/scope/regressions and 0-GLSL applicability only, retaining the successful 26642 added-path cleanup proof. Compiler/build order is unchanged from successful 26642.

Implementation owners:
  A) HEIC Android-16 AOSP conformance: retain the successful 26642 matched SDR/HDR gain map, half-linear-resolution Motion gain map, and ISO 21496-1 metadata bytes. Make the HEIF publication layer internally consistent with Android 16 HeicCompositeStream/MPEG4Writer: base/tmap Display-P3+sRGB+unspecified matrix+full range, gain unspecified/full, no parallel base ICC, visible gain item, essential IPMA properties, HEIC mif1/heic/tmap brands, and no explicit requested MediaCodec color-aspect keys.
  B) Quick gear UI: remove RAW and Battery Saver rows (Exposure Bracketing remains removed) and allow remaining rows to reflow naturally. Replace selected yellow circle/background treatment with yellow icon-glyph tint only; unselected icons remain white.
  C) Lens/manual UI: remove the selected lens circle and color only the selected lens text yellow; remove the manual chevron pill/border/elevation and match the 35dp/13sp lens-label visual scale.

Frozen successful 26642 behavior:
  matched SDR/HDR UHDR quotient, half-resolution Motion gain map and measured range, shared GL, SHORT/Sabre, color/denoise/Local-Laplacian/highlight, capture routing, DNG, Prefix Name, visible Photo/internal Motion routing, settings cleanup and all 257 asset shaders remain byte-identical unless explicitly listed in the 10-path runtime allowlist.

Upload workflow:
  Extract this ZIP locally.
  In vscode.dev on branch experimental-clean-photon-rebuild, upload/replace every path listed in R1_26643_UPLOAD_PATHS.txt exactly.
  Confirm Source Control shows exactly that upload scope and no live app/ path.
  Commit once and push. Do not manually edit runtime source.
  The 26643 workflow reconstructs from the successful 26642 Actions artifact and runs the exact inherited guarded compiler/build sequence.

Before Actions, this handoff is PREPARED / UPLOAD-READY only. Real Kotlin/Java, both NDK ABIs, full assemble, one-APK proof and post-build invariance become authoritative only after the 26643 Actions run succeeds. Real GLSL is not applicable because all 257 asset shaders are byte-identical to successful 26642.

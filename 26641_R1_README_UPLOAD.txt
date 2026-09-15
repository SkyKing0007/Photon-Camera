PHOTON/IRIS 26641 R1 — TRUE UHDR + HEIC COLOR SIGNALING + SHARED-GL CORRECTNESS + BOUNDED GAINMAP PERFORMANCE

Runtime authority:
  successful 26640 R1 commit 29b5a38277fc2584aa980df8410d5936e2d6bb55
  Actions run 34917470763
  artifact 10376279662
  artifact SHA-256 6b9e8bcaca965af1aba99593508e53870241ae16f306ac1c36be55fbdb1cda4e
  deterministic candidate TAR SHA-256 9518f2c3da0dd9136e55dd031e3138fbedd3a5469f077411425ec3d8f3fb8a39

Verification-mechanics authority:
  exact successful 26639 compiler/build/patch/PRE-BUILD/assemble/postbuild procedure, inherited through successful 26640.
  Build-script authority blob: a5870d5776c05b6ec134cc1da50da2c835770419
  Workflow authority blob: 4fc781824f9ecf38291575e4536a361560141bf1

Target: 0.9726641 / 26641
Backup:
  backup-26640-pre-26641-uhdr-heic-shared-gl-performance
  verified at exact successful 26640 commit 29b5a38277fc2584aa980df8410d5936e2d6bb55 before source write.

Runtime changes: exactly 5 files, 0 additions/removals. See R1_26641_RUNTIME_CHANGED_PATHS.txt.
Infrastructure: 26641 handoff identity/authority/scope/regression applicability only; compiler/build ordering is unchanged from successful 26639.

Implementation owners:
  A) Motion UHDR restores the full matched SDR-compressed linear-luminance delta exactly once, using the same canonical extended-linear master and 1/64 quotient offsets. The 26640 squared-compression attenuation is retired. No fixed luma threshold, semantic detector, gain dilation, or RGB gain-map authority.
  B) HEIC keeps the protected libheif ISO-21496/tmap container and the same gain map as JPG. Hardware HEVC now explicitly signals Android-16-style base Display-P3/sRGB/full-range and gain-map unspecified/unspecified/full-range color aspects, with output-format logging for device proof.
  C) Shared GL no longer interprets texture object names as texture units or fixed tracking slots. Ownership is dynamic and generation-safe; constructors preserve the caller's texture binding; framebuffer objects are deleted through glDeleteFramebuffers.
  D) Motion gain maps use half linear resolution. HDR and SDR are filtered in linear light before division; the completed gain field is never blurred/dilated. Night remains on its inherited independent 1/4-resolution path. Timing telemetry isolates draw/readback/scan/bitmap cost.

Frozen behavior:
  successful 26640 SHORT/local-motion correction is byte-identical;
  successful 26639 color/shadow/detail/local-laplacian/highlight owners are protected;
  Sabre, alignment, demosaic, denoise, capture routing, DNG, native/vendor, and HEIC libheif/JNI container bytes are unchanged.

Upload workflow:
  Extract this ZIP locally.
  In vscode.dev on branch experimental-clean-photon-rebuild, upload/replace every path listed in R1_26641_UPLOAD_PATHS.txt exactly.
  Confirm Source Control shows exactly that upload scope and no live app/ path.
  Commit once and push. Do not manually edit runtime source.
  The 26641 workflow reconstructs from the successful 26640 Actions artifact and runs the same guarded compiler/build sequence as successful 26639/26640.

Before Actions, this handoff is PREPARED / UPLOAD-READY only. Real glslang 16.5.0, Kotlin, Java, both NDK ABIs, full assemble, one-APK proof, and post-build invariance become authoritative only after the 26641 Actions run succeeds.

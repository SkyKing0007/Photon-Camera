PHOTON 26640 R1 — LOCAL-MOTION-SAFE SHORT + MATCHED-INTENT UHDR

Runtime authority:
  successful 26639 R1 commit 18861d3d4885cd66cca7207cf1134f8e081c475b
  Actions run 34902211748
  artifact 10371172131
  artifact SHA-256 3b92946201952ae01cc542abe25d681faa0c90561d1071cf7e7c8682f86d525f
  deterministic candidate TAR SHA-256 b8b022227ed809ce2fbabf76664a8ff4272bc25a0c8b9a308a80589db28d8668

Verification-mechanics authority:
  exact successful 26639 procedure, inherited from successful 26638.
  Build-script authority blob: a5870d5776c05b6ec134cc1da50da2c835770419
  Workflow authority blob: 4fc781824f9ecf38291575e4536a361560141bf1

Target: 0.9726640 / 26640
Backup: NONE, per user instruction.

Runtime changes: exactly 5 files, 0 additions/removals. See R1_26640_RUNTIME_CHANGED_PATHS.txt.
Infrastructure: 26640 handoff identity/authority/scope/regression files only; compiler/build ordering is unchanged from successful 26639.

Implementation owners:
  A) live Sabre SHORT component propagation now requires destination-local multi-phase post-source-clip support before trust can propagate. Strong stationary boundary seed remains; SHORT is not globally disabled.
  B) Motion UHDR retires the 26639 fixed 0.65/0.85 pointwise threshold. Gain is a scalar linear-luminance quotient from spatially matched SDR/HDR intents of the same canonical extended-linear Motion master, with 1/64 offsets. No semantic detector, no gain dilation, no RGB gain-map color owner. Motion metadata follows the measured stored gain range.

Upload workflow:
  Extract this ZIP locally.
  In vscode.dev on branch experimental-clean-photon-rebuild, upload/replace every path listed in R1_26640_UPLOAD_PATHS.txt exactly.
  Confirm Source Control shows exactly that upload scope and no live app/ path.
  Commit once and push. Do not manually edit runtime source.
  The 26640 workflow reconstructs from the successful 26639 Actions artifact and runs the same guarded compiler/build sequence as 26639.

Before Actions, this handoff is PREPARED / UPLOAD-READY only. Changed GLSL/Kotlin/Java real compiler proof and full Android assemble become authoritative only after the 26640 Actions run succeeds.

Photon 26596 V1 Phase-Complete SHORT + UHDR + SR handoff

Runtime authority: successful 26595 commit 7fd605dbbf02c394432108fd259ace19f0d33b93, Actions run 33900804690, job 101114167335, artifact 9947679988.
Verification mechanics: exact successful 26595 implementation with successful 26593 compiler/build ordering preserved.
Backup: NONE, per user request.

Runtime scope is exactly 8 files listed in V1_26596_RUNTIME_CHANGED_PATHS.txt.
The handoff reconstructs from the exact successful 26595 compiled candidate and overlays only those sealed payload bytes.

26596 corrects two device-proven failures: (1) 26595 SHORT contributed 12,213 pixels but exact sensor loss in only one CFA phase was still excluded; (2) Motion UHDR could encode gain up to 8x while declaring full HDR at 1.6033x. 26596 admits exact one-or-more-phase sensor loss only with same-phase SHORT proof/headroom/flow coherence, and makes Motion UHDR display capacity equal the actual encoded gain peak. True-2x gain is capped to the same native content authority while keeping ratioMax as its encoding denominator.

Upload all files/folders in this ZIP to branch experimental-clean-photon-rebuild as one clean commit directly on 7fd605dbbf02c394432108fd259ace19f0d33b93. Do not upload APKs. GitHub Actions is authoritative for real GLSL/Kotlin/Java/NDK/full assemble proof.

Photon 26586 V1 — Viewfinder / Highlight Authority Split

RUNTIME AUTHORITY
- successful 26585 V1 commit 7201c93c1993a1a42c89744acce2f661adc5d09d
- Actions run 33710354236 / job 100508291920
- artifact 9876758467, SHA-256 aa95beb48d3cebfb1c5df959b7778cac043faf55bc78d96ac098b22d17349c8c
- compiled candidate tar SHA-256 fe80c7288b94e11194f28710f08f0a8c221d9e8c706e75fdbd1639b6b55e8f28

VERIFICATION-MECHANICS AUTHORITY
- exact successful 26585 V1 pre-handoff/build procedure, inheriting the proven 26567 authority-seeded sequence.
- no redesign of lineage, workflow, shader, compiler, patch, PRE-BUILD, assemble, or invariance order.

RUNTIME CHANGED-FILE ALLOWLIST
1. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java
2. app/version.properties

BEHAVIORAL CHANGE
- viewfinder/body exposure trials use successful-26584 structured meter authority (P90 / 0.965) rather than final P98 / 0.945 highlight headroom;
- final highlight authority remains successful-26585 P98 / 0.945 and is evaluated after displayGain is frozen;
- successful-26585 adaptive-color/pink-cyan-green safeguards, render, Sabre/VGN/SR, DNG/UHDR, Jin, Night and native GPU owners remain byte-frozen.

BACKUP
- none, per user instruction; deterministic rollback patch to successful 26585 is packaged.

UPLOAD / LINEAGE REQUIREMENT
The current branch contains failed 26586 handoff commits. To use the exact successful-26585 procedure, experimental-clean-photon-rebuild must first be reset so HEAD is exactly successful 26585 commit 7201c93c1993a1a42c89744acce2f661adc5d09d. Then extract this handoff into the repository root, commit the sealed handoff once, and push. Do not manually copy handoff_payload files into app/; Actions performs the authority-seeded runtime write.

Suggested commit message:
26586 V1: split viewfinder exposure metering from highlight headroom

Before Actions success this handoff is PREPARED / UPLOAD-READY only.

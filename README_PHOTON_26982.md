# Photon 26982 — 3-stage guarded handoff

Upload **STAGE_1_UPLOAD.zip** contents at repository root, commit; then **STAGE_2_WORKFLOW.zip** contents, commit; then **STAGE_3_TRIGGER.zip** contents last, commit. Never edit the sealed trigger. All stages target `experimental-clean-photon-rebuild` only; never push to dev or push APKs. The workflow fetches *actual successful 26981* Actions source and recompiles 26982 using inherited checks.

Experiment C: MGC sharpening bands 0/1/2 0–2 in 0.1 steps, per physical lens, frozen with C shutter session; default 1.0 retains original donor curves. GuidedUpsample and standalone both receive capture-local tuning. No A/B pipeline changes.

B/Super Res ON: low-risk partial GPU contention mitigation (event-driven preview, PixelCopy histogram pause during active B/ON). Direct ISP SurfaceView handoff was **not** enabled: the successful Camera2 session does not provide a proven second compatible display surface or transform; unsafe reconfiguration would jeopardize RAW. Performance and preview appearance require device testing.

Local SHA/scope/patch/host proofs do **not** constitute an Android build. Only Actions success plus published artifact is BUILD-PROVEN. No APK is included in this handoff.

# 26545 V1.2 Sabre ownership-isolation handoff

Target branch: `experimental-clean-photon-rebuild`

This is a corrective revision of 0.9726545 / 26545. It reconstructs the exact successful 26544 runtime authority in Actions, applies the full audited 26545 V1.2 runtime patch, then runs real glslang 16.5.0, the real project Kotlin compiler, the real project Java compiler, and full Android assemble.

V1.2 specifically fixes the tested Sabre crash caused by a Spatial-only highlight reliability node leaking into the Sabre post graph. Routing now uses a durable reconstruction owner (`SPATIAL_RGB` or `SABRE`) with defense-in-depth assertions at the bridge, Hdrx boundary, PostPipeline graph, and Spatial-only nodes.

No backup branch is required for this contained corrective revision. Do not edit or push `dev`. Replace the prior 26545 handoff files at repository root with this package and commit them to `experimental-clean-photon-rebuild`.

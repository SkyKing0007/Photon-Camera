26519 — Per-Lens Viewfinder Match Strength
=============================================

Base
----
Exact successful 26518 source artifact at commit:
18582e3ca2c9a7fdaf5bb5c816036d215e887f95

No new backup is required for this build, per user request.

Image-quality invariant
-----------------------
26518 fixed the broad pink/green bright-edge artifact. 26519 must keep the released c4ff Spatial RGB
owner, its quarter-resolution guide/alignment behavior, and the narrow 26518 result-SNR ABI adapter
byte-for-byte unchanged.

Brightness change
-----------------
26519 restores the exact 26516 viewfinder metering/solver relationship that produced the known
+1.764 EV reference result, then scales only that solved EV by a per-lens response percentage:

    appliedEV = raw26516SolvedEV * (matchStrengthPercent / 100)

Default: 65%
Reference calibration: +1.764 EV * 0.65 = +1.1466 EV

This is NOT a fixed +1.15 EV offset and NOT a global +1.0/+1.2 EV clamp. Each scene still produces
its own raw adaptive solve before response scaling.

Slider
------
Photo Settings -> Motion viewfinder match strength
Range: 0..100%
Default: 65%
100% = full 26516 measured EV response
0% = no automatic viewfinder-match EV response

The key is a normal Photon preference (not pref_motion_iq_ / pref_tunable_), so when Photon's
existing "Save per lens settings" option is enabled, it is saved/restored separately for each
camera ID using the existing per-lens JSON machinery.

Frozen
------
Camera2 AE/shutter/ISO, Short, Long, c4ff stacker/shaders/fusion, 26518 SNR ABI adapter, bridge,
color transform, display shader, render/UHDR, and manual Iris Exposure.

Expected artifact
-----------------
photon-26519-per-lens-viewfinder-response-v1
IrisCamera-0.9726519-26519-per-lens-viewfinder-response-debug.apk

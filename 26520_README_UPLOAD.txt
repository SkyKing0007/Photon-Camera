26520 — ZSL Shared-Batch Stacked DNG + Explicit One-Normal Capture

Base: 9b59a27235747733bacdde68bf6a888ebffefa18
Backup: backup-26519-before-26520-zsl-stacked-dng

Frame Count = 1
----------------
One admitted NORMAL RAW is now a valid Motion batch. Requests >=2 retain the two-normal
minimum, so this does not reintroduce silent single-frame fallback.

If a shutter-frozen RAW arrives before its exact SENSOR_TIMESTAMP TotalCaptureResult, 26520
allows 180 ms for metadata only. mMotionTopUpActive remains false, so new normal RAWs are
not admitted after shutter. Neighbor metadata is never borrowed.

JPEG HDR roles
--------------
Short, Long/shadow auxiliary, Bento and the full JPEG/UHDR path remain available with one
normal frame. They remain outside MotionBatch.frames.

Stacked DNG
-----------
The DNG uses the exact same admitted NORMAL frame population as the JPEG candidate.
Requested 15 / admitted 13 -> JPEG normals 13 and DNG stack frames 13.

No second alignment pass is added. The existing Wronski/Motion reconstruction already owns a
normal-only persistent Bayer numerator/denominator/support accumulator. 26520 taps its
one-time normalized Bayer result before Short/Long/Bento recovery, converts packed CFA back
to RAW16 sensor code using the reference black/white levels, and sends that to the existing
DNG writer.

DNG does NOT receive Short/Long/Bento, Spatial RGB/demosaic, lens shading, viewfinder/display
gain, tone mapping, JPEG denoise, sharpening or UltraHDR. Local rejection can make effective
per-pixel support lower than the admitted frame count; logs report both.

Frozen: released c4ff Spatial RGB pink-artifact fix, 26518 SNR ABI bridge, 26519 per-lens
Viewfinder Match Strength slider/default 65%, Camera2 AE/shutter/ISO, color/tone/UHDR.

Expected artifact: photon-26520-zsl-stacked-dng-v1
Expected APK: IrisCamera-0.9726520-26520-zsl-stacked-dng-debug.apk

V3 exact-26519 procedure correction
-----------------------------------
- The successful 26519 V2 Actions artifact is the sole runtime source authority.
- The downloaded 26519 source manifest is checked before any transform.
- The complete six-path transform is executed in memory against that exact artifact before candidate writes.
- Hdrx reconstruct-call discovery is source-format independent and requires exactly one semantic invocation.
- Repository app/src is never substituted for the tested 26519 artifact.
- No new runtime architecture change versus the original 26520 design.

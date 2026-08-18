PHOTON CAMERA 26504 — INTEGRATED HDR / STRONG-CLIPPING HANDOFF
Created: 2026-08-18

UPLOAD AT REPOSITORY ROOT:
  apply_26504_integrated.py
  validate_26504_integrated.py
  build_26504_integrated_hdr_strong_clipping.sh
  26504_README_UPLOAD.txt
  26504_HANDOFF_HASHES.sha256

UPLOAD UNDER .github/workflows/:
  build-26504-integrated-hdr-strong-clipping.yml

DO NOT MODIFY app/src/main OR app/version.properties MANUALLY.
DO NOT MODIFY OR PUSH dev.

Required branch:
  experimental-clean-photon-rebuild

Protected infrastructure base:
  1b8ac72772ac007410cc05c334ac84b10578b1fa

Canonical tested runtime:
  6118984523296945a0910e55ddaa4d3126184059

Required backup:
  backup-26503-v7-before-26504-20260818
  -> 1b8ac72772ac007410cc05c334ac84b10578b1fa

READY-TO-PASTE COMMIT MESSAGE:
26504: integrated quad-coherent HDR strong-clipping correction

EXPECTED ACTIONS ARTIFACT:
  photon-26504-integrated-hdr-strong-clipping

EXPECTED APK:
  IrisCamera-0.9726504-26504-integrated-hdr-strong-clipping-debug.apk

26504 DOES:
- exact 2x2 Bayer-quad highlight trust
- one packed-cell confidence expansion; no RGB blur
- incomplete-highlight chroma neutralization after lens shading
- actual Wronski/Camera2 noise + local support chroma sanity
- composition influence bounded to +/-0.25 EV around frozen capture-state anchor
- local effective-stack shadow permission
- conservative Short-A boundary observability preserved
- hue-preserving extended-range render direction preserved
- heavy full-resolution diagnostic readbacks disabled

26504 DOES NOT:
- change Wronski
- change capture/ZSL/HAL AE
- change Camera2 color transform
- change EXIF
- change UHDR geometry
- restore ESD/ABLC/old Photon denoise
- enable sharpening
- implement preview luminance readback/matching
- promote candidate source

Test on-device before any promotion.

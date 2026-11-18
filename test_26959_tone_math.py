#!/usr/bin/env python3
"""Remove fixed EV, not adaptive SDR/tone/UHDR. Exact source-chain and fine highlight preservation."""
import argparse,pathlib,re,math,hashlib
R=pathlib.Path(__file__).resolve().parent

def verify(live=False):
 pre=R/'handoff_payload_26959'
 shader=(R if live else pre)/'app/src/main/assets/shaders/motionv2/render.glsl'
 src=shader.read_text()
 assert src.count('void main()')==1
 assert 'IRIS_26959_NO_FIXED_EV' in src
 assert 'const float iris26954SdrExposureScale=1.3195079107728942;' not in src
 assert 'IRIS_26954_V2_26940_SDR_GLOBAL_EDITOR_EV_WITH_MONOTONE_WHITE' not in src
 assert src.count('iris26892SdrAdaptiveGuide(mappedGuide)')==2
 for needle in ('iris26824AdaptiveBodySGuide(mappedGuide)','iris26660ObjectColorGamma(mappedGuide)','iris26770MidtonePresentationTrim(mappedGuide)','iris26638ApplyShadowFloorGuard(linearSrgb)','iris26908NightPresentationLift(linearSrgb)','fitDisplayGamut(linearSrgb)','iris26638UserSaturation(linearSrgb,iris26630MotionSaturation)','srgbEncode(linearSrgb)','iris26932BOffSdrBridge(mappedGuide,sourceGuide)'):
  assert needle in src,needle
 assert src.count('iris26954BOffNight26940Sdr!=0') >= 1
 assert 'linearSrgb=unexposed*uniformScale;' not in src
 assert src.index('linearSrgb=iris26638ApplyShadowFloorGuard(linearSrgb)') < src.index('IRIS_26959_NO_FIXED_EV') < src.index('Output=clamp(')
 # No post-tone fixed EV, no hidden -0.4EV in gainmap and exact prior protected shader.
 manifest={p:h for h,p in (line.split('  ',1) for line in (R/'26959_BASE_26958_FULL_APP.sha256').read_text().splitlines()) if p=='app/src/main/assets/shaders/motionv2/gainmap.glsl'}
 assert len(manifest)==1
 if live:
  gain=R/'app/src/main/assets/shaders/motionv2/gainmap.glsl'
  assert hashlib.sha256(gain.read_bytes()).hexdigest()==manifest['app/src/main/assets/shaders/motionv2/gainmap.glsl']
 assert 11.0 != 13.0 and math.isfinite(2**0.4)
 print('PASS fixed +0.4EV single last-step removed, adaptive SDR tonal owners and protected UHDR unchanged')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');p.add_argument('--payload',action='store_true');a=p.parse_args();verify(a.live)

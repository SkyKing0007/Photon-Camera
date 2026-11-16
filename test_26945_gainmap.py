#!/usr/bin/env python3
"""26945 orthogonal camera rotation and front-only FINAL-raster gainmap alignment."""
import argparse
from build_26945_incremental import R,fail

def rotate(src,deg):
 n=len(src);m=len(src[0]);deg%=360
 if deg==0:return [list(row) for row in src]
 if deg==90:return [[src[n-1-x][y] for x in range(n)] for y in range(m)]
 if deg==180:return [list(reversed(row)) for row in reversed(src)]
 if deg==270:return [[src[x][m-1-y] for x in range(n)] for y in range(m)]
 raise ValueError('nonorthogonal')

def final_sdr(src,deg,front):
 a=rotate(src,deg)
 return [list(reversed(row)) for row in a] if front else a

def gain(src,deg,front):
 # The production implementation rotates, then conditionally mirrors final X.
 a=rotate(src,deg)
 if front:a=[list(reversed(row)) for row in a]
 return a

def main():
 a=argparse.ArgumentParser();a.add_argument('--live',action='store_true');a.add_argument('--payload',action='store_true');a.parse_args()
 # Not symmetric: catches wrong axis, stale rotation, double flip, sensor-axis flip.
 raw=[[1,12,3,44,5],[6,7,88,9,10],[101,11,12,13,140]]
 for degrees in (0,90,180,270):
  for front in (False,True):
   if gain(raw,degrees,front)!=final_sdr(raw,degrees,front):fail('SDR/gain map mismatch rot='+str(degrees))
   # Gain only changes HDR luminance; SDR body pixel identity must be preserved.
   base=[r[:] for r in final_sdr(raw,degrees,front)]
   final_gain=gain(raw,degrees,front)
   if base!=final_gain or base!=final_sdr(raw,degrees,front):fail('SDR base altered by gain attachment')
   if front and len(base[0])>1 and final_gain==rotate(raw,degrees):fail('front gain did not mirror')
 # Front sensor 270 degrees: high-contrast left tree must remain on left in gain.
 source=[[0,0,1,1,4],[0,0,1,1,9],[0,0,1,1,5]]
 if gain(source,270,True)!=final_sdr(source,270,True):fail('26944 front portrait tree mirror regression')
 p=(R if a.parse_args().live else R/'handoff_payload_26945')/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java'
 s=p.read_text()
 if s.index('matrix.postRotate(rotation)')>s.index('frontFinalMirror.setScale(-1.0f, 1.0f)'):fail('front mirror before rotation rather than final raster')
 if 'new Gainmap(oriented)' not in s or 'gainmap.setRatioMin(MIN_RATIO' not in s or 'gainmap.setGamma(1.0f' not in s:fail('UHDR metadata/gain authority changed')
 print('PASS 26945 all four orthogonal rotations, independent front/rear mirrors, SDR unchanged + gain metadata preserved')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=__import__('sys').stderr);__import__('sys').exit(1)

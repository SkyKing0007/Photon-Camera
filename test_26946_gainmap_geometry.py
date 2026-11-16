#!/usr/bin/env python3
"""Independent pixel-by-pixel GL shader oracle vs front Bitmap orthogonal transform.
Uses actual compiled 26945 GL shader byte receipt, all angles and 16:9 crops.
"""
import argparse,pathlib,re,sys
from build_26946_incremental import R,fail,scope,sha
SHADER='app/src/main/assets/shaders/addwatermark_rotate.glsl'
SHADER_SHA='494715ea9225367cc05f0dbd0df1bf3c3ca7eed9b6628fcd9bbc338d4dd240cb'  # successful 26945 actual compiled GL shader

def source_value(rows,x,y):return rows[y][x]

def gl_expected(rows,rotation,mirror,crop_width,crop_height):
 H=len(rows);W=len(rows[0]);bottom=H-crop_height
 out_w,out_h=(crop_width,crop_height) if rotation in (0,180) else (crop_height,crop_width)
 code={0:0,90:3,180:2,270:1}[rotation];result=[]
 for y in range(out_h):
  dest=[]
  for x in range(out_w):
   if code==0:sx=x;sy=H-1-y if mirror else bottom+y
   elif code==1:sx=W-1-y;sy=H-1-x if mirror else bottom+x
   elif code==2:sx=W-1-x;sy=bottom+y if mirror else H-1-y
   else:sx=y;sy=bottom+x if mirror else H-1-x
   dest.append(source_value(rows,sx,sy))
  result.append(dest)
 return result

def bitmap_model(rows,rotation,mirror,crop_width,crop_height):
 H=len(rows);W=len(rows[0]);top=H-crop_height
 left=(W-crop_width) if rotation in (180,270) and mirror else 0
 # No crop is applied to rear: front is the only target of this change.
 if mirror:src=[row[left:left+crop_width] for row in rows[top:top+crop_height]]
 else:src=rows
 if rotation==0:rot=[list(r) for r in src]
 elif rotation==90:rot=[ [src[len(src)-1-x][y] for x in range(len(src))] for y in range(len(src[0])) ]
 elif rotation==180:rot=[list(reversed(row)) for row in reversed(src)]
 else:rot=[[src[x][len(src[0])-1-y] for x in range(len(src))] for y in range(len(src[0]))]
 if not mirror:return rot
 if rotation in (0,180):return list(reversed(rot))
 return [list(reversed(row)) for row in rot]

def main():
 a=argparse.ArgumentParser();a.add_argument('--live',action='store_true');a.add_argument('--payload',action='store_true');args=a.parse_args()
 root=R if args.live else R/'handoff_payload_26946'
 src=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java').read_text()
 if args.live:
  gl=R/SHADER
  if not gl.is_file() or sha(gl)!=SHADER_SHA:fail('current protected final SDR GL shader differs from actual successful 26945 source')
  shader=gl.read_text()
  for k in ('case 0:', 'case 1:', 'case 2:', 'case 3:',
            'mirror ? texSizeLocal.y - 1 - q.y',
            'mirror ? cropBottom + q.y',
            'mirror ? texSizeLocal.y - 1 - q.x',
            'mirror ? cropBottom + q.x',
            'texSizeLocal.x - 1 - q.y','texSizeLocal.x - 1 - q.x'):
   if k not in shader:fail('protected successful 26945 final SDR GLSL coordinate contract changed: '+k)
 if 'setScale(-1.0f, 1.0f)' in src:fail('original 26945 front X-only mirror still present')
 if src.count('final boolean mirrorFinalY = (rotation == 0 || rotation == 180);')!=1:fail('new final mirror axis not enforced')
 if src.count('rotation == 180 || rotation == 270')!=1:fail('source crop high-X case missing')
 # Non-symmetric identity raster; 4:3/16:9, high Y AND high X crop.
 tested=0
 for W,H,cW,cH in ((8,6,8,6),(8,6,8,4),(8,6,6,4),(7,13,7,13),(7,13,5,13),(16,12,16,8)):
  raw=[[int(y*W+x)+17 for x in range(W)] for y in range(H)]
  for rotation in (0,90,180,270):
   gain=bitmap_model(raw,rotation,True,cW,cH)
   actual=gl_expected(raw,rotation,True,cW,cH)
   if gain!=actual:fail(f'front UHDR map/GL SDR pixel mismatch {W}x{H} crop={cW}x{cH} rot={rotation} got={gain} expected={actual}')
   # The original 26945 false assumption must be rejected specifically at 180/0.
   if rotation in (0,180) and W>1 and H>1:
    old=[list(reversed(row)) for row in bitmap_model(raw,rotation,False,W,H)]
    if old==gl_expected(raw,rotation,True,W,H):fail('old 26945 X-only defect not detected')
   tested+=1
 # Historical non-mirrored shader/Android rotation must remain unchanged, full image.
 for rotation in (0,90,180,270):
  raw=[[y*8+x for x in range(8)] for y in range(6)]
  if bitmap_model(raw,rotation,False,8,6)!=gl_expected(raw,rotation,False,8,6):fail('rear baseline rotation modified/mismatched')
 print(f'PASS {tested} pixel-exact front GL/Android orientation+crop cases; rear baseline unchanged, old 26945 180-degree bug rejected')
if __name__=='__main__':
 try:main()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)

#!/usr/bin/env python3
from __future__ import annotations
import argparse,struct
from pathlib import Path

def rd16(b,o,be): return int.from_bytes(b[o:o+2],'big' if be else 'little')
def rd32(b,o,be): return int.from_bytes(b[o:o+4],'big' if be else 'little')
def wr16(b,o,v,be): b[o:o+2]=int(v).to_bytes(2,'big' if be else 'little')
def wr32(b,o,v,be): b[o:o+4]=int(v).to_bytes(4,'big' if be else 'little')
def promote(b):
    if len(b)<16: return False
    be=True if b[:2]==b'MM' else False if b[:2]==b'II' else None
    if be is None or rd16(b,2,be)!=42: return False
    ifd=rd32(b,4,be)
    if ifd>len(b)-2: return False
    count=rd16(b,ifd,be); es=ifd+2; nxt=es+count*12
    if nxt>len(b)-4: return False
    preview=rd32(b,nxt,be)
    if preview==0 or preview>len(b)-2: return False
    val=None
    for i in range(count):
        e=es+i*12
        if rd16(b,e,be)==330:
            if rd16(b,e+2,be)!=4 or rd32(b,e+4,be)!=1: return False
            val=e+8; break
    if val is None: return False
    wr32(b,val,preview,be); wr32(b,nxt,0,be); return True

def fixture(be,tag=330,typ=4,count=1):
    b=bytearray(96); b[:2]=b'MM' if be else b'II'; wr16(b,2,42,be); wr32(b,4,16,be)
    wr16(b,16,1,be); wr16(b,18,tag,be); wr16(b,20,typ,be); wr32(b,22,count,be); wr32(b,26,0,be)
    wr32(b,30,48,be); wr16(b,48,1,be); wr16(b,50,256,be); wr16(b,52,4,be); wr32(b,54,1,be); wr32(b,58,8,be); wr32(b,62,0,be)
    return b

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); a=ap.parse_args(); root=Path(a.root)
    cpp=(root/'app/src/main/cpp/dngCreator.cpp').read_text()
    saver=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java').read_text()
    rawvideo=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/RawVideoProcessor.java').read_text()
    for tok in ['SetCustomFieldULong(330, 0u)','iris26527PromoteSecondIfdToSubIfd','metadata.strip_offset = dng_image0->GetStripOffset();','dng_writer.AddImage(previewImage);']:
        if tok not in cpp: raise SystemExit('candidate SubIFD contract missing: '+tok)
    if saver.count('dngCreator.setEmbeddedPreviewEnabled(true);')!=1: raise SystemExit('still-preview opt-in count drift')
    if 'setEmbeddedPreviewEnabled' in rawvideo: raise SystemExit('RawVideo unexpectedly opts into embedded preview')
    for be in (False,True):
        b=fixture(be); assert promote(b); assert rd32(b,26,be)==48 and rd32(b,30,be)==0
    for bad in [fixture(False,331,4,1),fixture(False,330,3,1),fixture(False,330,4,2),bytearray(12)]:
        assert not promote(bad)
    print('PASS: SubIFD tag-330 pointer promotion little+big endian')
    print('PASS: malformed tag/type/count/short-buffer negative cases')
    print('PASS: stacked still is sole preview opt-in; RawVideo remains default-off')
if __name__=='__main__': main()

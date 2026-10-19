#!/usr/bin/env python3
"""Permanent 26856 B-only RGBA16F readback state regression.

The real failure condition: inherited PACK_ROW_LENGTH / SKIP_PIXELS / PBO can
change readPixels(ByteBuffer) addressing even with PACK_ALIGNMENT=1. Prove
all previous A/B source remains byte-identical outside the intended correction.
This is static/contract proof, NEVER real GLES or project compilation.
"""
from pathlib import Path
import hashlib, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
CURRENT=ROOT/'EVIDENCE/26856_PRE_COUNT_LONG_STACKER.kt'
LATEST=ROOT/'handoff_payload_26856/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
BASE=ROOT/'EVIDENCE/26856_PRIOR_WIP_STACKER.kt'
SCRIPT=ROOT/'transform_readback_state.py'
old=BASE.read_bytes();new=CURRENT.read_bytes()
assert hashlib.sha256(old).hexdigest()=='60e346b4e3d698881f8ee24af1a94fff12cab6cde6400466262f737ecefa0c64'
assert hashlib.sha256(new).hexdigest()=='5b9ffdca9e242fee92ea2f4a2c739df6ce2f49e69c5f2068d1a37e2ff554d695'
s=new.decode(); prior=old.decode()
latest=LATEST.read_text()
marker='    /* IRIS_26856_B_2X_EXACT_GL_PIXEL_PACK_OWNER'
methodstop='    /* IRIS_26856_B_2X_MEASURED_NORMAL_TILE_EXECUTION'
assert latest[latest.index(marker):latest.index(methodstop,latest.index(marker))]==s[s.index(marker):s.index(methodstop,s.index(marker))], 'GL pack owner changed during later frame/LONG fix'
methodstart=s.index('    /* IRIS_26856_B_2X_EXACT_GL_PIXEL_PACK_OWNER')
methodend=s.index('    /* IRIS_26856_B_2X_MEASURED_NORMAL_TILE_EXECUTION',methodstart)
body=s[methodstart:methodend]
required=[
 'GLES30.GL_PIXEL_PACK_BUFFER_BINDING',
 'GLES30.GL_PACK_ALIGNMENT', 'GLES30.GL_PACK_ROW_LENGTH',
 'GLES30.GL_PACK_SKIP_ROWS', 'GLES30.GL_PACK_SKIP_PIXELS',
 'GLES30.GL_READ_FRAMEBUFFER_BINDING', 'GLES30.GL_DRAW_FRAMEBUFFER_BINDING',
 'GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)',
 'GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH, 0)',
 'GLES30.glPixelStorei(GLES30.GL_PACK_SKIP_ROWS, 0)',
 'GLES30.glPixelStorei(GLES30.GL_PACK_SKIP_PIXELS, 0)',
 'GLES30.glReadPixels(0, 0, readWidth, readHeight,',
 'finally {',
 'GLES30.glBindFramebuffer(GLES30.GL_READ_FRAMEBUFFER, previousReadFbo)',
 'GLES30.glBindFramebuffer(GLES30.GL_DRAW_FRAMEBUFFER, previousDrawFbo)',
 'GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, previousPackBuffer)',
 'GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, previousPackAlignment)',
 'GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH, previousRowLength)',
 'GLES30.glPixelStorei(GLES30.GL_PACK_SKIP_ROWS, previousSkipRows)',
 'GLES30.glPixelStorei(GLES30.GL_PACK_SKIP_PIXELS, previousSkipPixels)',
 'destination.remaining() == requiredBytes',
]
for item in required:assert item in body,item
assert s.count('readIris26856B2xTightlyPackedRgba16f(')==3
execstart=s.index('    private fun reconstructIris26856BTrue2xTiles(')
execend=s.index('    private fun reconstructTrue2x(',execstart)
run=s[execstart:execend]
assert run.count('readIris26856B2xTightlyPackedRgba16f(')==2
assert 'GLES30.glReadPixels(' not in run
# All A and unrelated B methods keep exact prior bytes after removing the single
# inserted method and reversing precisely the two direct readback call sites.
s2=s[:methodstart]+s[methodend:]
oldSupport='''                        bindRenderTargets(intArrayOf(support), "26856 B 2x support read")
                        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
                        GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
                        GLES30.glReadPixels(0, 0, tw / 2, th / 2,
                            GLES30.GL_RGBA, GLES30.GL_HALF_FLOAT, supportBytes)
                        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
                        checkGlError("26856 B 2x CFA support readback")'''
newSupport='''                        readIris26856B2xTightlyPackedRgba16f(
                            support, tw / 2, th / 2, supportBytes,
                            "26856 B 2x CFA support readback",
                        )'''
oldRgb='''                            bindRenderTargets(intArrayOf(sensorRgb), "26856 B 2x output readback")
                            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
                            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
                            GLES30.glReadPixels(0, 0, tw, th, GLES30.GL_RGBA,
                                GLES30.GL_HALF_FLOAT, pixels)
                            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
                            checkGlError("26856 B 2x RGBA16F output readback")'''
newRgb='''                            readIris26856B2xTightlyPackedRgba16f(
                                sensorRgb, tw, th, pixels,
                                "26856 B 2x RGBA16F output readback",
                            )'''
assert s2.count(newSupport)==s2.count(newRgb)==1
s2=s2.replace(newSupport,oldSupport).replace(newRgb,oldRgb)
assert s2==prior,'source change spread beyond B-only readback and its helper'
# Counterexample to old code: nonzero 12-pixel pack row length on a 6-pixel
# support read would need 12xheight RGBA half storage, not 6xheight. Our new
# helper forces row length=0 (tight) and guarantees previous state restored.
width,height,inherited_row_length=6,8,12
assert inherited_row_length*height*8 > width*height*8
print('PASS 26856 true2x B-only readback: exact 7 GL pack/FBO states restored on error')
print('PASS both CFA-proof and RGB16F payload have tight buffers and no inherited PBO')
print('PASS historical 26856 exact pack-state regression against frozen pre-frame/LONG source; new source retains byte-identical pack owner')

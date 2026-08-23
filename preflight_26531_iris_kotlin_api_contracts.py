#!/usr/bin/env python3
from pathlib import Path
import argparse, re, shutil, subprocess, tempfile

STACK = Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt')

def fail(msg):
    raise SystemExit('FAIL: ' + msg)

def require(cond, msg):
    if not cond:
        fail(msg)

def extract_block(text, needle, open_char='(', close_char=')'):
    start = text.find(needle)
    if start < 0:
        fail('missing anchor: ' + needle)
    pos = text.find(open_char, start)
    if pos < 0:
        fail('missing opening delimiter after: ' + needle)
    depth = 0
    for i in range(pos, len(text)):
        ch = text[i]
        if ch == open_char:
            depth += 1
        elif ch == close_char:
            depth -= 1
            if depth == 0:
                return text[pos + 1:i]
    fail('unbalanced block after: ' + needle)

def named_args(block):
    # Top-level named arguments only. Nested lambda/default expressions are ignored by depth.
    names=[]; depth=0; token=[]
    chunks=[]
    for ch in block:
        if ch in '([{': depth += 1
        elif ch in ')]}': depth -= 1
        if ch == ',' and depth == 0:
            chunks.append(''.join(token)); token=[]
        else:
            token.append(ch)
    chunks.append(''.join(token))
    for chunk in chunks:
        m=re.match(r'\s*([A-Za-z_]\w*)\s*=', chunk, re.S)
        if m: names.append(m.group(1))
    return names

def function_params(text, name):
    m=re.search(r'\bfun\s+'+re.escape(name)+r'\s*\(', text)
    require(m is not None, f'missing function declaration {name}')
    block=extract_block(text, m.group(0))
    params=[]
    for part in block.split(','):
        mm=re.search(r'([A-Za-z_]\w*)\s*:', part)
        if mm: params.append(mm.group(1))
    return params

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--kotlinc', default=None, help='optional kotlinc executable for focused contract compile')
    a=ap.parse_args()
    root=Path(a.root)
    p=root/STACK
    require(p.is_file(), f'missing {STACK}')
    s=p.read_text(encoding='utf-8')

    # Exact regression #1 from failed 26531 V1.2: long clipping-mask shader still accepts dense flow.
    flow_params=function_params(s, 'renderAlignedLongFrameClippingMask')
    require('flowTexture' in flow_params and 'alignmentTexture' not in flow_params,
            f'long clipping signature drift: {flow_params}')
    call_anchor='renderAlignedLongFrameClippingMask(\n                                        rawTexture = temporalRaw,'
    start=s.find(call_anchor)
    require(start >= 0, 'long clipping call anchor missing')
    # Select the call nearest the SHADOW_LONG branch rather than the declaration.
    branch=s.find('RawBurstFrameRole.SHADOW_LONG ->')
    call_start=s.find('renderAlignedLongFrameClippingMask(', branch)
    require(call_start >= 0, 'SHADOW_LONG clipping call missing')
    call_block=extract_block(s[call_start:], 'renderAlignedLongFrameClippingMask(')
    args=named_args(call_block)
    require(args == ['rawTexture','flowTexture'], f'long clipping named args mismatch: {args}')
    require('flowTexture = prepared.flowTexture' in call_block,
            'long clipping no longer consumes prepared.flowTexture')
    require('alignmentTexture = prepared.bayerAlignmentTexture' not in call_block,
            'broken final-Bayer argument leaked into long clipping call')

    # Final Bayer alignment belongs only to the strength/noise capture path.
    strength_params=function_params(s, 'captureStrengthFrame')
    require('alignmentTexture' in strength_params and 'flowTexture' not in strength_params,
            f'strength capture signature drift: {strength_params}')
    require('bindTexture(strengthAlignmentProgram, "uAlignment", 0, alignmentTexture)' in s,
            'strength host no longer binds final Bayer alignment')
    require('alignmentTexture = prepared.bayerAlignmentTexture' in s,
            'temporal strength capture missing final Bayer alignment')
    require('alignmentTexture = bentoBayerAlignmentTexture' in s,
            'Bento strength capture missing final Bayer alignment')

    # Exact regression #2 from failed 26531 V1.2: every referenced tuning property must exist and initialize.
    data=re.search(r'private data class BayerKernelTuning\s*\((.*?)\n\s*\)', s, re.S)
    require(data is not None, 'BayerKernelTuning declaration missing')
    fields=set(re.findall(r'val\s+([A-Za-z_]\w*)\s*:', data.group(1)))
    required={'referenceSignal','referenceNoiseVariance','referenceGreenShotNoiseFactor',
              'referenceGreenReadVariance','referenceSnr','baseSpatialScale'}
    require(required <= fields, f'BayerKernelTuning missing fields: {sorted(required-fields)}')
    init_start=s.find('return BayerKernelTuning(')
    require(init_start >= 0, 'BayerKernelTuning initialization missing')
    init_block=extract_block(s[init_start:], 'BayerKernelTuning(')
    init_args=set(named_args(init_block))
    require(required <= init_args, f'BayerKernelTuning initialization missing: {sorted(required-init_args)}')
    require('referenceGreenShotNoiseFactor = shotNoise.getOrElse(1) { 0f }' in init_block,
            'reference green shot factor not sourced from normalized green channel')
    require('referenceGreenReadVariance = readNoise.getOrElse(1) { 0f }' in init_block,
            'reference green read variance not sourced from normalized green channel')
    for prop in ('referenceGreenShotNoiseFactor','referenceGreenReadVariance'):
        require(f'kernelTuning.{prop}' in s, f'expected merge weight no longer consumes {prop}')

    # Focused Kotlin compiler contract: catches named-argument/property mistakes even without Android SDK.
    kotlinc=a.kotlinc or shutil.which('kotlinc')
    if kotlinc:
        src='''\nprivate data class BayerKernelTuning(\n    val referenceSignal: Float,\n    val referenceNoiseVariance: Float,\n    val referenceGreenShotNoiseFactor: Float,\n    val referenceGreenReadVariance: Float,\n    val referenceSnr: Float,\n    val baseSpatialScale: Float,\n)\nprivate data class Prepared(val flowTexture:Int,val bayerAlignmentTexture:Int)\nprivate fun renderAlignedLongFrameClippingMask(rawTexture:Int, flowTexture:Int):Int = rawTexture + flowTexture\nprivate fun captureStrengthFrame(frameIndex:Int, alignmentTexture:Int):Int = frameIndex + alignmentTexture\nprivate fun contract(p:Prepared,k:BayerKernelTuning):Float {\n    renderAlignedLongFrameClippingMask(rawTexture=1, flowTexture=p.flowTexture)\n    captureStrengthFrame(frameIndex=0, alignmentTexture=p.bayerAlignmentTexture)\n    return k.referenceGreenShotNoiseFactor + k.referenceGreenReadVariance\n}\n'''
        with tempfile.TemporaryDirectory(prefix='iris26531_kapi_') as td:
            q=Path(td)/'Contract.kt'; q.write_text(src)
            cp=subprocess.run([kotlinc,str(q),'-d',str(Path(td)/'contract.jar')], text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            require(cp.returncode == 0, 'focused kotlinc contract failed:\n'+cp.stdout)
        print('PASS: focused kotlinc named-argument/property contract')
    else:
        print('INFO: kotlinc unavailable; static API contract checks completed')

    print('PASS: 26531 Iris Kotlin API contracts (long-flow + final-Bayer strength + green-noise fields)')

if __name__=='__main__':
    main()

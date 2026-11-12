#!/usr/bin/env python3
"""26923 V4: execute the REAL inline Python shader preflights against the
compiled 26922-derived 26923 live source before running expensive glslang.
Regression for Actions run 43299831723 (wrong 26923-vs-26922 uniform).
This is additive to, never a substitute for, pinned ESSL/SPIR-V/NDK compilation.
"""
from pathlib import Path
import subprocess, re, sys, hashlib

R=Path(__file__).resolve().parent
WRAPPER=R/'compile_26923_shaders.sh'
SHADER=R/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt'
FINAL=R/'app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag'
HR=R/'compile_26923_hr_spirv.sh'
NATIVE=R/'app/src/main/cpp/iris26864/bridge/Iris26923WronskiFinalize.comp'


def run_exact_python(script, label, should_pass=True):
    result=subprocess.run(['python3','-S','-'],input=script,text=True,
                          cwd=R,capture_output=True)
    if should_pass:
        if result.returncode:
            raise AssertionError(label+' failed: '+result.stdout+' '+result.stderr)
        print(result.stdout.strip())
    else:
        assert result.returncode != 0 and 'AssertionError' in result.stderr,\
            label+' failed to reject invalid historical uniform'
    return result


def get_heredocs(s, mark):
    matches=re.findall(r"python3 -S - <<'"+re.escape(mark)+r"'\n(.*?)\n"+re.escape(mark)+r"(?=\n|$)",s,re.S)
    return matches


def main():
    assert SHADER.is_file() and FINAL.is_file() and NATIVE.is_file(),\
        'real compiled-source candidate must exist, not payload-only verification'
    src=SHADER.read_text()
    assert src.count('val shader="""')==1
    inner=src.split('val shader="""',1)[1].split('""".trimIndent()',1)[0]
    assert inner.lstrip().startswith('#version 300 es')
    assert inner.count('uniform int uIris26922SrOn;')==1,\
        'successful 26922 active inline shader ownership changed'
    assert inner.count('uniform float uIris26922ShotVariance;')==1
    assert inner.count('uniform float uIris26922ReadVariance;')==1
    assert 'IRIS_26922_SR_ON_UNCERTAINTY_AWARE_CHROMA' in inner
    assert 'uIris26923SrOn;' not in inner,\
        'unexpected new shader ABI unsupported by compiled 26922 authority'
    assert 'uIris26923SrOn;' not in WRAPPER.read_text(),\
        'regressed stale/imagined shader contract from failed Actions run 43299831723'
    assert FINAL.read_text().startswith('#version 310 es')
    assert 'IRIS_26922_B_SRON_MATCHED_HDR_SDR_QUOTIENT' in FINAL.read_text()
    assert NATIVE.read_text().startswith('#version 450')

    # Run the SAME inline Python code GitHub Actions executes (rather than
    # paraphrasing it in a second implementation). Compiler tools are NOT
    # skipped in the real workflow; this stage catches assertion mistakes first.
    body=WRAPPER.read_text()
    blocks=get_heredocs(body,'PY')
    assert len(blocks)==2,'expected both genuine compiler wrapper Python blocks'
    assert 'assert orig.count(old)==1' in blocks[0]
    assert "src.count('uniform int uIris26922SrOn;')==1" in blocks[1]
    (R/'.photon_26904_incremental_work/real_shader_tools/26923_sr_shaders').mkdir(
        parents=True,exist_ok=True)
    try:
        for i,block in enumerate(blocks,1):
            compile(block,f'compile_26923_shaders.sh PY#{i}','exec')
            run_exact_python(block,f'26923 real shader preflight PY#{i}')
        generated=R/'.photon_26923_tone_compile_full.sh'
        assert generated.is_file()
        subprocess.run(['bash','-n',str(generated)],cwd=R,check=True)
        # The historical 26906 shader preflight was changed ONLY to test the
        # correct 26922 B ON source; compiler commands/optimizer stay identical.
        old=(R/'compile_26906_tone_glsl.sh').read_text()
        transformed=generated.read_text()
        assert '$COMPILER" -G --auto-map-locations' in transformed
        assert 'spirv-opt --target-env=opengl4.5 -O' in transformed
        assert transformed.count('IRIS_26922_B_SRON_MATCHED_HDR_SDR_QUOTIENT')==1
        assert old.count("'motionv2/render.glsl:render'")==1
    finally:
        (R/'.photon_26923_tone_compile_full.sh').unlink(missing_ok=True)

    # Fail-closed reproduction of the exact V3 bug using the original
    # executable check, not a trivial regex-only test.
    bad=blocks[1].replace("src.count('uniform int uIris26922SrOn;')==1",
                          "src.count('uniform int uIris26923SrOn;')==1",1)
    assert bad!=blocks[1]
    run_exact_python(bad,'26923 V3 wrong-uniform negative',should_pass=False)

    nblocks=get_heredocs(HR.read_text(),'END_26923_STATIC_SHADER_CONTRACT')
    assert len(nblocks)==1,'missing actual native shader source/CMake preflight'
    compile(nblocks[0],'compile_26923_hr_spirv.sh static contract','exec')
    run_exact_python(nblocks[0],'26923 real HR CMake/shader preflight')
    for p in [WRAPPER,HR,R/'compile_26920_lk_shaders.sh']:
        subprocess.run(['bash','-n',str(p)],cwd=R,check=True)
    print('PASS 26923 V4 exact live 26922 shader ABI; both actual ESSL wrapper Python preflights; 26906 compiler shell preserved; new HR shader/CMake contract; former wrong-uniform assertion rejected')

if __name__=='__main__':
    try:main()
    except Exception as e:
        print('26923 BLOCKED: shader ABI precompile contract: '+str(e),file=sys.stderr)
        raise

#!/usr/bin/env python3
"""26905 original-source B-SR-OFF all-NORMAL and RAW-model receipt regression."""
from pathlib import Path
import argparse,hashlib,re,subprocess,tempfile,sys

def req(x,msg):
    if not x:raise AssertionError('26905 BLOCKED: '+msg)

def java_helper(s):
    name='private static boolean iris26905BOffNormalOnly('
    req(s.count(name)==1,'B OFF capture predicate must have one owner')
    a=s.index(name);b=s.index('{',a);c=s.index('}',b)
    return s[a:c+1]

def run_java(helper):
    # Compile the EXACT extracted production predicate, not a Python simulation.
    code='''public class Proof {
        static class Iris26856ABSettings { enum Mode { ORIGINAL_26850, AMAZE_26855 } }
        '''+helper.replace('com.particlesdevs.photoncamera.settings.Iris26856ABSettings.Mode','Iris26856ABSettings.Mode')+'''
        public static void main(String[] args) {
            boolean[] expected={false,false,true,false};
            boolean[] got={iris26905BOffNormalOnly(Iris26856ABSettings.Mode.ORIGINAL_26850,false),
                 iris26905BOffNormalOnly(Iris26856ABSettings.Mode.ORIGINAL_26850,true),
                 iris26905BOffNormalOnly(Iris26856ABSettings.Mode.AMAZE_26855,false),
                 iris26905BOffNormalOnly(Iris26856ABSettings.Mode.AMAZE_26855,true)};
            if(!java.util.Arrays.equals(expected,got))throw new AssertionError("B OFF predicate altered");
            for(int n:new int[]{2,8,14,30}){
                int normals=n-(got[2]?0:1);
                if(normals!=n)throw new AssertionError("unexpected reserved LONG slot");
            }
            System.out.println("PASS extracted actual B-only NORMAL-budget Java helper; A/B/B-ON 2,8,14,30");
        }
    }
    '''
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'Proof.java';p.write_text(code)
        subprocess.run(['javac','-d',td,str(p)],check=True)
        subprocess.run(['java','-cp',td,'Proof'],check=True)

def test(root,installed,with_javac):
    src=root/('app' if installed else 'handoff_payload_26905/app')
    capture=(src/'src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
    cpp=(src/'src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp').read_text()
    version=(src/'version.properties').read_text()
    req('VERSION_BUILD=26905' in version and 'VERSION_NAME=0.9726905' in version,'version incorrect')
    req(capture.count('final boolean iris26905BOffAllNormal = iris26905BOffNormalOnly(')==1,'route ownership not unique')
    req(capture.count('final com.particlesdevs.photoncamera.settings.Iris26856ABSettings.Mode iris26856FrozenExperiment =')==1,
        'B snapshot must be frozen once')
    req(capture.index('final boolean iris26905BOffAllNormal =')<capture.index('final boolean iris26593LongBudgetAllows =')
        <capture.index('final int iris26593AuxCount ='), 'must decide B OFF before LONG budgeting')
    req('final boolean iris26593LongBudgetAllows = iris26593TotalTarget >= 2 && !iris26905BOffAllNormal;' in capture,
        'B OFF does not block LONG at its actual request callsite')
    req('final int iris26593NormalTarget = iris26593TotalTarget - iris26593AuxCount;' in capture,
        'normal budget did not inherit explicit zero auxiliaries')
    req('final int iris26757EffectiveTotalTarget = iris26757EffectiveNormalTarget + iris26593AuxCount;' in capture,
        'immutable total budget not retained')
    req('if (iris26593TotalPresent != iris26593Plan.totalTargetFrames)' in capture,
        'missing exact total immutable capture gate')
    req('iris26593MissingNormals' in capture and 'submitMotion26593MissingNormals' in capture,
        'postshutter exact normal topup missing')
    req('IRIS_26905_B_OFF_NORMAL_FRAME_BUDGET_HELPER' in capture and 'IRIS_26905_B_OFF_ALL_NORMAL_BUDGET' in capture,
        'implementation markers missing')
    req(cpp.count('IRIS_26905_B_OFF_RAW_BURST_NOISE_MODEL')==1 and
        cpp.count('recorder.setMeasuredRawNoise(slopes, offsets, measured);')==1,
        'native noise receipt/algorithm owner changed')
    req('std::fprintf(stderr, "IRIS_26888_B_OFF_RAW_BURST_NOISE' not in cpp,
        'noise report still in inaccessible stderr')
    req('validBlocks[site]' in cpp and 'fit.has_value()' in cpp and
        '(!fit && measured)' in cpp and 'measured ? 0 : 1' in cpp,
        'must distinguish actual fit/fallback/unmeasured and not claim effective local support')
    req('for (std::uint32_t b = 0; b < bx * by; ++b)' in cpp,
        'native RAW source valid-block statistics missing')
    req('#include <android/log.h>' in cpp and '__android_log_print(ANDROID_LOG_INFO' in cpp,
        'Android-visible receipt missing')
    if with_javac:run_java(java_helper(capture))
    if installed:
        expected={}
        for line in (root/'26905_PRECOMPILE_EXPECTED_FULL_APP.sha256').read_text().splitlines():
            h,path=line.split('  ',1);expected[path]=h
        actual={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in expected}
        req(actual==expected,'actual installed source differs from exact verified expected candidate')
    print('PASS 26905 frozen B OFF all-NORMAL capture ownership, capture completion, noise-fit receipt, source scope')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--with-javac',action='store_true');p.add_argument('--installed',action='store_true')
    try:
        a=p.parse_args();test(a.root.resolve(),a.installed,a.with_javac)
    except Exception as e:
        print('26905 TEST FAIL',e,file=sys.stderr);sys.exit(1)

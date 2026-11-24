#!/usr/bin/env python3
"""Full pinned successor source and active-owner boundary checks."""
import argparse,importlib.util,pathlib,re,xml.etree.ElementTree as ET,subprocess,sys
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder26983',R/'build_26983_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
p=argparse.ArgumentParser();m=p.add_mutually_exclusive_group(required=True);m.add_argument('--live',action='store_true');m.add_argument('--payload',action='store_true');o=p.parse_args();root=R if o.live else R/'handoff_payload_26983';changes,base,expected=b.scope()
if o.live:b.exact(root,'26983_EXPECTED_FULL_APP.sha256','26983 live full source')
else:
 for q in changes:assert b.sha(root/q)==expected[q],q
j=root/'app/src/main/java/com/particlesdevs/photoncamera';k=root/'app/src/main/java/com/hinnka/mycamera/processor'
controller=(j/'capture/CaptureController.java').read_text();saver=(j/'processing/ImageSaver.java').read_text();default=(j/'processing/DefaultSaver.java').read_text();batch=(j/'processing/processor/Iris26983COnBatchPublication.java').read_text();bridge=(j/'processing/processor/PhotonMotionMgc1271Bridge.kt').read_text();ingress=(k/'GlesIris26983COnMotionIngress.kt').read_text();fence=(j/'capture/Iris26983DirectPreviewFence.java').read_text()
assert '"C".equals(iris26972RequestedAtShutter.id) &&' in controller and 'iris26972CStartIndependentCamera2(false);' in controller
assert 'iris26486ImageSaver.runIris26983COnRaw(' in controller and 'else iris26486ImageSaver.runMotionRaw(' in controller
assert 'iris26983FrozenOutput' in controller and 'iris26983COnAtPress?new Iris26983COnOutput():null' in controller
assert 'Iris26983COnCaptureSafety.frozenNormalPairMatches' in controller and 'Iris26983COnShutterIsoMath.solve26970' in controller
assert 'Iris26983DirectPreviewPlan.query(' in controller and 'iris26983StartDirectPreview(iris26935Relay.token()' in controller
assert 'iris26983FinishDirectPreview(iris26935Relay.token())' in controller and 'Iris26983DirectPreviewRequests.Targets.DIRECT' in controller
assert 'iris26983PreviewTransitionActive()' in controller and 'abortToGl' in fence and 'freshGl' in controller
assert 'runIris26983COnBatch(' in saver and 'Iris26983COnBatchPublication.run(' in default
assert batch.index('PhotonMotionMgc1271Bridge.publishCOnDng(')<batch.index('Iris26983COnPhotoPublication.runPrepared(')
assert 'if(rawSaver==2)' in batch and 'return;' in batch[batch.index('if(rawSaver==2)'):batch.index('Iris26983COnPhotoPublication.runPrepared(')]
assert 'if (cOnDngOnly) throw COnDngCompleted(saved)' in bridge and 'requireParity(!cOnDngOnly,' in bridge and 'if (!cOnDngOnly) inputImages.forEach' in bridge
assert 'if (cOnDngOnly) null else GlesMgcRawFusion(' in bridge
assert 'GlesIris26983COnPipeline' in ingress and 'Iris26983COnCapturePreparation' in ingress
assert not any(x in ingress for x in ('GlesIris26864','Iris26975CPinnedDonorProEngine','Iris26972CCamera2ShutterSession'))
for q in ['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java','app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java','app/src/main/java/com/hinnka/mycamera/processor/experimentc/Iris26975CPinnedDonorProEngine.kt','app/build.gradle']:
 assert base[q]==expected[q],q
assert all(not q.startswith('app/src/main/java/com/hinnka/mycamera/processor/experimentc/') for q in changes)
assert not any('/jniLibs/' in q or '/third_party/' in q for q in changes)
if o.live:
 # New separately named shader sources, original C OFF inventory validated by its existing compiler.
 subprocess.run([sys.executable,'-S',str(R/'verify_26983_con_glsl.py'),'--root',str(root/'app')],check=True)
print('PASS 26983 exact source, C ON dispatch, C OFF retention, independent DNG-only bypass and B/C preview lifecycle source boundaries')

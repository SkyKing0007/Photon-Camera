#!/usr/bin/env python3
import argparse,pathlib,subprocess,shutil,tempfile,sys
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--candidate',required=True);a=p.parse_args();r=pathlib.Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='photon26983_host_') as td:
 t=pathlib.Path(td);(t/'actual').symlink_to(pathlib.Path(a.base).resolve(),target_is_directory=True);(t/'candidate').symlink_to(pathlib.Path(a.candidate).resolve(),target_is_directory=True)
 for name in ('test_26983_capture_policy_host.py','test_26983_con_host.py','test_26983_post_host.py','test_26983_gpu_host.py','test_26983_orchestration_host.py','test_26983_motion_ingress_host.py','26983_copy_records.json','26983_post_copy_records.json','advance_post_26983.py'):
  shutil.copyfile(r/name,t/name)
 for name in ('capture_policy','con','post','gpu','orchestration','motion_ingress'):
  subprocess.run([sys.executable,str(t/f'test_26983_{name}_host.py')],check=True)
print('PASS independent capture policies, source/JNI parity, host C++/JDK/Kotlin processing contracts and RAW ownership; Android device/real Android compiler NOT proven')

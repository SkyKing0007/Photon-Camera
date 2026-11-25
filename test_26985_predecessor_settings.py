import pathlib,sys,tempfile,shutil,subprocess,hashlib
R=pathlib.Path(__file__).resolve().parent
base,candidate=map(pathlib.Path,sys.argv[1:]);base=base.resolve();candidate=candidate.resolve()
j='app/src/main/java/com/particlesdevs/photoncamera/'
k='app/src/main/java/com/hinnka/mycamera/processor/'
setting=j+'ui/settings/SettingsActivity.java'
old=dict((p,h) for h,p in (l.split('  ',1) for l in (R/'26984_BASE_26983_FULL_APP.sha256').read_text().splitlines()))
with tempfile.TemporaryDirectory() as td:
 t=pathlib.Path(td)
 paths=[setting,j+'ui/camera/CameraFragment.java',j+'ui/camera/views/settingsbar/SettingsBarLayout.java']+[k+p for p in ('Iris26972CCaptureToGallery.kt','experimentc/Iris26975CPinnedDonorProEngine.kt','experimentc/original129/raw/RawDemosaicProcessor.kt','experimentc/original129/raw/MgcSharpen.kt','experimentc/original129/raw/GlesMgcSharpen.kt','experimentc/original129/raw/MgcSharpenCurveBuilder.kt','experimentc/original129/processor/PhotonSharpenTuning.kt')]
 for p in paths:
  src=(R/'handoff_payload_26983'/p) if p==setting else base/p
  assert hashlib.sha256(src.read_bytes()).hexdigest()==old[p],p
  dest=t/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
 subprocess.run([sys.executable,'-S',str(R/'test_26984_settings_host.py'),'--base',str(t),'--candidate',str(candidate)],check=True)

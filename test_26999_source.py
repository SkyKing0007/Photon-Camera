#!/usr/bin/env python3
import argparse,json,xml.etree.ElementTree as ET
import build_26999_incremental as b
p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--live',action='store_true');g.add_argument('--payload',action='store_true');o=p.parse_args();changed,base,expected=b.scope();R=b.R if o.live else b.R/'handoff_payload_26999'
if o.live:b.exact(R,'26999_EXPECTED_FULL_APP.sha256','26999 actual live source')
else:assert all(b.sha(R/f)==expected[f] for f in changed)
J='app/src/main/java/com/particlesdevs/photoncamera/'
D=J+'ui/settings/custompreferences/'
def read(p):return (R/p).read_text()
for f in changed:
 if f.endswith('.xml'):ET.parse(R/f)
assert not any('/cpp/' in p or '/jniLibs/' in p or '/assets/' in p or '/processor/' in p or '/processing/' in p for p in changed)
mp=json.loads((b.R/'26999_UPSTREAM_SOURCE_MAP.json').read_text());assert mp['donor_commit']=='ce0581b5a3a535d062957eec7fb3415747084516' and len(mp['files'])==29
for row in mp['files']:
 assert base[row['candidate']]==expected[row['candidate']]==row['candidate_sha256'] and row['candidate'] not in changed
 if o.live:assert b.sha(R/row['candidate'])==row['candidate_sha256']
for k in ['settings/Iris26998CDenoiseSettings.java','settings/Iris26982CSharpenSettings.java','capture/CaptureController.java','util/Log.java','processing/ImagePath.java','settings/Iris26856ABSettings.java']:
 assert J+k not in changed and base[J+k]==expected[J+k]
s=read('app/src/main/res/xml/preferences.xml');assert s.count('Customize SNR Levels')==2 and 'Tap label to edit five SNR-adaptive bands' not in s
s=read(D+'Iris26998CAdvancedDenoisePreference.java');assert '"Level "+(i+1)' in s and '"Level "+(band+1)' in s and 'setMax(1600)' in s and '"RESET"' in s and '"CANCEL"' in s and '"SET"' in s and 'saveEnabledBands(c,selected,isChroma,draft)' in s
s=read(D+'UniversalSeekBarPreference.java');assert all('pref_iris_26982_c_mgc_band_'+str(i) in s for i in range(3)) and 'String.format(Locale.ROOT, "%.2f", Float.parseFloat(valueToPersist))' in s and 'persistString(valueToPersist)' in s and 'setDirectValue(value)' in s
s=read(J+'util/SimpleStorageHelper.java');assert all(x in s for x in ('IRIS_CONFIGS_DIR_NAME = "Configs"','IRIS_RAW_DIR_NAME, IRIS_LOGS_DIR_NAME, IRIS_CONFIGS_DIR_NAME','for (String child : REQUIRED_DIRS) ok &= ensureDownloadsDirectory(context, child)','for (String child : REQUIRED_DIRS) ok &= findOrCreateDirectory(iris, child) != null','"text/plain", false','matchesDownloadsLocation(context, uri, path)','IRIS_CONFIGS_DIR_NAME + "/x"','name.toLowerCase(Locale.ROOT).endsWith(".xml")','Configuration already exists','verifyConfigBytes(in, bytes)'))
s=read(J+'ui/camera/CameraActivity.java');assert s.count('SimpleStorageHelper.ensureIrisStorageHierarchy(')==3 and 'SimpleStorageHelper.setDownloadsRoot(this)' in s and 'SimpleStorageHelper.setStorageRoot(CameraActivity.this, root)' in s
s=read(D+'BackupPreferences.java');assert 'editText.setText("")' in s and 'XML format' in s and 'backup_file_name' not in s
s=read(D+'RestorePreference.java');assert 'SimpleStorageHelper.listBackupFileNames(context)' in s and 'super.onClick()' in s and 'setEntryValues(names)' in s and '.json' not in s
s=read(J+'settings/BackupRestoreUtil.java');assert all(x in s for x in ('Iris26999XmlConfig.encode(values)','Iris26999XmlConfig.decode','SimpleStorageHelper.saveConfig(context, name, xml)','SimpleStorageHelper.openConfig(context, fileName)','iris_26856_physical_lens_ab','iris_26926_b_sr_on_fallback_per_physical_lens','iris26995_c_lkr_denoise','iris_26912_b_off_noise_per_physical','camera_preferences','R.string._per_lens','restoring = true','finally { restoring = false; }','edit.commit()'))
assert 'BackupRestoreUtil.isRestoring()' in read(J+'settings/PreferenceKeys.java') and 'BackupRestoreUtil.isRestoring()' in read(J+'ui/settings/SettingsActivity.java')
print('PASS exact UI/config/storage-only scope, 29 original donor mappings, protected processing, all specified behavior source contracts')

#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,xml.etree.ElementTree as ET
B,C=map(Path,sys.argv[1:3]); A={'app/src/main/res/xml/preferences.xml','app/version.properties'}
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {p.relative_to(r).as_posix():h(p) for p in (r/'app').rglob('*') if p.is_file()}
b,c=U(B),U(C); assert {p for p in set(b)|set(c) if b.get(p)!=c.get(p)}==A; assert len(b)==1783 and len(c)==1783
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726817' in v and 'VERSION_BUILD=26817' in v
root=ET.parse(C/'app/src/main/res/xml/preferences.xml').getroot(); ns='{http://schemas.android.com/apk/res/android}'; about=next(x for x in root if x.attrib.get(ns+'key')=='@string/pref_category_about_key')
d=[x for x in list(about) if x.attrib.get(ns+'key')=='@string/pref_enable_logging_key']; assert len(d)==1
assert sum(1 for x in about.iter() if x.attrib.get(ns+'key')=='@string/pref_enable_logging_key')==1
assert d[0].attrib.get(ns+'defaultValue')=='false' and d[0].attrib.get(ns+'icon')=='@drawable/ic_logging_document'
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/util/Log.java','app/src/main/java/com/particlesdevs/photoncamera/util/MotionTrace.java','app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java','app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java','app/src/main/res/drawable/ic_logging_document.xml','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt']:
    assert h(B/rel)==h(C/rel),rel
print('PASS 26817 direct About-category logging switch; all 26816 backend/IQ bytes preserved')

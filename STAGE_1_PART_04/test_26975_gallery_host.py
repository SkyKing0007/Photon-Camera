#!/usr/bin/env python3
"""Exact C production-publisher Java compiled with tiny HOST-only Android API models.
Never substitute for Android SDK compile or on-device provider validation.
"""
from pathlib import Path
import argparse, subprocess, tempfile, textwrap
parser=argparse.ArgumentParser()
parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2]/"26975_full_engine_candidate/app")
ROOT=parser.parse_args().root.resolve()
SRC=ROOT/'src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26975CDonorMediaStorePublisher.java'
S=SRC.read_text()
HELPER=(ROOT/'src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java').read_text()
MANAGER=(ROOT/'src/main/java/com/particlesdevs/photoncamera/util/FileManager.java').read_text()
assert 'Environment.DIRECTORY_DCIM + "/Camera/"' in HELPER
assert 'sDCIM_CAMERA = new File(sEXTERNAL_DIR + "//DCIM//Camera//")' in MANAGER
assert 'android.os.Environment.DIRECTORY_DCIM + "/Camera/"' in S
assert 'DCIM/PhotonCamera/' not in S
assert 'MediaStore.MediaColumns.RELATIVE_PATH, RELATIVE_DIR' in S
assert 'if (!store.commit(row))' in S and 'store.discard(row)' in S
assert 'hasOriginalNormalizedExif(verifiedJpegR)' in S
assert 'public static Uri publish' in S
JAVA={
'android/content/ContentValues.java':'''package android.content; public class ContentValues extends java.util.HashMap<String,Object> {
 public void put(String k,String v){super.put(k,v);} public void put(String k,Integer v){super.put(k,v);} public void put(String k,Long v){super.put(k,v);} }''',
'android/content/Context.java':'''package android.content; public abstract class Context { public abstract ContentResolver getContentResolver(); }''',
'android/content/ContentResolver.java':'''package android.content; import android.net.Uri; import java.io.*;
 public abstract class ContentResolver { public abstract Uri insert(Uri uri,ContentValues values);
 public abstract OutputStream openOutputStream(Uri uri,String mode) throws IOException;
 public abstract int update(Uri uri,ContentValues values,String where,String[] args);
 public abstract int delete(Uri uri,String where,String[] args); }''',
'android/net/Uri.java':'''package android.net; public class Uri { private final String value;
 public Uri(String value){this.value=value;} public String toString(){return value;} }''',
'android/os/Environment.java':'''package android.os; public final class Environment { public static final String DIRECTORY_DCIM="DCIM"; }''',
'android/os/Build.java':'''package android.os; public final class Build { public static class VERSION {public static final int SDK_INT=36;}
 public static class VERSION_CODES {public static final int Q=29;} }''',
'android/provider/MediaStore.java':'''package android.provider; import android.net.Uri; public final class MediaStore {
 public static final String VOLUME_EXTERNAL_PRIMARY="external_primary";
 public static class MediaColumns {public static final String DISPLAY_NAME="DISPLAY_NAME",MIME_TYPE="MIME_TYPE",RELATIVE_PATH="RELATIVE_PATH",IS_PENDING="IS_PENDING";}
 public static class Images { public static class ImageColumns {public static final String DATE_TAKEN="DATE_TAKEN";}
 public static class Media { public static Uri getContentUri(String volume){return new Uri("content://"+volume);} } } }''',
'androidx/exifinterface/media/ExifInterface.java':'''package androidx.exifinterface.media; import java.io.File;
 public final class ExifInterface { public static final String TAG_ORIENTATION="orientation"; public static final int ORIENTATION_NORMAL=1;
 public ExifInterface(File file){} public int getAttributeInt(String tag,int fallback){return ORIENTATION_NORMAL;} }''',
'com/hinnka/mycamera/processor/experimentc/original129/gallery/Jpeg444ExportEncoder.java':'''package com.hinnka.mycamera.processor.experimentc.original129.gallery; import java.io.File;
 public final class Jpeg444ExportEncoder {public static final Jpeg444ExportEncoder INSTANCE=new Jpeg444ExportEncoder();
 public boolean isJpegR(File file){return file.length()>64;} }''',
'com/particlesdevs/photoncamera/processing/experimentc/Iris26972CContract.java':'''package com.particlesdevs.photoncamera.processing.experimentc;
 public final class Iris26972CContract {public static final boolean CONTROLLED_DEVICE_TRIAL_ENABLED=true;}''',
'com/particlesdevs/photoncamera/processing/experimentc/PublisherHost.java':r'''package com.particlesdevs.photoncamera.processing.experimentc;
import android.content.*; import android.net.Uri; import android.provider.MediaStore;
import java.io.*; import java.nio.file.*; import java.util.*; import java.util.concurrent.atomic.AtomicInteger;
public final class PublisherHost {
 static void require(boolean condition,String why){ if(!condition)throw new AssertionError(why); }
 static class Provider extends ContentResolver {
    ContentValues reserved; ContentValues committed; ByteArrayOutputStream stream; int discards=0;
    public Uri insert(Uri uri,ContentValues v){reserved=v;return new Uri("content://gallery/image/1");}
    public OutputStream openOutputStream(Uri uri,String mode){stream=new ByteArrayOutputStream();return stream;}
    public int update(Uri uri,ContentValues v,String where,String[] args){committed=v;return 1;}
    public int delete(Uri uri,String where,String[] args){discards++;return 1;}
 }
 static class Ctx extends Context { final Provider provider=new Provider();
    public ContentResolver getContentResolver(){return provider;} }
 static class Store implements Iris26975CDonorMediaStorePublisher.PendingStore {
    final ByteArrayOutputStream bytes=new ByteArrayOutputStream(); int reserve=0,commit=0,discard=0;
    public Object reserve(String name,long time){reserve++;return "row";}
    public OutputStream open(Object row){return bytes;}
    public boolean commit(Object row){commit++;return true;}
    public boolean discard(Object row){discard++;return true;}
 }
 public static void main(String[] unused) throws Exception {
    Path path=Files.createTempFile("photon26975c-host", ".jpg");
    try {
        byte[] reference=new byte[150_000]; new Random(26975).nextBytes(reference); Files.write(path,reference);
        Ctx ctx=new Ctx();
        Uri uri=Iris26975CDonorMediaStorePublisher.publish(ctx,path.toFile(),"IRIS_C_26975.jpg",123456789L,0);
        require(uri!=null,"no published image");
        require("DCIM/Camera/".equals(ctx.provider.reserved.get(MediaStore.MediaColumns.RELATIVE_PATH)),"not Iris DCIM/Camera");
        require(Integer.valueOf(1).equals(ctx.provider.reserved.get(MediaStore.MediaColumns.IS_PENDING)),"missing pending image reservation");
        require(Integer.valueOf(0).equals(ctx.provider.committed.get(MediaStore.MediaColumns.IS_PENDING)),"pending row not committed");
        require(Arrays.equals(reference,ctx.provider.stream.toByteArray()),"JPEG/R payload byte-identical publication failed");
        require(ctx.provider.discards==0,"successful row was deleted");
        Store s=new Store();Object committed=Iris26975CDonorMediaStorePublisher.transferVerified(path.toFile(),"IRIS_C_26975.jpg",5L,s);
        require(committed!=null && s.commit==1 && s.discard==0 && Arrays.equals(reference,s.bytes.toByteArray()),"test seam success failed");
        Store cancelling=new Store(); AtomicInteger checks=new AtomicInteger();boolean rejected=false;
        try { Iris26975CDonorMediaStorePublisher.transferVerified(path.toFile(),"IRIS_C_26975.jpg",5L,cancelling,()->checks.incrementAndGet()<4); }
        catch(IOException expected){rejected=true;}
        require(rejected && cancelling.reserve==1 && cancelling.commit==0 && cancelling.discard==1,"partial cancelled JPEG/R did not roll back");
        Store malformed=new Store();rejected=false;
        try { Iris26975CDonorMediaStorePublisher.transferVerified(path.toFile(),"../evil.jpg",5L,malformed); }
        catch(IOException expected){rejected=true;}
        require(rejected && malformed.reserve==0,"invalid filename reached MediaStore");
        System.out.println("PASS C-only Java publisher: Iris DCIM/Camera; byte-exact JPEG/R; pending/commit; cancellation rollback; filename rejection");
    }finally{Files.deleteIfExists(path);}
 }
}'''
}
with tempfile.TemporaryDirectory(prefix='photon26975_gallery_') as td:
 t=Path(td)
 for rel,s in JAVA.items():
  f=t/'src'/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s)
 dest=t/'src/com/particlesdevs/photoncamera/processing/experimentc/Iris26975CDonorMediaStorePublisher.java'
 dest.write_bytes(SRC.read_bytes())
 files=[str(x) for x in (t/'src').rglob('*.java')]
 subprocess.run(['javac','--release','17','-encoding','UTF-8','-d',str(t/'classes'),*files],check=True)
 subprocess.run(['java','-cp',str(t/'classes'),'com.particlesdevs.photoncamera.processing.experimentc.PublisherHost'],check=True)
print('PASS source gallery/MediaStore owner vs actual Iris A/B source; host scope only')

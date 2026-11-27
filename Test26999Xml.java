import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import com.particlesdevs.photoncamera.settings.Iris26999XmlConfig;
public class Test26999Xml {
 static InputStream in(String s) { return new ByteArrayInputStream(s.getBytes(StandardCharsets.UTF_8)); }
 static void invalid(String s, Set<String> keys) throws Exception { try { Iris26999XmlConfig.decode(in(s),keys); throw new AssertionError("accepted malformed config: "+s); } catch (Exception expected) {} }
 public static void main(String[] args) throws Exception {
  Map<String,Map<String,Object>> m=new LinkedHashMap<>();
  Map<String,Object> main=new LinkedHashMap<>();main.put("iris_26998_c_denoise_luma_0030_enabled",true);main.put("iris_26998_c_denoise_luma_0030_bands","0.10,4.0,0.10,0.10,10.0");main.put("iris_26982_c_mgc_band_1_0030","0.2");main.put("pref_tunable_a",0.125f);main.put("i",Integer.MIN_VALUE);main.put("l",Long.MAX_VALUE);main.put("float",-0.0f);main.put("special\t\r", "  & < > \" \r\n\t 😀 ");main.put("set",new HashSet<>(List.of("a&b","<t>","")));main.put("empty","");
  m.put("main",main);m.put("per_lens",new LinkedHashMap<>(Map.of("settings_for_camera_0","{\"noise\":\"0.00\"}","settings_for_camera_5","{\"noise\":\"1.00\"}")));m.put("super_res_denoise",new LinkedHashMap<>(Map.of("0",true,"5",false)));m.put("experiment_selection",new LinkedHashMap<>());
  byte[] a=Iris26999XmlConfig.encode(m);assert Arrays.equals(a,Iris26999XmlConfig.encode(m));assert m.equals(Iris26999XmlConfig.decode(new ByteArrayInputStream(a),m.keySet()));
  assert Iris26999XmlConfig.fileName("  My 1x settings  ").equals("My 1x settings.xml");assert Iris26999XmlConfig.fileName("my.XML").equals("my.xml");for(String name:List.of("",".xml","../bad","bad\\name","bad/name","bad:name","bad.")){try{Iris26999XmlConfig.fileName(name);throw new AssertionError(name);}catch(IOException expected){}}
  assert Iris26999XmlConfig.decode(in("<map><string name=\"s\">x&amp;y</string><int name=\"i\" value=\"4\"/><long name=\"l\" value=\"2147483648\"/><boolean name=\"b\" value=\"false\"/><set name=\"k\"><string>one</string></set></map>"),m.keySet()).get("main").equals(Map.of("s","x&y","i",4,"l",2147483648L,"b",false,"k",Set.of("one")));
  for(String x:List.of("<map><int name=\"n\" value=\"bad\"/></map>","<map><string name=\"n\">a</string><string name=\"n\">b</string></map>","<map><boolean name=\"x\" value=\"1\"/></map>","<iris-config version=\"1\"><store name=\"main\"/></iris-config>","<iris-config version=\"1\"><store name=\"iris_storage_access\"/></iris-config>","<!DOCTYPE map [<!ENTITY x SYSTEM \"file:///etc/passwd\">]><map><string name=\"a\">&x;</string></map>","<map><string name=\"x\"><other/></string></map>","<map><unsupported name=\"x\"/></map>")) invalid(x,m.keySet());
  System.out.println("PASS actual Java XML typed per-lens roundtrip, deterministic encoding, filename checks, legacy XML, malformed/duplicate/scope/XXE rejection");
 }
}

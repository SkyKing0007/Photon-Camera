package android.hardware.camera2;
import java.util.HashMap;
public class CaptureResult {public static final class Key<T>{}
 public static final Key<Integer> CONTROL_AE_ANTIBANDING_MODE=new Key<>();
 public static final int CONTROL_AE_ANTIBANDING_MODE_50HZ=1,CONTROL_AE_ANTIBANDING_MODE_60HZ=2,CONTROL_AE_ANTIBANDING_MODE_AUTO=3;
 private final HashMap<Key<?>,Object> m=new HashMap<>();
 public <T> T get(Key<T> k){return (T)m.get(k);} public <T> void set(Key<T>k,T v){m.put(k,v);}
}

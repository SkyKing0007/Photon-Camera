package android.hardware.camera2;
import android.util.Range; import java.util.HashMap;
public class CameraCharacteristics { public static final class Key<T>{}
 public static final Key<Range<Long>> SENSOR_INFO_EXPOSURE_TIME_RANGE=new Key<>();
 public static final Key<Range<Integer>> SENSOR_INFO_SENSITIVITY_RANGE=new Key<>();
 public static final Key<Integer> SENSOR_MAX_ANALOG_SENSITIVITY=new Key<>();
 private final HashMap<Key<?>,Object> m=new HashMap<>();
 public <T> void set(Key<T> k,T v){m.put(k,v);} public <T> T get(Key<T> k){return (T)m.get(k);}
}

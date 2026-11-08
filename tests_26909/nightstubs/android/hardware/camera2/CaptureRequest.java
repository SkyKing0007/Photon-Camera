package android.hardware.camera2;
import java.util.HashMap;
public class CaptureRequest {public static final class Key<T>{}
 public static final Key<Integer> CONTROL_AE_MODE=new Key<>();
 public static final Key<Long> SENSOR_EXPOSURE_TIME=new Key<>();
 public static final Key<Integer> SENSOR_SENSITIVITY=new Key<>();
 public static final int CONTROL_AE_MODE_OFF=0;
 public static class Builder {private final HashMap<Key<?>,Object> m=new HashMap<>(); public <T> void set(Key<T>k,T v){m.put(k,v);} public <T>T get(Key<T>k){return (T)m.get(k);}}
}

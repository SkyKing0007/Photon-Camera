package com.particlesdevs.photoncamera.ui.settings.custompreferences;
import android.content.Context;
import android.util.AttributeSet;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.settings.Iris26995SuperResDenoiseSettings;
/** Inherits the exact Noise Reduction switch layout, tints and appearance. */
public final class Iris26995SuperResDenoisePreference extends ManagedSwitchPreference {
    private boolean rebinding;
    public Iris26995SuperResDenoisePreference(Context context,AttributeSet attrs){super(context,attrs);}
    @Override public boolean getPersistedBoolean(boolean fallback){return Iris26995SuperResDenoiseSettings.read(getContext(),PreferenceKeys.getCameraID());}
    @Override public boolean persistBoolean(boolean value){return rebinding || Iris26995SuperResDenoiseSettings.write(getContext(),PreferenceKeys.getCameraID(),value);}
    public void refreshForSelectedLens(){rebinding=true;try{setChecked(getPersistedBoolean(false));}finally{rebinding=false;}}
}

package com.particlesdevs.photoncamera.ui.settings.custompreferences;

import android.content.Context;
import android.util.AttributeSet;
import androidx.annotation.NonNull;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.settings.Iris26982CSharpenSettings;

/** Identical UniversalSeekBarPreference appearance/dialog; C-only finite 0.1 step validation. */
public final class Iris26982CBandPreference extends UniversalSeekBarPreference {
    public Iris26982CBandPreference(Context context, AttributeSet attrs) { super(context, attrs); }
    public Iris26982CBandPreference(Context context) { super(context); }
    @Override protected boolean persistString(String value) {
        if (!Iris26982CSharpenSettings.valid(value)) {
            PhotonCamera.showToast("Use a value 0.0–2.0 in steps of 0.1");
            // A rejected precise value is never persisted. Rebind from the retained value.
            notifyChanged();
            return false;
        }
        return super.persistString(value);
    }
}

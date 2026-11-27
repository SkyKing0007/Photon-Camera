package com.particlesdevs.photoncamera.ui.settings.custompreferences;

import android.content.Context;
import android.util.AttributeSet;
import androidx.preference.EditTextPreference;

public class BackupPreferences extends EditTextPreference {
    public BackupPreferences(Context context, AttributeSet attrs) {
        super(context, attrs);
        setPersistent(false);
        setDialogMessage("Settings will be exported to XML format (includes per-lens settings)");
        setOnBindEditTextListener(editText -> editText.setText(""));
    }
}

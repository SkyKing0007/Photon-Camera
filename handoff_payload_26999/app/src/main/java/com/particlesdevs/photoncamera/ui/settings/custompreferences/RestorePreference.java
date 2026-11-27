package com.particlesdevs.photoncamera.ui.settings.custompreferences;

import android.content.Context;
import android.util.AttributeSet;
import android.widget.Toast;
import androidx.preference.ListPreference;
import com.particlesdevs.photoncamera.util.SimpleStorageHelper;

public class RestorePreference extends ListPreference {
    public RestorePreference(Context context, AttributeSet attrs) {
        super(context, attrs);
        setPersistent(false);
    }

    @Override protected void onClick() {
            Context context = getContext();
            String[] names = SimpleStorageHelper.listBackupFileNames(context);
            setEntries(names);
            setEntryValues(names);
            setValue(null);
            if (names.length == 0) {
                Toast.makeText(context, "No XML configurations in Configs", Toast.LENGTH_SHORT).show();
                return;
            }
            super.onClick();
    }
}

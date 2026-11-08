package com.particlesdevs.photoncamera.ui.settings.custompreferences;

import android.content.Context;
import android.util.AttributeSet;

/**
 * Preserve the standard Iris managed-switch appearance while preventing its
 * global SettingsManager persistence override from writing a lens-specific
 * setting to the global preference namespace. The actual owner is the
 * 26856 physical-lens store, snapshotted only at shutter press.
 */
public final class Iris26912PerLensHighlightSwitch extends ManagedSwitchPreference {
    public Iris26912PerLensHighlightSwitch(Context context) { super(context); }
    public Iris26912PerLensHighlightSwitch(Context context, AttributeSet attrs) {
        super(context, attrs);
    }
    public Iris26912PerLensHighlightSwitch(Context context, AttributeSet attrs, int style) {
        super(context, attrs, style);
    }
    @Override public boolean getPersistedBoolean(boolean defaultValue) { return defaultValue; }
    @Override public boolean persistBoolean(boolean value) { return false; }
}

package com.particlesdevs.photoncamera.ui.settings.custompreferences;

import android.app.AlertDialog;
import android.content.Context;
import android.text.InputType;
import android.widget.EditText;
import android.widget.SeekBar;
import android.widget.TextView;
import android.widget.LinearLayout;
import android.view.View;

import androidx.annotation.NonNull;
import androidx.preference.Preference;
import androidx.preference.PreferenceViewHolder;

import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.settings.Iris26926FallbackSettings;

import java.util.Locale;

/** Reuses the existing preference_seekbar layout/fonts, no binder-triggered persistence. */
public final class Iris26926FallbackSliderPreference extends Preference {
    private final String physicalLens;
    private final int parameter;
    private SeekBar bar;
    private TextView value;

    public Iris26926FallbackSliderPreference(Context context, String physicalLens, int parameter) {
        super(context);
        this.physicalLens = physicalLens;
        this.parameter = parameter;
        setLayoutResource(R.layout.preference_seekbar);
        setPersistent(false);
    }
    private static String display(int steps) {
        return String.format(Locale.US, "%.2f", steps * 0.25f);
    }
    private void update(int steps, boolean write) {
        if (write) Iris26926FallbackSettings.writeSteps(getContext(), physicalLens, parameter, steps);
        if (bar != null && bar.getProgress() != steps) bar.setProgress(steps);
        if (value != null) value.setText(display(steps));
    }
    @Override public void onBindViewHolder(@NonNull PreferenceViewHolder holder) {
        super.onBindViewHolder(holder);
        holder.setDividerAllowedAbove(false);
        bar = (SeekBar) holder.findViewById(R.id.seekbar);
        value = (TextView) holder.findViewById(R.id.seekbar_value);
        if (bar == null || value == null) throw new IllegalStateException("26926 missing original seekbar layout");
        bar.setOnSeekBarChangeListener(null);
        bar.setMax(Iris26926FallbackSettings.maxSteps(parameter));
        update(Iris26926FallbackSettings.readSteps(getContext(), physicalLens, parameter), false);
        bar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar b, int progress, boolean fromUser) {
                if (!fromUser) return;
                if (PhotonCamera.getVibration() != null) PhotonCamera.getVibration().Tick();
                update(progress, true);
            }
            @Override public void onStartTrackingTouch(SeekBar b) { }
            @Override public void onStopTrackingTouch(SeekBar b) { }
        });
        value.setVisibility(View.VISIBLE);
        value.setOnClickListener(v -> preciseEntry());
    }
    private void preciseEntry() {
        final Context context = getContext();
        final EditText input = new EditText(context);
        input.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        input.setText(display(Iris26926FallbackSettings.readSteps(context, physicalLens, parameter)));
        input.setSelectAllOnFocus(true);
        final LinearLayout content = new LinearLayout(context);
        content.setPadding(50, 20, 50, 20);
        content.addView(input);
        new AlertDialog.Builder(context)
                .setTitle(getTitle())
                .setMessage("0.25 increments, range 0.00 to " +
                        display(Iris26926FallbackSettings.maxSteps(parameter)) +
                        "; default " + display(Iris26926FallbackSettings.defaultSteps(parameter)))
                .setView(content)
                .setPositiveButton("Set", (dialog, which) -> {
                    try {
                        float requested = Float.parseFloat(input.getText().toString().trim());
                        if (!Iris26926FallbackSettings.isValid(requested, parameter))
                            throw new IllegalArgumentException("not a valid 0.25 increment");
                        update(Math.round(requested * 4f), true);
                    } catch (RuntimeException bad) {
                        PhotonCamera.showToast("Enter a valid value in 0.25 increments");
                    }
                })
                .setNegativeButton("Cancel", null).show();
    }
}

package com.particlesdevs.photoncamera.ui.settings.custompreferences;

import android.app.AlertDialog;
import android.content.Context;
import android.content.res.TypedArray;
import android.text.InputType;
import android.util.AttributeSet;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.preference.Preference;
import androidx.preference.PreferenceViewHolder;

import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.control.Vibration;

import java.util.Locale;

/**
 * IRIS_26408_IQ_STRING_PERSISTENCE_FIX
 *
 * Motion-IQ-only seekbar.
 *
 * Why it exists:
 * - Photon SettingsManager stores settings as Strings.
 * - The generic UniversalSeekBarPreference writes Strings, but it also
 *   quantizes and re-persists values while binding/initializing.
 * - Its float->progress conversion truncates binary float error, so values
 *   such as 1.30 can become 1.25 and repeated binds can walk values downward.
 *
 * This class never writes while merely binding/reopening. User drag writes
 * the selected grid value; precise-entry writes the exact entered value.
 */
public final class MotionIqLabSeekBarPreference extends Preference
        implements SeekBar.OnSeekBarChangeListener {

    private final Vibration vibration;
    private final float mMin;
    private final float mMax;
    private final boolean isFloat;
    private final boolean showSeekBarValue;
    private float mStepPerUnit;
    private int seekBarProgress;
    private TextView seekBarValue;
    private SeekBar seekBar;
    private String fallbackValue;

    public MotionIqLabSeekBarPreference(
            Context context, AttributeSet attrs, int defStyleAttr, int defStyleRes) {
        super(context, attrs, defStyleAttr, defStyleRes);
        TypedArray a = context.obtainStyledAttributes(
                attrs, R.styleable.UniversalSeekBarPreference, defStyleAttr, defStyleRes);
        vibration = PhotonCamera.getVibration();
        mMax = a.getFloat(R.styleable.UniversalSeekBarPreference_maxValue, 100.0f);
        mMin = a.getFloat(R.styleable.UniversalSeekBarPreference_minValue, 0.0f);
        mStepPerUnit = a.getFloat(R.styleable.UniversalSeekBarPreference_stepPerUnit, 1.0f);
        showSeekBarValue =
                a.getBoolean(R.styleable.UniversalSeekBarPreference_showSeekBarValue, true);
        isFloat = a.getBoolean(R.styleable.UniversalSeekBarPreference_isFloat, false);
        if (!isFloat && mStepPerUnit > 1.0f) {
            mStepPerUnit = 1.0f;
        }
        a.recycle();
    }

    public MotionIqLabSeekBarPreference(Context context, AttributeSet attrs, int defStyleAttr) {
        this(context, attrs, defStyleAttr, 0);
    }

    public MotionIqLabSeekBarPreference(Context context, AttributeSet attrs) {
        this(context, attrs, 0);
    }

    public MotionIqLabSeekBarPreference(Context context) {
        this(context, null);
    }

    @Override
    protected Object onGetDefaultValue(TypedArray a, int index) {
        fallbackValue = a.getString(index);
        return fallbackValue;
    }

    @Override
    protected void onSetInitialValue(Object defaultValue) {
        if (fallbackValue == null && defaultValue != null) {
            fallbackValue = defaultValue.toString();
        }
        // Deliberately do not persist or quantize here.
    }

    @Override
    public void onBindViewHolder(@NonNull PreferenceViewHolder holder) {
        super.onBindViewHolder(holder);
        holder.setDividerAllowedAbove(false);

        seekBar = (SeekBar) holder.findViewById(R.id.seekbar);
        seekBarValue = (TextView) holder.findViewById(R.id.seekbar_value);

        seekBar.setMax(Math.max(0, Math.round((mMax - mMin) * mStepPerUnit)));
        seekBar.setOnSeekBarChangeListener(this);

        String stored = getPersistedString(fallbackValue);
        if (stored == null) {
            stored = isFloat ? Float.toString(mMin) : Integer.toString((int) mMin);
        }

        float value;
        try {
            value = Float.parseFloat(stored);
        } catch (NumberFormatException e) {
            value = fallbackValue != null ? Float.parseFloat(fallbackValue) : mMin;
            stored = formatExact(value);
        }

        value = clamp(value, mMin, mMax);
        int progress = valueToProgress(value);
        seekBarProgress = progress;
        updateSeekbar(progress);
        updateLabel(formatExact(value));

        if (seekBarValue != null) {
            seekBarValue.setOnClickListener(v -> showPreciseValueDialog());
        }
    }

    @Override
    public void onProgressChanged(SeekBar bar, int progress, boolean fromUser) {
        if (!fromUser) return;
        vibration.Tick();

        seekBarProgress = progress;
        String value = convertToValue(progress);
        updateLabel(value);
        persistString(value);
    }

    @Override
    public void onStartTrackingTouch(SeekBar seekBar) {}

    @Override
    public void onStopTrackingTouch(SeekBar seekBar) {}

    private int valueToProgress(float value) {
        int maxProgress = Math.max(0, Math.round((mMax - mMin) * mStepPerUnit));
        int progress = Math.round((value - mMin) * mStepPerUnit);
        return Math.max(0, Math.min(maxProgress, progress));
    }

    private String convertToValue(int progress) {
        float value = (float) progress / mStepPerUnit + mMin;
        return isFloat
                ? String.format(Locale.ROOT, "%.2f", value)
                : Integer.toString((int) value);
    }

    private String formatExact(float value) {
        if (!isFloat) return Integer.toString((int) value);
        return String.format(Locale.ROOT, "%.10f", value)
                .replaceAll("0+$", "")
                .replaceAll("\\.$", "");
    }

    private void setDirectValue(float value) {
        value = clamp(value, mMin, mMax);
        String exact = formatExact(value);
        int progress = valueToProgress(value);

        seekBarProgress = progress;
        updateSeekbar(progress);
        updateLabel(exact);
        persistString(exact);
    }

    private void updateLabel(String value) {
        if (seekBarValue == null) return;
        if (showSeekBarValue) {
            seekBarValue.setVisibility(android.view.View.VISIBLE);
            seekBarValue.setText(value);
        } else {
            seekBarValue.setVisibility(android.view.View.GONE);
        }
    }

    private void updateSeekbar(int progress) {
        if (seekBar != null) seekBar.setProgress(progress);
    }

    private static float clamp(float v, float lo, float hi) {
        return Math.max(lo, Math.min(hi, v));
    }

    private void showPreciseValueDialog() {
        Context context = getContext();
        if (context == null) return;

        String persisted = getPersistedString(fallbackValue);
        float currentValue;
        try {
            currentValue = Float.parseFloat(persisted);
        } catch (Throwable t) {
            currentValue = fallbackValue != null ? Float.parseFloat(fallbackValue) : mMin;
        }
        float defaultValue =
                fallbackValue != null ? Float.parseFloat(fallbackValue) : currentValue;

        AlertDialog.Builder builder = new AlertDialog.Builder(context);
        builder.setTitle(getTitle());
        builder.setMessage(
                "Enter precise value (" + formatExact(mMin) + " - " + formatExact(mMax)
                        + ")\nDefault: " + formatExact(defaultValue));

        final EditText input = new EditText(context);
        input.setInputType(
                InputType.TYPE_CLASS_NUMBER
                        | (isFloat ? InputType.TYPE_NUMBER_FLAG_DECIMAL : 0)
                        | InputType.TYPE_NUMBER_FLAG_SIGNED);
        input.setText(formatExact(currentValue));
        input.setSelectAllOnFocus(true);

        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
        lp.setMargins(50, 20, 50, 20);
        input.setLayoutParams(lp);

        LinearLayout container = new LinearLayout(context);
        container.setOrientation(LinearLayout.VERTICAL);
        container.addView(input);
        builder.setView(container);

        builder.setPositiveButton("Set", (dialog, which) -> {
            try {
                float value = Float.parseFloat(input.getText().toString());
                setDirectValue(value);
            } catch (NumberFormatException e) {
                PhotonCamera.showToast("Invalid number format");
            }
        });

        builder.setNeutralButton("Reset", (dialog, which) -> {
            setDirectValue(defaultValue);
            PhotonCamera.showToast("Reset to default: " + formatExact(defaultValue));
        });

        builder.setNegativeButton("Cancel", (dialog, which) -> dialog.cancel());

        AlertDialog dialog = builder.create();
        dialog.show();
        input.requestFocus();
    }
}
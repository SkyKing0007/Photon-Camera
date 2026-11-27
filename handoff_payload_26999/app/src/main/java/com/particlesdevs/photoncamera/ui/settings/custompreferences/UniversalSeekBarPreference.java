package com.particlesdevs.photoncamera.ui.settings.custompreferences;

import android.app.AlertDialog;
import android.content.Context;
import android.content.res.TypedArray;
import android.text.InputType;
import android.util.AttributeSet;
import com.particlesdevs.photoncamera.util.Log;
import android.view.View;
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
 * Created by vibhorSrv on 12/09/2020
 */
public class UniversalSeekBarPreference extends Preference implements SeekBar.OnSeekBarChangeListener {
    private static final String TAG = "UnivSeekBarPref";
    private static final boolean isLoggingOn = false;
    private final Vibration vibration;
    private final float mMin, mMax;
    private final boolean isFloat, showSeekBarValue;
    private float mStepPerUnit;
    private int seekBarProgress;
    private TextView seekBarValue;
    private SeekBar seekBar;
    private String fallback_value;
    // IRIS_26556_MODE_SPECIFIC_SLIDER_VIEW_CAP: affects only what this preference view can
    // display/edit. It never rewrites a larger persisted global value merely because the view
    // was opened in a mode with a lower effective maximum.
    private Float runtimeMaxValue = null;

    public UniversalSeekBarPreference(Context context, AttributeSet attrs, int defStyleAttr, int defStyleRes) {
        super(context, attrs, defStyleAttr, defStyleRes);
        TypedArray a = context.obtainStyledAttributes(
                attrs, R.styleable.UniversalSeekBarPreference, defStyleAttr, defStyleRes);
        vibration = PhotonCamera.getVibration();
        mMax = a.getFloat(R.styleable.UniversalSeekBarPreference_maxValue, 100.0f);
        mMin = a.getFloat(R.styleable.UniversalSeekBarPreference_minValue, 0.0f);
        mStepPerUnit = a.getFloat(R.styleable.UniversalSeekBarPreference_stepPerUnit, 1.0f);
        showSeekBarValue = a.getBoolean(R.styleable.UniversalSeekBarPreference_showSeekBarValue, true);
        isFloat = a.getBoolean(R.styleable.UniversalSeekBarPreference_isFloat, false);
        if (!isFloat && mStepPerUnit > 1)
            mStepPerUnit = 1.0f;
        a.recycle();
    }

    public UniversalSeekBarPreference(Context context, AttributeSet attrs, int defStyleAttr) {
        this(context, attrs, defStyleAttr, 0);
    }

    public UniversalSeekBarPreference(Context context, AttributeSet attrs) {
        this(context, attrs, 0);
    }

    public UniversalSeekBarPreference(Context context) {
        this(context, null);
    }

    private void log(String msg) {
        if (isLoggingOn)
            Log.d(TAG + getKey(), msg);
    }

    @Override
    public void onBindViewHolder(@NonNull PreferenceViewHolder holder) {
//        log("onBindViewHolder");
        super.onBindViewHolder(holder);
        holder.setDividerAllowedAbove(false);
        seekBar = (SeekBar) holder.findViewById(R.id.seekbar);
        seekBarValue = (TextView) holder.findViewById(R.id.seekbar_value);
        final float effectiveMax = getEffectiveMax();
        seekBar.setMax((int) ((effectiveMax - mMin) * mStepPerUnit));
        seekBar.setOnSeekBarChangeListener(this);
        if (runtimeMaxValue == null) {
            set(convertToProgress(fallback_value));
        } else {
            // Render a mode-limited view without persisting the clamped display value.
            float persisted = Float.parseFloat(getPersistedString(fallback_value));
            float display = Math.max(mMin, Math.min(effectiveMax, persisted));
            int progress = (int) ((display - mMin) * mStepPerUnit);
            seekBarProgress = progress;
            updateLabel(formatValue(display));
            updateSeekbar(progress);
        }
        
        // Add click listener for precise value input on the value text
        if (seekBarValue != null) {
            seekBarValue.setOnClickListener(v -> showPreciseValueDialog());
        }
    }

    @Override
    public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
        if(fromUser) vibration.Tick();
        if (fromUser) {
            set(progress);
        }
    }

    @Override
    public void onStartTrackingTouch(SeekBar seekBar) {

    }

    @Override
    public void onStopTrackingTouch(SeekBar seekBar) {

    }

    @Override
    protected void onSetInitialValue(Object defaultValue) {
//        log("onSetInitialValue : " + defaultValue);
        if (defaultValue == null) {
            defaultValue = fallback_value;
        }
        set(convertToProgress(defaultValue.toString()));
    }

    @Override
    protected Object onGetDefaultValue(TypedArray a, int index) {
        fallback_value = a.getString(index);
        log("onGetDefaultValue : " + fallback_value);
        return a.getString(index);
    }

    private void set(int progress) {
        seekBarProgress = progress;
        String valueToPersist = convertToValue(progress);
        updateLabel(valueToPersist);
        updateSeekbar(progress);
        persistString(valueToPersist);
        log("set : " + valueToPersist);
    }
    
    public void setRuntimeMaxValue(float value) {
        runtimeMaxValue = Math.max(mMin, Math.min(mMax, value));
        notifyChanged();
    }

    private float getEffectiveMax() {
        return runtimeMaxValue == null ? mMax : runtimeMaxValue;
    }

    private String formatValue(float value) {
        return isFloat
                ? String.format(Locale.ROOT, "%.10f", value).replaceAll("0+$", "").replaceAll("\\.$", "")
                : String.valueOf((int) value);
    }

    private void setDirectValue(float value) {
        // Set value directly without step quantization - for manual input
        String valueToPersist = isFloat ? 
            String.format(Locale.ROOT, "%.10f", value).replaceAll("0+$", "").replaceAll("\\.$", "") :
            String.valueOf((int) value);
        
        // Update seekbar to closest step position
        int progress = (int) ((value - mMin) * mStepPerUnit);
        seekBarProgress = progress;
        
        updateLabel(valueToPersist);
        updateSeekbar(progress);
        persistString(valueToPersist);
        log("setDirectValue : " + valueToPersist);
    }

    private boolean isCSharpeningBand() {
        String key = getKey();
        return key != null && (key.equals("pref_iris_26982_c_mgc_band_0")
                || key.equals("pref_iris_26982_c_mgc_band_1")
                || key.equals("pref_iris_26982_c_mgc_band_2"));
    }

    private void updateLabel(String valueToPersist) {
        if (seekBarValue != null) {
            if (showSeekBarValue) {
                seekBarValue.setVisibility(View.VISIBLE);
                seekBarValue.setText(isCSharpeningBand()
                        ? String.format(Locale.ROOT, "%.2f", Float.parseFloat(valueToPersist))
                        : valueToPersist);
            } else
                seekBarValue.setVisibility(View.GONE);
        }
    }

    private void updateSeekbar(int progress) {
        if (seekBar != null)
            seekBar.setProgress(progress);
    }

    private int convertToProgress(String defValue) {
        return (int) ((Float.parseFloat(getPersistedString(defValue)) - mMin) * mStepPerUnit);
    }

    private String convertToValue(int progress) {
        if (isFloat)
            return String.format(Locale.ROOT, "%.2f", (float) progress / mStepPerUnit + mMin);
        else
            return String.valueOf((int) ((float) progress / mStepPerUnit + mMin));
    }

    public String getValue() {
        return getPersistedString(fallback_value);
    }

    public int getSeekBarProgress() {
        return seekBarProgress;
    }

    public SeekBar getSeekBar() {
        return seekBar;
    }
    
    private void showPreciseValueDialog() {
        Context context = getContext();
        if (context == null) return;
        
        // Get current value
        final float effectiveMax = getEffectiveMax();
        float currentValue = Math.max(mMin, Math.min(effectiveMax,
                Float.parseFloat(getPersistedString(fallback_value))));
        String currentValueText = isFloat ? 
            String.format(Locale.ROOT, "%.10f", currentValue).replaceAll("0+$", "").replaceAll("\\.$", "") :
            String.valueOf((int) currentValue);
        
        // Get default value
        float defaultValue = Math.max(mMin, Math.min(effectiveMax,
                Float.parseFloat(fallback_value)));
        
        // Create input dialog
        AlertDialog.Builder builder = new AlertDialog.Builder(context);
        builder.setTitle(getTitle());
        builder.setMessage("Enter precise value (" + 
            String.format(Locale.ROOT, isFloat ? "%.10f" : "%.0f", mMin).replaceAll("0+$", "").replaceAll("\\.$", "") + " - " +
            String.format(Locale.ROOT, isFloat ? "%.10f" : "%.0f", effectiveMax).replaceAll("0+$", "").replaceAll("\\.$", "") +
            ")\nDefault: " + 
            String.format(Locale.ROOT, isFloat ? "%.10f" : "%.0f", defaultValue).replaceAll("0+$", "").replaceAll("\\.$", ""));
        
        // Create input field
        final EditText input = new EditText(context);
        input.setInputType(InputType.TYPE_CLASS_NUMBER | 
            (isFloat ? InputType.TYPE_NUMBER_FLAG_DECIMAL : 0) | 
            InputType.TYPE_NUMBER_FLAG_SIGNED);
        
        input.setText(isCSharpeningBand() ? String.format(Locale.ROOT, "%.2f", currentValue) : currentValueText);
        input.setSelectAllOnFocus(true);
        
        // Add padding
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
                String valueStr = input.getText().toString();
                float value = Float.parseFloat(valueStr);
                
                // Clamp to min/max
                if (value < mMin) {
                    value = mMin;
                    PhotonCamera.showToast("Value clamped to minimum: " + mMin);
                } else if (value > effectiveMax) {
                    value = effectiveMax;
                    PhotonCamera.showToast("Value clamped to maximum: " + effectiveMax);
                }
                
                // Set the exact value directly - bypasses step quantization
                setDirectValue(value);
                
                Log.d(TAG, "Set precise value: " + value + " for " + getKey());
            } catch (NumberFormatException e) {
                PhotonCamera.showToast("Invalid number format");
                Log.w(TAG, "Invalid input: " + input.getText().toString());
            }
        });
        
        builder.setNeutralButton("Reset", (dialog, which) -> {
            // Reset to exact default value - preserves precision
            setDirectValue(defaultValue);
            
            PhotonCamera.showToast("Reset to default: " + defaultValue);
            Log.d(TAG, "Reset to default: " + defaultValue + " for " + getKey());
        });
        
        builder.setNegativeButton("Cancel", (dialog, which) -> dialog.cancel());
        
        AlertDialog dialog = builder.create();
        dialog.show();
        
        // Request keyboard
        input.requestFocus();
    }

}
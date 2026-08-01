/*
 *
 *  PhotonCamera / Iris Camera UI
 *  AuxButtonsLayout.java
 *
 */

package com.particlesdevs.photoncamera.ui.camera.views;

import android.content.Context;
import android.util.AttributeSet;
import android.util.TypedValue;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;

import androidx.annotation.Nullable;

import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.ui.camera.binding.CustomBinding;
import com.particlesdevs.photoncamera.ui.camera.data.CameraLensData;
import com.particlesdevs.photoncamera.ui.camera.model.AuxButtonsModel;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;

/**
 * Compact horizontal optical-lens selector.
 */
public class AuxButtonsLayout extends LinearLayout {
    private static final Comparator<CameraLensData> SORT_BY_ZOOM_FACTOR =
            Comparator.comparingDouble(CameraLensData::getZoomFactor)
                    .thenComparing(CameraLensData::getCameraId);

    private final HashMap<Integer, String> auxButtonsMap =
            new HashMap<>();

    private AuxButtonListener auxButtonListener;
    private AuxButtonsModel auxButtonsModel;

    public AuxButtonsLayout(
            Context context,
            @Nullable AttributeSet attrs
    ) {
        super(context, attrs);
    }

    private static String getAuxButtonName(
            float zoomFactor
    ) {
        return String.format(
                Locale.US,
                "%.1fx",
                zoomFactor - 0.049f
        ).replace(".0", "");
    }

    public void setAuxButtonsModel(
            AuxButtonsModel auxButtonsModel
    ) {
        this.auxButtonsModel =
                auxButtonsModel;

        auxButtonListener =
                auxButtonsModel
                        .getAuxButtonListener();
    }

    public void setActiveId(String activeId) {
        refresh(activeId);
    }

    private void refresh(String cameraId) {
        if (auxButtonsModel == null) {
            return;
        }

        List<CameraLensData> front =
                auxButtonsModel
                        .getFrontCameras();

        List<CameraLensData> back =
                auxButtonsModel
                        .getBackCameras();

        if (front == null
                || back == null) {
            return;
        }

        if (!isFront(cameraId, front)) {
            setAuxButtons(
                    back,
                    cameraId
            );
        } else {
            setAuxButtons(
                    front,
                    cameraId
            );
        }
    }

    private boolean isFront(
            String cameraId,
            List<CameraLensData> frontCameras
    ) {
        return frontCameras.stream().anyMatch(
                cameraLensData ->
                        cameraLensData
                                .getCameraId()
                                .equals(cameraId)
        );
    }

    private void setAuxButtons(
            List<CameraLensData> source,
            String activeId
    ) {
        removeAllViews();
        auxButtonsMap.clear();

        List<CameraLensData> ordered =
                new ArrayList<>(source);

        ordered.sort(
                SORT_BY_ZOOM_FACTOR
        );

        for (CameraLensData cameraLensData
                : ordered) {
            addNewButton(
                    cameraLensData
                            .getCameraId(),
                    getAuxButtonName(
                            cameraLensData
                                    .getZoomFactor()
                    )
            );
        }

        setListenerAndSelected(
                activeId
        );

        updateVisibility();
    }

    private void setListenerAndSelected(
            String activeId
    ) {
        View.OnClickListener listener =
                this::onAuxButtonClick;

        for (int index = 0;
                index < getChildCount();
                index++) {
            View button =
                    getChildAt(index);

            button.setOnClickListener(
                    listener
            );

            boolean selected =
                    activeId.equals(
                            auxButtonsMap.get(
                                    button.getId()
                            )
                    );

            button.setSelected(
                    selected
            );
        }
    }

    private void updateVisibility() {
        setVisibility(
                getChildCount() > 1
                        ? View.VISIBLE
                        : View.INVISIBLE
        );
    }

    private void onAuxButtonClick(
            View view
    ) {
        if (!auxButtonsModel.isEnabled()) {
            return;
        }

        for (int index = 0;
                index < getChildCount();
                index++) {
            View child =
                    getChildAt(index);

            child.setSelected(
                    view.equals(child)
            );
        }

        if (auxButtonListener != null) {
            auxButtonListener
                    .onAuxButtonClicked(
                            auxButtonsMap.get(
                                    view.getId()
                            )
                    );
        }
    }

    private void addNewButton(
            String cameraId,
            String buttonText
    ) {
        Button button =
                new Button(getContext());

        LayoutParams params =
                new LayoutParams(
                        LayoutParams.WRAP_CONTENT,
                        dp(38)
                );

        params.setMargins(
                dp(2),
                0,
                dp(2),
                0
        );

        button.setLayoutParams(
                params
        );

        button.setMinWidth(
                dp(42)
        );

        button.setMinimumWidth(
                dp(42)
        );

        button.setPadding(
                dp(8),
                0,
                dp(8),
                0
        );

        button.setText(
                buttonText
        );

        button.setTextAppearance(
                R.style.AuxButtonText
        );

        button.setTextColor(
                getResources().getColorStateList(
                        R.color.iris_lens_text,
                        getContext().getTheme()
                )
        );

        button.setBackgroundResource(
                R.drawable
                        .iris_lens_button_background
        );

        button.setStateListAnimator(null);
        button.setTransformationMethod(null);
        button.setAllCaps(false);

        int buttonId =
                View.generateViewId();

        button.setId(
                buttonId
        );

        auxButtonsMap.put(
                buttonId,
                cameraId
        );

        addView(
                button
        );
    }

    private int dp(float value) {
        return Math.round(
                TypedValue.applyDimension(
                        TypedValue.COMPLEX_UNIT_DIP,
                        value,
                        getResources()
                                .getDisplayMetrics()
                )
        );
    }

    public interface AuxButtonListener {
        void onAuxButtonClicked(
                String cameraId
        );
    }
}

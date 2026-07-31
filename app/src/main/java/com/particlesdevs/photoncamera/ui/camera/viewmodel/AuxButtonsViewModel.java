/*
 *
 *  PhotonCamera / Iris Camera UI
 *  AuxButtonsViewModel.java
 *
 */

package com.particlesdevs.photoncamera.ui.camera.viewmodel;

import android.hardware.camera2.CameraCharacteristics;

import androidx.lifecycle.ViewModel;

import com.particlesdevs.photoncamera.ui.camera.CameraFragment;
import com.particlesdevs.photoncamera.ui.camera.data.CameraLensData;
import com.particlesdevs.photoncamera.ui.camera.model.AuxButtonsModel;
import com.particlesdevs.photoncamera.ui.camera.views.AuxButtonsLayout;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

/**
 * ViewModel which connects {@link AuxButtonsModel} with {@link CameraFragment}.
 *
 * Lens buttons are always sorted from the lowest optical zoom factor to the
 * highest. This gives 0.6x, 1x, 3x, 4.1x on the current device while staying
 * data-driven for other OEM camera arrangements.
 */
public class AuxButtonsViewModel extends ViewModel {
    private static final Comparator<CameraLensData> SORT_BY_ZOOM_FACTOR =
            Comparator.comparingDouble(CameraLensData::getZoomFactor)
                    .thenComparing(CameraLensData::getCameraId);

    private final AuxButtonsModel auxButtonsModel =
            new AuxButtonsModel();

    private boolean initialized = false;
    private boolean isEnabled = true;

    public void initCameraLists(
            Map<String, CameraLensData> cameraLensDataMap
    ) {
        if (!initialized) {
            List<CameraLensData> frontCameras =
                    new ArrayList<>();

            List<CameraLensData> backCameras =
                    new ArrayList<>();

            cameraLensDataMap.forEach(
                    (id, cameraLensData) -> {
                        if (cameraLensData.getFacing()
                                == CameraCharacteristics
                                        .LENS_FACING_BACK) {
                            backCameras.add(
                                    cameraLensData
                            );
                        } else if (
                                cameraLensData.getFacing()
                                        == CameraCharacteristics
                                                .LENS_FACING_FRONT
                        ) {
                            frontCameras.add(
                                    cameraLensData
                            );
                        }
                    }
            );

            backCameras.sort(
                    SORT_BY_ZOOM_FACTOR
            );

            frontCameras.sort(
                    SORT_BY_ZOOM_FACTOR
            );

            auxButtonsModel.setBackCameras(
                    backCameras
            );

            auxButtonsModel.setFrontCameras(
                    frontCameras
            );

            initialized = true;
        }
    }

    public void setAuxButtonListener(
            AuxButtonsLayout.AuxButtonListener auxButtonListener
    ) {
        auxButtonsModel.setAuxButtonListener(
                auxButtonListener
        );
    }

    public boolean isEnabled() {
        return isEnabled;
    }

    public void setEnabled(boolean enabled) {
        isEnabled = enabled;
        auxButtonsModel.setEnabled(enabled);
    }

    public void setActiveId(String cameraId) {
        auxButtonsModel.setCurrentCameraId(
                cameraId
        );
    }

    public AuxButtonsModel getAuxButtonsModel() {
        return auxButtonsModel;
    }
}

/*
 *
 *  PhotonCamera
 *  SettingsBarEntryProvider.java
 *  Copyright (C) 2020 - 2021  Vibhor Srivastava
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <https://www.gnu.org/licenses/>.
 * /
 */

package com.particlesdevs.photoncamera.ui.camera.viewmodel;

import androidx.lifecycle.Observer;
import androidx.lifecycle.ViewModel;

import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.settings.SettingType;
import com.particlesdevs.photoncamera.ui.camera.model.SettingsBarButtonModel;
import com.particlesdevs.photoncamera.ui.camera.model.SettingsBarEntryModel;
import com.particlesdevs.photoncamera.ui.camera.model.TopBarSettingsData;
import com.particlesdevs.photoncamera.ui.camera.views.settingsbar.SettingsBarLayout;

import java.util.ArrayList;
import java.util.List;

public class SettingsBarEntryProvider extends ViewModel {
    private final SettingsBarEntryModel hdrxEntry = SettingsBarEntryModel.newEntry(R.id.hdrx_entry_layout, R.string.hdrx, SettingType.HDRX);
    private final SettingsBarEntryModel timerEntry = SettingsBarEntryModel.newEntry(R.id.timer_entry_layout, R.string.countdown_timer, SettingType.TIMER);
    private final SettingsBarEntryModel quadEntry = SettingsBarEntryModel.newEntry(R.id.quad_entry_layout, R.string.quad_bayer_toggle_text, SettingType.QUAD);
    private final SettingsBarEntryModel fpsEntry = SettingsBarEntryModel.newEntry(R.id.fps_entry_layout, R.string.fps_60_toggle_text, SettingType.FPS_60);
    private final SettingsBarEntryModel flashEntry = SettingsBarEntryModel.newEntry(R.id.flash_entry_layout, R.string.flash, SettingType.FLASH);
    private final SettingsBarEntryModel gridEntry = SettingsBarEntryModel.newEntry(R.id.grid_entry_layout, R.string.turn_on_grid, SettingType.GRID);
    private final SettingsBarEntryModel eisEntry = SettingsBarEntryModel.newEntry(R.id.eis_entry_layout, R.string.eis_toggle_text, SettingType.EIS);
    /* IRIS_26532_FIXED_2X_SUPER_RES_UI */
    private final SettingsBarEntryModel superResEntry = SettingsBarEntryModel.newEntry(R.id.super_res_entry_layout, R.string.super_res, SettingType.SUPER_RES);
    private final List<SettingsBarEntryModel> allEntries = new ArrayList<>(7);

    public SettingsBarEntryProvider() {
//        allEntries.add(hdrxEntry);
        allEntries.add(flashEntry);
        allEntries.add(timerEntry);
        allEntries.add(quadEntry);
        allEntries.add(eisEntry);
        allEntries.add(fpsEntry);
        allEntries.add(gridEntry);
        allEntries.add(superResEntry);
    }

    public void createEntries() {
        createHdrxEntry();
        createQuadBayerEntry();
        createEisEntry();
        createFlashEntry();
        createFpsEntry();
        createTimerEntry();
        createGridEntry();
        createSuperResEntry();
        updateAllEntries();
    }

    public void updateAllEntries() {
        updateEntry(gridEntry, PreferenceKeys.getGridValue());
        updateEntry(flashEntry, PreferenceKeys.getAeMode());
        updateEntry(timerEntry, PreferenceKeys.getCountdownTimerIndex());
        updateEntry(hdrxEntry, PreferenceKeys.isHdrXOn());
        updateEntry(eisEntry, PreferenceKeys.isEisPhotoOn());
        updateEntry(fpsEntry, PreferenceKeys.getFpsMode());
        updateEntry(quadEntry, PreferenceKeys.isQuadBayerOn());
        updateEntry(superResEntry, PreferenceKeys.isIrisSuperResOn());
    }

    public void addObserver(Observer<TopBarSettingsData<?, ?>> observer) {
        allEntries.forEach(settingsBarEntryModel -> settingsBarEntryModel.getTopBarSettingsData().observeForever(observer));
    }

    public void removeObserver(Observer<TopBarSettingsData<?, ?>> observer) {
        allEntries.forEach(settingsBarEntryModel -> settingsBarEntryModel.getTopBarSettingsData().removeObserver(observer));
    }

    public void addEntries(SettingsBarLayout settingsBarLayout) {
        settingsBarLayout.removeEntries();
        allEntries.forEach(settingsBarLayout::addEntry);
    }

    private void createHdrxEntry() {
        hdrxEntry.addSettingsBarButtonModels(
                SettingsBarButtonModel.newButtonModel(R.id.hdrx_off_button, R.drawable.ic_hdrx_off, R.string.off, 0, hdrxEntry),
                SettingsBarButtonModel.newButtonModel(R.id.hdrx_on_button, R.drawable.ic_hdrx_on, R.string.on, 1, hdrxEntry)
        );
    }

    private void createQuadBayerEntry() {
        quadEntry.addSettingsBarButtonModels(
                SettingsBarButtonModel.newButtonModel(R.id.quad_off_button, R.drawable.ic_quad_off, R.string.off, 0, quadEntry),
                SettingsBarButtonModel.newButtonModel(R.id.quad_on_button, R.drawable.ic_quad_on, R.string.on, 1, quadEntry)
        );
    }

    private void createEisEntry() {
        eisEntry.addSettingsBarButtonModels(
                SettingsBarButtonModel.newButtonModel(R.id.eis_off_button, R.drawable.ic_eis_off, R.string.off, 0, eisEntry),
                SettingsBarButtonModel.newButtonModel(R.id.eis_on_button, R.drawable.ic_eis_on, R.string.on, 1, eisEntry)
        );
    }

    private void createSuperResEntry() {
        /* IRIS_26561_DEDICATED_SUPER_RES_ICONS: keep setting ownership unchanged while making
         * Super Res visually distinct from the Quad Bayer setting. */
        superResEntry.addSettingsBarButtonModels(
                SettingsBarButtonModel.newButtonModel(R.id.super_res_off_button, R.drawable.ic_super_res_off, R.string.off, 0, superResEntry),
                SettingsBarButtonModel.newButtonModel(R.id.super_res_on_button, R.drawable.ic_super_res_on, R.string.on, 1, superResEntry)
        );
    }

    private void createFlashEntry() {
        flashEntry.addSettingsBarButtonModels(
                SettingsBarButtonModel.newButtonModel(R.id.torch_button, R.drawable.ic_torch, R.string.torch, 0, flashEntry),
                SettingsBarButtonModel.newButtonModel(R.id.flash_odd_button, R.drawable.ic_flash_off, R.string.off, 1, flashEntry)
        );
    }

    private void createFpsEntry() {
        fpsEntry.addSettingsBarButtonModels(
                SettingsBarButtonModel.newButtonModel(R.id.fps_auto_button, R.drawable.autofps_select_24px, R.string.fps_auto, 0, fpsEntry),
                SettingsBarButtonModel.newButtonModel(R.id.fps24_button, R.drawable.fps24_select_24px, R.string.fps_24, 1, fpsEntry),
                SettingsBarButtonModel.newButtonModel(R.id.fps30_button, R.drawable.fps30_select_24px, R.string.fps_30, 2, fpsEntry),
                SettingsBarButtonModel.newButtonModel(R.id.fps60_button, R.drawable.fps60_select_24px, R.string.fps_60, 3, fpsEntry)
        );
    }

    private void createTimerEntry() {
        timerEntry.addSettingsBarButtonModels(
                SettingsBarButtonModel.newButtonModel(R.id.timer_off_button, R.drawable.ic_timeroff, R.string.off, 0, timerEntry),
                SettingsBarButtonModel.newButtonModel(R.id.timer3s_button, R.drawable.ic_timer3s, R.string.t_3s, 1, timerEntry),
                SettingsBarButtonModel.newButtonModel(R.id.timer10s_button, R.drawable.ic_timer10s, R.string.t_10s, 2, timerEntry)
        );
    }

    private void createGridEntry() {
        gridEntry.addSettingsBarButtonModels(
                SettingsBarButtonModel.newButtonModel(R.id.grid_off_button, R.drawable.ic_grid_off, R.string.off, 0, gridEntry),
                SettingsBarButtonModel.newButtonModel(R.id.grid_33_button, R.drawable.ic_grid_on, R.string.three_x3, 1, gridEntry),
                SettingsBarButtonModel.newButtonModel(R.id.grid_44_button, R.drawable.ic_grid_on, R.string.four_x4, 2, gridEntry),
                SettingsBarButtonModel.newButtonModel(R.id.grid_gr_button, R.drawable.ic_grid_on, R.string.golden_ratio, 3, gridEntry),
                SettingsBarButtonModel.newButtonModel(R.id.grid_dt_button, R.drawable.ic_grid_on, R.string.diag_triangle, 4, gridEntry)
        );
    }

    private void updateEntry(SettingsBarEntryModel entry, int value) {
        for (SettingsBarButtonModel buttonModel : entry.getSettingsBarButtonModels()) {
            if (buttonModel.getButtonValue() == value) {
                buttonModel.setSelected(true);
                entry.setStateTextStringId(buttonModel.getButtonStateNameStringId());
            } else {
                buttonModel.setSelected(false);
            }
        }
    }

    private void updateEntry(SettingsBarEntryModel entry, boolean value) {
        for (SettingsBarButtonModel buttonModel : entry.getSettingsBarButtonModels()) {
            if ((buttonModel.getButtonValue() == 1) == value) {
                buttonModel.setSelected(true);
                entry.setStateTextStringId(buttonModel.getButtonStateNameStringId());
            } else {
                buttonModel.setSelected(false);
            }
        }
    }
}
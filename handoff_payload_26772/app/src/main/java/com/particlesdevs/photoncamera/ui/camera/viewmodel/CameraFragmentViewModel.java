package com.particlesdevs.photoncamera.ui.camera.viewmodel;

import android.app.Application;
import android.graphics.Bitmap;
import android.graphics.drawable.Drawable;
import android.content.ContentUris;
import android.database.Cursor;
import android.net.Uri;
import android.provider.MediaStore;
import com.particlesdevs.photoncamera.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.AndroidViewModel;

import com.bumptech.glide.Glide;
import com.bumptech.glide.request.target.CustomTarget;
import com.bumptech.glide.request.transition.Transition;
import com.particlesdevs.photoncamera.ui.camera.CustomOrientationEventListener;
import com.particlesdevs.photoncamera.ui.camera.model.CameraFragmentModel;

/**
 * Class get used to update the Models binded to the ui
 * it should not contain any ref to ui
 */
public class CameraFragmentViewModel extends AndroidViewModel {

    private static final String TAG = CameraFragmentViewModel.class.getSimpleName();
    //Model binded to the ui
    private final CameraFragmentModel cameraFragmentModel;
    private volatile Uri latestImageUri; // IRIS_26772_EXTERNAL_GALLERY_THUMB_URI_OWNER
    //listen to device orientation changes
    private CustomOrientationEventListener mCustomOrientationEventListener;


    public CameraFragmentViewModel(@NonNull Application application) {
        super(application);
        cameraFragmentModel = new CameraFragmentModel();
        initOrientationEventListener();
    }

    public CameraFragmentModel getCameraFragmentModel() {
        return cameraFragmentModel;
    }

    public void onResume() {
        mCustomOrientationEventListener.enable();
        cameraFragmentModel.setSettingsBarVisibility(false);
    }

    public void onPause() {
        mCustomOrientationEventListener.disable();
    }

    private void initOrientationEventListener() {
        final int RotationDur = 350;
        final int Rotation90 = 2;
        final int Rotation180 = 3;
        final int Rotation270 = 4;
        mCustomOrientationEventListener = new CustomOrientationEventListener(getApplication()) {
            @Override
            public void onSimpleOrientationChanged(int orientation) {
                int rot = 0;
                switch (orientation) {
                    case Rotation90:
                        rot = -90;
                        //rotate as left on top
                        break;
                    case Rotation270:
                        //rotate as right on top
                        rot = 90;
                        break;
                    case Rotation180:
                        //rotate as upside down
                        rot = 180;
                        break;
                }
                Log.d(TAG, "onSimpleOrientationChanged" + rot);
                cameraFragmentModel.setDuration(RotationDur);
                cameraFragmentModel.setOrientation(rot);

                //mCameraUIView.rotateViews(rot, RotationDur);
                //PhotonCamera.getManualMode().rotate(rot, RotationDur);
            }
        };
    }
    public void updateGalleryThumb(@Nullable Uri uri) {
        Uri lastImageUri = uri != null ? uri : queryLatestImageUri();
        if (lastImageUri != null) {
            latestImageUri = lastImageUri;
            Glide.with(getApplication())
                    .asBitmap()
                    .load(lastImageUri)
                    .override(200)
                    .into(new CustomTarget<Bitmap>() {
                        @Override
                        public void onResourceReady(@NonNull Bitmap resource, @Nullable Transition<? super Bitmap> transition) {
                            cameraFragmentModel.setBitmap(resource);
                        }

                        @Override
                        public void onLoadCleared(@Nullable Drawable placeholder) {

                        }
                    });
        }
    }

    public Uri getLatestImageUri() {
        Uri cached = latestImageUri;
        if (cached != null) return cached;
        cached = queryLatestImageUri();
        latestImageUri = cached;
        return cached;
    }

    private Uri queryLatestImageUri() {
        String[] projection = {MediaStore.Images.Media._ID};
        String sort = MediaStore.Images.Media.DATE_ADDED + " DESC";
        try (Cursor cursor = getApplication().getContentResolver().query(
                MediaStore.Images.Media.EXTERNAL_CONTENT_URI, projection, null, null, sort)) {
            if (cursor != null && cursor.moveToFirst()) {
                return ContentUris.withAppendedId(
                        MediaStore.Images.Media.EXTERNAL_CONTENT_URI, cursor.getLong(0));
            }
        } catch (Throwable ignored) {
            // Thumbnail lookup never blocks CameraActivity; freshly captured URIs update directly.
        }
        return null;
    }

    public void setScreenAspectRatio(float aspectRatio){
        cameraFragmentModel.setScreenAspectRatio(aspectRatio);
    }

    public boolean isSettingsBarVisible() {
        return cameraFragmentModel.isSettingsBarVisibility();
    }

    public void setSettingsBarVisible(boolean visible) {
        cameraFragmentModel.setSettingsBarVisibility(visible);
    }

    @Override
    protected void onCleared() {
        super.onCleared();
    }
}

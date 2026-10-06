package com.particlesdevs.photoncamera.ui.camera.binding;

import android.graphics.Bitmap;
import android.util.DisplayMetrics;
import android.view.View;
import android.view.ViewGroup;
import android.widget.CheckedTextView;
import android.widget.ImageView;

import androidx.constraintlayout.widget.ConstraintLayout;
import androidx.databinding.BindingAdapter;

import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.ui.camera.model.AuxButtonsModel;
import com.particlesdevs.photoncamera.ui.camera.views.AuxButtonsLayout;

/**
 * Class to handle custom bindings that should get applied when a model change
 * <p>
 * Created by KillerInk on 02/Oct/2020
 * Modified by Vibhor
 */
public class CustomBinding {
    private static final long IRIS_ROTATION_DURATION_MS = 350L;


    /**
     * Handle the rotation that should get applied when the CameraFragmentModels rotation change
     * the view item must add attribute 'bindRotate="@{uimodel}"'
     *
     * @param view any view that needs to be rotated
     * @param orientation physical-device presentation rotation
     */
    @BindingAdapter("bindRotate")
    public static void rotateView(View view, int orientation) {
        if (view != null)
            view.animate().rotation(orientation).setDuration(IRIS_ROTATION_DURATION_MS).start();
    }

    /**
     * IRIS_26774_DOWNWARD_RIGHT_BOUND_HISTOGRAM_HINGE_OWNER
     * Keep the portrait histogram rectangle as the geometry authority. Both quarter-turn device
     * orientations must make the pill fall downward into the same right-most vertical strip of
     * that portrait rectangle. The transformed bounds therefore never extend past the portrait
     * right edge and never swing upward/left. Returning to portrait animates translation back to
     * zero before normalizing the dormant pivot, so no positional offset can accumulate.
     */
    @BindingAdapter("bindHistogramRotate")
    public static void rotateHistogram(View view, int orientation) {
        if (view == null) return;
        view.post(() -> {
            view.animate().cancel();
            final float width = view.getWidth();
            final float height = view.getHeight();
            if (width <= 0f || height <= 0f) return;

            if (orientation == -90) {
                // Top-right hinge: rotate downward, then keep the rotated width inside the
                // original portrait right boundary instead of letting it fall off-screen.
                view.setPivotX(width);
                view.setPivotY(0f);
                view.animate()
                        .rotation(-90f)
                        .translationX(-height)
                        .translationY(0f)
                        .setDuration(IRIS_ROTATION_DURATION_MS)
                        .start();
            } else if (orientation == 90) {
                // Bottom-left hinge gives the opposite physical orientation the same downward
                // fall. The translation places its final vertical strip at [width-height,width].
                view.setPivotX(0f);
                view.setPivotY(height);
                view.animate()
                        .rotation(90f)
                        .translationX(width - height)
                        .translationY(-height)
                        .setDuration(IRIS_ROTATION_DURATION_MS)
                        .start();
            } else if (orientation == 0) {
                // Preserve the active quarter-turn hinge while returning so changing the pivot
                // cannot cause an instantaneous jump. Normalize it only after reaching portrait.
                if (view.getRotation() > 0f) {
                    view.setPivotX(0f);
                    view.setPivotY(height);
                } else {
                    view.setPivotX(width);
                    view.setPivotY(0f);
                }
                view.animate()
                        .rotation(0f)
                        .translationX(0f)
                        .translationY(0f)
                        .setDuration(IRIS_ROTATION_DURATION_MS)
                        .withEndAction(() -> {
                            if (view.getRotation() == 0f) {
                                view.setPivotX(view.getWidth());
                                view.setPivotY(0f);
                            }
                        })
                        .start();
            } else {
                // Preserve inherited upside-down behavior; this correction owns quarter turns.
                view.setPivotX(width);
                view.setPivotY(0f);
                view.animate()
                        .rotation(orientation)
                        .translationX(0f)
                        .translationY(0f)
                        .setDuration(IRIS_ROTATION_DURATION_MS)
                        .start();
            }
        });
    }

    /**
     * IRIS_26772_FRONT_CAMERA_PHYSICAL_ROTATION_OWNER
     * Rotate an inner parent with physical orientation so the child arrow can keep its independent
     * tap-to-switch rotationBy(180) animation without competing for the same rotation property.
     */
    @BindingAdapter("bindFrontCameraRotate")
    public static void rotateFrontCamera(View view, int orientation) {
        if (view != null) {
            view.animate().rotation(orientation).setDuration(IRIS_ROTATION_DURATION_MS).start();
        }
    }

    /**
     * IRIS_26772_R3_GALLERY_THUMBNAIL_BITMAP_BINDING_OWNER
     * Surviving owner of the camera bottom-bar thumbnail binding after the legacy Gallery package
     * is removed. This preserves the exact former Gallery imageFromBitmap contract without
     * restoring Gallery ownership.
     */
    @BindingAdapter("imageFromBitmap")
    public static void setImageBitmap(ImageView view, Bitmap bitmap) {
        if (view != null) {
            view.setImageBitmap(bitmap);
        }
    }

    /**
     * Handle the rotation that should get applied to any ViewGroup when the CameraFragmentModels rotation change
     * Only the children views within the ViewGroup will rotate.
     * the ui item must add bindViewGroupChildrenRotate="@{uimodel}"
     *
     * @param viewGroup the container ViewGroup
     * @param orientation physical-device presentation rotation
     */
    @BindingAdapter("bindViewGroupChildrenRotate")
    public static void rotateAuxButtons(ViewGroup viewGroup, int orientation) {
        if (viewGroup != null) {
            for (int i = 0; i < viewGroup.getChildCount(); i++) {
                viewGroup.getChildAt(i).animate().rotation(orientation).setDuration(IRIS_ROTATION_DURATION_MS).start();
            }
        }
    }

    /**
     * Change the selected state of any view
     *
     * @param view     the target view
     * @param selected whether selected
     */
    @BindingAdapter("android:selected")
    public static void setSelected(View view, Boolean selected) {
        if (selected != null && view != null) {
            view.setSelected(selected);
        }
    }

    /**
     * Selects/unselects the children of the target {@link ViewGroup} here {@link R.id#buttons_container}.
     * Only the child with given view id will be selected and rest of children will get unselected.
     *
     * @param viewGroup the target ViewGroup
     * @param viewID    id of the {@link CheckedTextView} to be checked
     */
    @BindingAdapter("selectViewIdInViewGroup")
    public static void selectViewIdInViewGroup(ViewGroup viewGroup, int viewID) {
        if (viewGroup != null) {
            for (int i = 0; i < viewGroup.getChildCount(); i++) {
                viewGroup.getChildAt(i).setSelected(viewGroup.getChildAt(i).getId() == viewID);
            }
        }
    }

    @BindingAdapter("settingsBarVisibility")
    public static void toggleSettingsBarVisibility(ViewGroup viewGroup, boolean visible) {
        if (viewGroup != null)
            if (visible)
                viewGroup.post(() -> {
                    viewGroup.animate().setDuration(200).alpha(1).translationY(0).scaleX(1).scaleY(1).start();
                    viewGroup.setVisibility(View.VISIBLE);
                });
            else
                viewGroup.post(() -> viewGroup.animate().setDuration(200).alpha(0).translationY(-viewGroup.getResources().getDimension(R.dimen.standard_125))
                        .scaleX(0).scaleY(0).withEndAction(() -> viewGroup.setVisibility(View.INVISIBLE))
                        .start());
    }

    @BindingAdapter("setAuxButtonModel")
    public static void setAuxButtonModel(AuxButtonsLayout layout, AuxButtonsModel auxButtonsModel) {
        if (auxButtonsModel != null)
            layout.setAuxButtonsModel(auxButtonsModel);
    }

    @BindingAdapter("hideAuxButtons")
    public static void setAuxButtonsHidden(AuxButtonsLayout layout, boolean hidden) {
        if (layout != null)
            layout.setAuxButtonsHidden(hidden);
    }

    @BindingAdapter("setActiveId")
    public static void setActiveCameraId(AuxButtonsLayout layout, String cameraId) {
        if (cameraId != null)
            layout.setActiveId(cameraId);
    }

    @BindingAdapter("layoutMarginTop")
    public static void setLayoutMarginTop(View view, float margin) {
        ViewGroup.MarginLayoutParams layoutParams = ((ViewGroup.MarginLayoutParams) view.getLayoutParams());
        layoutParams.topMargin = (int) margin;
        view.setLayoutParams(layoutParams);
    }

    @BindingAdapter("adjustCameraContainer")
    public static void adjustCameraContainer(ConstraintLayout cameraContainer, float displayAspectRatio) {
        if (displayAspectRatio <= 16f / 9) {
            ConstraintLayout.LayoutParams params = (ConstraintLayout.LayoutParams) cameraContainer.getLayoutParams();
            params.topToTop = ConstraintLayout.LayoutParams.PARENT_ID;
            params.topToBottom = ConstraintLayout.LayoutParams.UNSET;
        }
    }

    @BindingAdapter("adjustTopBar")
    public static void adjustTopBar(View topbar, float displayAspectRatio) {
        if (displayAspectRatio > 16f / 9) {
            ConstraintLayout.LayoutParams params = (ConstraintLayout.LayoutParams) topbar.getLayoutParams();
            DisplayMetrics displayMetrics = topbar.getResources().getDisplayMetrics();
            float dpHeight = displayMetrics.heightPixels / displayMetrics.density;
            float dpWidth = displayMetrics.widthPixels / displayMetrics.density;
            float dpmargin = (dpHeight - (dpWidth / 9f * 16f));
            params.topMargin = (int) dpmargin;
        }
    }
    
    @BindingAdapter("setAspectRatio")
    public static void setAspectRatio(View view, String ratio) {
        if (view != null && ratio != null && !ratio.isEmpty()) {
            ViewGroup.LayoutParams layoutParams = view.getLayoutParams();
            if (layoutParams instanceof ConstraintLayout.LayoutParams) {
                ConstraintLayout.LayoutParams params = (ConstraintLayout.LayoutParams) layoutParams;
                if (!ratio.equals(params.dimensionRatio)) {
                    params.dimensionRatio = ratio;
                    view.setLayoutParams(params);
                }
            }
        }
    }
}

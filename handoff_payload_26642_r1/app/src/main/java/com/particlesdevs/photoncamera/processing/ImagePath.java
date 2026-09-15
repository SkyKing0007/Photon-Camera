package com.particlesdevs.photoncamera.processing;

import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.util.FileManager;

import java.io.File;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class ImagePath {
    // IRIS_26642_PHOTO_PREFIX_NAME_OWNER
    // The public photo prefix is a literal prefix (underscore is optional). Video keeps the
    // established VID_ naming contract, and the timestamp/collision/storage policy is unchanged.
    public static String generateNewFileName(String prefix) {
        String timestamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date());
        if ("IMG".equals(prefix)) {
            String configured = PreferenceKeys.getPhotoPrefixName();
            return (isValidPhotoPrefix(configured) ? configured : "IMG_") + timestamp;
        }
        return prefix + "_" + timestamp;
    }

    public static boolean isValidPhotoPrefix(String prefix) {
        if (prefix == null || prefix.isEmpty() || prefix.length() > 64
                || ".".equals(prefix) || "..".equals(prefix)) return false;
        for (int i = 0; i < prefix.length(); ++i) {
            char c = prefix.charAt(i);
            if (c < 0x20 || c == 0x7f || c == '/' || c == '\\' || c == ':' || c == '*'
                    || c == '?' || c == '"' || c == '<' || c == '>' || c == '|') return false;
        }
        return true;
    }



    public static Path newDNGFilePath() {
        return getNewImageFilePath("dng");
    }

    public static Path newImageFilePath() {
        return getNewImageFilePath("");
    }

    public static Path getNewImageFilePath(String extension) {
        File dir = FileManager.sDCIM_CAMERA;
        if (extension.equalsIgnoreCase("dng")) {
            dir = FileManager.sPHOTON_RAW_DIR;
        }
        if(!extension.isEmpty()) {
            return Paths.get(dir.getAbsolutePath(), generateNewFileName("IMG") + '.' + extension);
        } else {
            return Paths.get(dir.getAbsolutePath(), generateNewFileName("IMG"));
        }
    }

    public static Path getNewImageFolderPath() {
        File dir = FileManager.sPHOTON_RAW_DIR;
        return Paths.get(dir.getAbsolutePath(), generateNewFileName("IMG"));
    }

    public static Path getNewVideoFolderPath() {
        File dir = FileManager.sPHOTON_RAW_DIR;
        return Paths.get(dir.getAbsolutePath(), generateNewFileName("VID"));
    }
}

package com.particlesdevs.photoncamera.processing.processor

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import com.hinnka.mycamera.processor.CalibratedRawNoiseProfile
import java.io.ByteArrayOutputStream
import java.io.File
import java.security.MessageDigest

/** IRIS_26514_PRIVATE_GCAM_C_PROFILE_STORE */
object IrisNoiseProfileStore {
    private const val MAX_BYTES = 1024 * 1024
    private const val DIR_NAME = "iris_noise_models"
    private val HEX_ID = Regex("^[0-9a-f]{64}$")

    data class ImportResult(
        val success: Boolean,
        val message: String,
        val displayName: String = "",
    )

    @JvmStatic
    fun importFromUri(context: Context, uri: Uri): ImportResult = runCatching {
        val displayName = resolveDisplayName(context, uri)
        require(displayName.lowercase().endsWith(".c")) { "Select a GCam .c noise-model file" }
        val bytes = context.contentResolver.openInputStream(uri)?.use(::readLimited)
            ?: throw IllegalArgumentException("Unable to open selected file")
        val source = String(bytes, Charsets.UTF_8)
        val id = sha256(bytes)
        // Parse before any setting/file mutation. Invalid imports leave the prior selection intact.
        CalibratedRawNoiseProfile.parseGcamC("iris-custom/$id", source)

        val dir = File(context.filesDir, DIR_NAME)
        require(dir.exists() || dir.mkdirs()) { "Unable to create Iris noise-model storage" }
        val dst = File(dir, "$id.c")
        val tmp = File(dir, ".$id.tmp")
        tmp.writeBytes(bytes)
        if (!tmp.renameTo(dst)) {
            tmp.copyTo(dst, overwrite = true)
            check(tmp.delete()) { "Unable to finalize imported profile" }
        }
        IrisMotionSettings.setImportedProfile(id, displayName)
        ImportResult(true, "Imported $displayName", displayName)
    }.getOrElse { error ->
        ImportResult(false, error.message ?: error.javaClass.simpleName)
    }

    @JvmStatic
    fun hasValidSelectedProfile(context: Context): Boolean =
        runCatching { loadSelectedProfile(context) != null }.getOrDefault(false)

    @JvmStatic
    fun loadSelectedProfile(context: Context): CalibratedRawNoiseProfile? {
        val settings = IrisMotionSettings.current()
        val id = settings.profileId
        if (!HEX_ID.matches(id)) return null
        val file = File(File(context.filesDir, DIR_NAME), "$id.c")
        if (!file.isFile || file.length() <= 0L || file.length() > MAX_BYTES.toLong()) return null
        return file.inputStream().use { input ->
            CalibratedRawNoiseProfile.parseGcamC("iris-custom/$id", input)
        }
    }

    /* IRIS_26912_B_OFF_PHYSICAL_PROFILE_STORE
     * Independent capture-lens selection, never the global A/DNG custom-noise
     * preference. Legacy profile IDs remain readable only through the original
     * A branch; B never inherits one physical lens's calibration into another.
     */
    private const val B_OFF_PREFS = "iris_26912_b_off_noise_per_physical"
    private fun lensKey(lens: String): String = "lens_" +
        sha256(lens.trim().toByteArray(Charsets.UTF_8))

    @JvmStatic
    fun bOffEnabled(context: Context, physicalId: String): Boolean =
        physicalId.isNotBlank() && context.applicationContext
            .getSharedPreferences(B_OFF_PREFS, Context.MODE_PRIVATE)
            .getBoolean(lensKey(physicalId) + "_enabled", false)

    @JvmStatic
    fun setBOffEnabled(context: Context, physicalId: String, enabled: Boolean) {
        require(physicalId.isNotBlank()) { "Missing physical camera ID" }
        context.applicationContext.getSharedPreferences(B_OFF_PREFS, Context.MODE_PRIVATE)
            .edit().putBoolean(lensKey(physicalId) + "_enabled", enabled).apply()
    }

    @JvmStatic
    fun bOffDisplayName(context: Context, physicalId: String): String {
        if (physicalId.isBlank()) return ""
        return context.applicationContext.getSharedPreferences(B_OFF_PREFS, Context.MODE_PRIVATE)
            .getString(lensKey(physicalId) + "_name", "") ?: ""
    }

    @JvmStatic
    fun importBOffForPhysical(context: Context, uri: Uri, physicalId: String): ImportResult = runCatching {
        require(physicalId.isNotBlank()) { "Missing physical camera ID" }
        val displayName = resolveDisplayName(context, uri)
        require(displayName.lowercase().endsWith(".c")) { "Select a GCam .c noise-model file" }
        val bytes = context.contentResolver.openInputStream(uri)?.use(::readLimited)
            ?: throw IllegalArgumentException("Unable to open selected file")
        val id = sha256(bytes)
        CalibratedRawNoiseProfile.parseGcamC("iris-b26912/$id", String(bytes, Charsets.UTF_8))
        val dir = File(context.filesDir, DIR_NAME)
        require(dir.exists() || dir.mkdirs()) { "Unable to create Iris noise-model storage" }
        val dst = File(dir, "$id.c")
        val tmp = File(dir, ".$id.tmp")
        tmp.writeBytes(bytes)
        if (!tmp.renameTo(dst)) {
            tmp.copyTo(dst, overwrite = true)
            check(tmp.delete()) { "Unable to finalize imported profile" }
        }
        // Commit after parse and complete file write; a failure cannot replace
        // the previous lens selection or enable another lens by accident.
        context.applicationContext.getSharedPreferences(B_OFF_PREFS, Context.MODE_PRIVATE)
            .edit().putString(lensKey(physicalId) + "_id", id)
            .putString(lensKey(physicalId) + "_name", displayName)
            .putBoolean(lensKey(physicalId) + "_enabled", true).apply()
        ImportResult(true, "Imported $displayName for camera $physicalId", displayName)
    }.getOrElse { ImportResult(false, it.message ?: it.javaClass.simpleName) }

    @JvmStatic
    fun loadBOffForPhysical(context: Context, physicalId: String): CalibratedRawNoiseProfile? =
        loadStoredBOffForPhysical(context, physicalId, true)

    @JvmStatic
    fun hasValidStoredBOffForPhysical(context: Context, physicalId: String): Boolean =
        loadStoredBOffForPhysical(context, physicalId, false) != null

    private fun loadStoredBOffForPhysical(context: Context, physicalId: String,
                                          requireEnabled: Boolean): CalibratedRawNoiseProfile? {
        if (physicalId.isBlank() || (requireEnabled && !bOffEnabled(context, physicalId))) return null
        val id = context.applicationContext.getSharedPreferences(B_OFF_PREFS, Context.MODE_PRIVATE)
            .getString(lensKey(physicalId) + "_id", "") ?: ""
        if (!HEX_ID.matches(id)) return null
        val file = File(File(context.filesDir, DIR_NAME), "$id.c")
        if (!file.isFile || file.length() <= 0L || file.length() > MAX_BYTES.toLong()) return null
        // Corrupted disk data or a stale selection always falls back to RAW-burst noise.
        return runCatching {
            file.inputStream().use { CalibratedRawNoiseProfile.parseGcamC("iris-b26912/$id", it) }
        }.getOrNull()
    }

    private fun resolveDisplayName(context: Context, uri: Uri): String {
        context.contentResolver.query(
            uri,
            arrayOf(OpenableColumns.DISPLAY_NAME),
            null,
            null,
            null,
        )?.use { cursor ->
            if (cursor.moveToFirst()) {
                val index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if (index >= 0) cursor.getString(index)?.takeIf { it.isNotBlank() }?.let { return it }
            }
        }
        return uri.lastPathSegment?.substringAfterLast('/')?.takeIf { it.isNotBlank() }
            ?: "noise_model.c"
    }

    private fun readLimited(input: java.io.InputStream): ByteArray {
        val out = ByteArrayOutputStream()
        val buffer = ByteArray(8192)
        var total = 0
        while (true) {
            val read = input.read(buffer)
            if (read < 0) break
            total += read
            require(total <= MAX_BYTES) { "Noise-model file exceeds 1 MiB" }
            out.write(buffer, 0, read)
        }
        require(total > 0) { "Noise-model file is empty" }
        return out.toByteArray()
    }

    private fun sha256(bytes: ByteArray): String =
        MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it.toInt() and 0xff) }
}

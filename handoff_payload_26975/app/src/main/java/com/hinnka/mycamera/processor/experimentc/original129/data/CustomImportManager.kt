package com.hinnka.mycamera.processor.experimentc.original129.data

import android.content.Context
import com.hinnka.mycamera.processor.experimentc.original129.raw.DcpInfo
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawNoiseProfileInfo
import com.hinnka.mycamera.processor.experimentc.original129.utils.PLog
import org.json.JSONArray
import java.io.File

/** Original PhotonCamera's custom DCP/noise import format, scoped to C processing. */
internal class CustomImportManager(private val context: Context) {
    private val customDcpDir: File
        get() = File(context.filesDir, "custom_dcps").apply { mkdirs() }
    private val customRawNoiseProfileDir: File
        get() = File(context.filesDir, "custom_raw_noise_profiles").apply { mkdirs() }

    fun getCustomDcps(): List<DcpInfo> {
        return try {
            val configFile = File(context.filesDir, "custom_dcps.json")
            if (!configFile.exists()) return emptyList()
            val jsonArray = JSONArray(configFile.readText())
            buildList {
                for (index in 0 until jsonArray.length()) {
                    val dcpObject = jsonArray.getJSONObject(index)
                    val id = dcpObject.getString("id")
                    val nameObject = dcpObject.getJSONObject("name")
                    val fileName = dcpObject.getString("fileName")
                    val file = File(customDcpDir, fileName)
                    if (!file.isFile || file.canonicalFile.parentFile != customDcpDir.canonicalFile) continue
                    val nameMap = mutableMapOf<String, String>()
                    nameObject.keys().forEach { lang -> nameMap[lang] = nameObject.getString(lang) }
                    add(DcpInfo(id = id, nameMap = nameMap, filePath = file.absolutePath, isBuiltIn = false))
                }
            }
        } catch (e: Exception) {
            PLog.e("CustomImportManager", "Failed to load custom DCPs", e)
            emptyList()
        }
    }

    fun getCustomRawNoiseProfiles(): List<RawNoiseProfileInfo> {
        return try {
            val configFile = File(context.filesDir, "custom_raw_noise_profiles.json")
            if (!configFile.exists()) return emptyList()
            val jsonArray = JSONArray(configFile.readText())
            buildList {
                for (index in 0 until jsonArray.length()) {
                    val profileObject = jsonArray.getJSONObject(index)
                    val id = profileObject.getString("id")
                    val fileName = profileObject.getString("fileName")
                    val file = File(customRawNoiseProfileDir, fileName)
                    if (!file.isFile || file.canonicalFile.parentFile != customRawNoiseProfileDir.canonicalFile) continue
                    val nameObject = profileObject.getJSONObject("name")
                    val nameMap = buildMap {
                        nameObject.keys().forEach { language -> put(language, nameObject.getString(language)) }
                    }
                    add(RawNoiseProfileInfo(id = id, nameMap = nameMap,
                        filePath = file.absolutePath, isBuiltIn = false))
                }
            }
        } catch (e: Exception) {
            PLog.e("CustomImportManager", "Failed to load custom RAW noise profiles", e)
            emptyList()
        }
    }
}

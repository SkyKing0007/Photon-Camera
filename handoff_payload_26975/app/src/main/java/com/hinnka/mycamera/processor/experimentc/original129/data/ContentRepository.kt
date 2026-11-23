package com.hinnka.mycamera.processor.experimentc.original129.data

import android.content.Context
import com.hinnka.mycamera.processor.experimentc.original129.raw.DcpInfo
import com.hinnka.mycamera.processor.experimentc.original129.raw.DcpManager
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawNoiseProfileManager
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.emptyFlow

/** C-private donor RAW profiles only; Iris exclusively owns UI/LUT/gallery preferences. */
internal class ContentRepository private constructor(context: Context) {
    val rawNoiseProfileManager = RawNoiseProfileManager(context)
    private val dcpManager = DcpManager(context)
    val userPreferencesRepository = DonorPreferencesRepository()
    fun getAvailableDcps(): List<DcpInfo> = dcpManager.getAvailableDcps()

    /** Absence of Iris's unrelated preferences invokes the original RAW AE default. */
    internal class DonorPreferences(val mlAeMaxHdrRatio: Float)
    internal class DonorPreferencesRepository {
        val userPreferences: Flow<DonorPreferences> = emptyFlow()
    }
    companion object {
        @Volatile private var instance: ContentRepository? = null
        fun getInstance(context: Context): ContentRepository = instance ?: synchronized(this) {
            instance ?: ContentRepository(context.applicationContext).also { instance = it }
        }
    }
}

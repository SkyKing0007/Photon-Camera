package com.hinnka.mycamera.processor.experimentc.original129.raw

object DcpNativeBridge {
    init {
        com.hinnka.mycamera.processor.experimentc.Iris26975COriginalNative.ensureLoaded()
    }

    external fun parseDcpToJson(filePath: String): String
}

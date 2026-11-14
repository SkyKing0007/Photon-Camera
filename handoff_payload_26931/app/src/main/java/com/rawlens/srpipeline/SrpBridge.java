// SPDX-License-Identifier: Apache-2.0
// IRIS_26931_NATIVE_DIRECT_BUFFER_FREE_FROM_ORIGINAL_SRP_LIBRARY.
package com.rawlens.srpipeline;

import java.nio.ByteBuffer;

public final class SrpBridge {
    private SrpBridge() {}
    static { System.loadLibrary("srpipeline"); }
    public static native void nativeFreeDirect(ByteBuffer buffer);
}

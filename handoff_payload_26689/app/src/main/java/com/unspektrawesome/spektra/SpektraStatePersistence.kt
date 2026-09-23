package com.unspektrawesome.spektra

/**
 * Minimal persistence contract for the Iris-hosted Unspektrawesome subsystem.
 * 26689 intentionally uses only the original in-memory state path so Iris does not
 * import the standalone app's preferences/UI persistence ownership.
 */
interface SpektraStatePersistence {
    fun load(): SpektraState?
    fun save(state: SpektraState)
}

object InMemorySpektraStatePersistence : SpektraStatePersistence {
    override fun load(): SpektraState? = null
    override fun save(state: SpektraState) = Unit
}

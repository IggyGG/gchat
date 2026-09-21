package boo.gchat.app.mobileplatform

import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test
import java.io.File
import java.util.UUID

class UnlockVaultInstrumentedTest {
    @Test fun optInRoundTripUpdateTamperAndDeletion() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val vault = UnlockVault(context)
        val slot = "test_" + UUID.randomUUID().toString()
        val path = File(context.noBackupFilesDir, "gchat-unlock-v1/$slot.bin")
        try {
            assertNull(vault.read(slot))
            try { vault.store(slot, "fixture unlock secret", false); fail("consent required") }
            catch (_: VaultFailure) { }
            assertFalse(path.exists())
            vault.store(slot, "fixture unlock secret", true)
            assertEquals("fixture unlock secret", vault.read(slot))
            assertFalse(String(path.readBytes(), Charsets.ISO_8859_1).contains("fixture unlock secret"))
            vault.store(slot, "replacement", true)
            assertEquals("replacement", vault.read(slot))
            val corrupt = path.readBytes()
            corrupt[corrupt.lastIndex] = (corrupt.last().toInt() xor 1).toByte()
            path.writeBytes(corrupt)
            try { vault.read(slot); fail("tampered ciphertext accepted") } catch (_: Exception) { }
            vault.delete(slot)
            assertNull(vault.read(slot))
            assertFalse(path.exists())
            vault.delete(slot)
        } finally { vault.delete(slot) }
    }
}

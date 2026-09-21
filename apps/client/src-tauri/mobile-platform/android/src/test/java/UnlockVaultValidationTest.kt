package boo.gchat.app.mobileplatform

import org.junit.Assert.*
import org.junit.Test

class UnlockVaultValidationTest {
    @Test fun rejectsPathSlotsAndInvalidSecrets() {
        for (slot in listOf("", "../x", "a/b", "a\\b", "a b", "å", "a".repeat(129))) {
            assertFalse(UnlockVault.validSlot(slot))
        }
        assertTrue(UnlockVault.validSlot("profile_A-123"))
        assertFalse(UnlockVault.validSecret(""))
        assertFalse(UnlockVault.validSecret("a\u0000b"))
        assertFalse(UnlockVault.validSecret("a".repeat(4097)))
        assertTrue(UnlockVault.validSecret("fixture passphrase"))
    }
}

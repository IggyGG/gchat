package boo.gchat.app.mobileplatform

import org.junit.Assert.*
import org.junit.Test

class PushNotificationValidationTest {
    @Test fun delayedPermissionAndTokenCallbacksCannotUndoOptOut() {
        val gate = PushEpoch()
        val requested = gate.advance()
        val disabled = gate.advance()
        assertFalse(gate.current(requested))
        assertTrue(gate.current(disabled))
        val reenabled = gate.advance()
        assertFalse(gate.current(disabled))
        assertFalse(gate.current(requested))
        assertTrue(gate.current(reenabled))
    }

    @Test fun gatewayPayloadIsAcceptedWithoutDisplayingItsData() {
        val reference = "ab".repeat(32)
        assertTrue(PushNotifications.isHint(mapOf("gcoms_activity" to "message", "gcoms_reference" to reference)))
        assertFalse(PushNotifications.isHint(mapOf("activity" to "message", "reference" to reference)))
        assertFalse(PushNotifications.isHint(mapOf("gcoms_activity" to "file", "gcoms_reference" to reference)))
        assertFalse(PushNotifications.isHint(mapOf("gcoms_activity" to "message", "gcoms_reference" to "text")))
    }

    @Test fun onlyOpaqueReferencesAreAccepted() {
        assertTrue(PushNotifications.validReference("ab".repeat(32)))
        for (value in listOf(null, "", "message text", "a".repeat(63), "a".repeat(65), "z".repeat(64))) {
            assertFalse(PushNotifications.validReference(value))
        }
    }
}

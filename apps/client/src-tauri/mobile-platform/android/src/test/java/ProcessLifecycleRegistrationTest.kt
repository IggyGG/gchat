package boo.gchat.app.mobileplatform

import androidx.arch.core.executor.testing.InstantTaskExecutorRule
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.LifecycleRegistry
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

class ProcessLifecycleRegistrationTest {
    @get:Rule val executor = InstantTaskExecutorRule()

    private class Owner : LifecycleOwner {
        val registry = LifecycleRegistry(this)
        override val lifecycle: Lifecycle get() = registry
    }

    @Test fun alreadyResumedProcessReplaysOnceAndDuplicateLoadDoesNotRegisterAgain() {
        val owner = Owner()
        owner.registry.currentState = Lifecycle.State.RESUMED
        val seen = mutableListOf<Int>()
        val target = ProcessLifecycleTarget { seen.add(it) }
        val registration = ProcessLifecycleRegistration()
        registration.bind(owner, target)
        registration.bind(owner, target)
        assertEquals(listOf(1), seen)
        assertEquals(1, owner.registry.observerCount)
    }

    @Test fun realStopAndResumeAreDeliveredButPauseAloneIsNotBackground() {
        val owner = Owner()
        owner.registry.currentState = Lifecycle.State.RESUMED
        val seen = mutableListOf<Int>()
        val target = ProcessLifecycleTarget { seen.add(it) }
        ProcessLifecycleRegistration().bind(owner, target)
        owner.registry.handleLifecycleEvent(Lifecycle.Event.ON_PAUSE)
        assertEquals(listOf(1), seen)
        owner.registry.handleLifecycleEvent(Lifecycle.Event.ON_STOP)
        assertEquals(listOf(1, 2), seen)
        owner.registry.handleLifecycleEvent(Lifecycle.Event.ON_START)
        owner.registry.handleLifecycleEvent(Lifecycle.Event.ON_RESUME)
        assertEquals(listOf(1, 2, 1), seen)
    }

    @Test fun replacementPluginReplaysCurrentStateWithoutKeepingTheOldRecipient() {
        val owner = Owner()
        owner.registry.currentState = Lifecycle.State.RESUMED
        val oldSeen = mutableListOf<Int>()
        val newSeen = mutableListOf<Int>()
        val oldTarget = ProcessLifecycleTarget { oldSeen.add(it) }
        val newTarget = ProcessLifecycleTarget { newSeen.add(it) }
        val registration = ProcessLifecycleRegistration()
        registration.bind(owner, oldTarget)
        registration.bind(owner, newTarget)
        registration.bind(owner, newTarget)
        assertEquals(listOf(1), oldSeen)
        assertEquals(listOf(1), newSeen)
        assertEquals(1, owner.registry.observerCount)
        owner.registry.currentState = Lifecycle.State.CREATED
        assertEquals(listOf(1), oldSeen)
        assertEquals(listOf(1, 2), newSeen)
    }

    @Test fun loadWhileStoppedReportsBackgroundBeforeNextResume() {
        val owner = Owner()
        owner.registry.currentState = Lifecycle.State.CREATED
        val seen = mutableListOf<Int>()
        val target = ProcessLifecycleTarget { seen.add(it) }
        ProcessLifecycleRegistration().bind(owner, target)
        assertEquals(listOf(2), seen)
        owner.registry.currentState = Lifecycle.State.RESUMED
        assertEquals(listOf(2, 1), seen)
    }
}

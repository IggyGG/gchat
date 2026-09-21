package boo.gchat.app.mobileplatform

import android.os.Looper
import android.util.Log
import androidx.lifecycle.DefaultLifecycleObserver
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.ProcessLifecycleOwner
import java.lang.ref.WeakReference

internal fun interface ProcessLifecycleTarget {
    fun changed(state: Int)
}

/** One process observer, with no strong reference to a plugin or Activity. */
internal class ProcessLifecycleRegistration : DefaultLifecycleObserver {
    private var owner: LifecycleOwner? = null
    private var target = WeakReference<ProcessLifecycleTarget>(null)
    private var state: Int? = null

    fun bind(nextOwner: LifecycleOwner, nextTarget: ProcessLifecycleTarget) {
        check(owner == null || owner === nextOwner) { "Process lifecycle owner changed" }
        if (target.get() === nextTarget) return
        target = WeakReference(nextTarget)
        if (owner == null) {
            owner = nextOwner
            // LifecycleRegistry immediately replays the current state to a new
            // observer. Register exactly once, including Activity recreation.
            nextOwner.lifecycle.addObserver(this)
            if (state == null) {
                publish(if (nextOwner.lifecycle.currentState.isAtLeast(Lifecycle.State.STARTED)) 1 else 2)
            }
        } else {
            state?.let(nextTarget::changed)
        }
    }

    private fun publish(next: Int) {
        if (state == next) return
        state = next
        target.get()?.changed(next)
    }

    override fun onResume(owner: LifecycleOwner) = publish(1)
    override fun onStop(owner: LifecycleOwner) = publish(2)
}

internal object ProcessLifecycleBridge {
    private val registration = ProcessLifecycleRegistration()

    fun bind(target: ProcessLifecycleTarget) {
        check(Looper.myLooper() == Looper.getMainLooper()) { "Lifecycle registration requires the main thread" }
        registration.bind(ProcessLifecycleOwner.get(), target)
        Log.i("GChatLifecycle", "process observer bound")
    }
}

package boo.gchat.app.mobileplatform

/** Pure generation gate shared by permission and asynchronous token callbacks. */
internal class PushEpoch {
    private var revision = 0L
    @Synchronized fun advance(): Long { revision = Math.addExact(revision, 1); return revision }
    @Synchronized fun current(expected: Long): Boolean = expected == revision
}

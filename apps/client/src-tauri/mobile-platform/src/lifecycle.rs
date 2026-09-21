use std::{
    collections::BTreeMap,
    panic::{catch_unwind, AssertUnwindSafe},
    sync::{Arc, Mutex, OnceLock},
};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum LifecycleEvent {
    Background,
    Foreground,
}

struct Subscriber {
    seen: Mutex<u64>,
    callback: Box<dyn Fn(LifecycleEvent) + Send + Sync>,
}

impl Subscriber {
    fn deliver(&self, generation: u64, event: LifecycleEvent) {
        let mut seen = self.seen.lock().unwrap_or_else(|e| e.into_inner());
        if generation <= *seen {
            return;
        }
        *seen = generation;
        // Callbacks only enqueue work. Serialize deliveries per subscriber, and
        // contain panics before returning through a native lifecycle callback.
        let _ = catch_unwind(AssertUnwindSafe(|| (self.callback)(event)));
    }
}

#[derive(Default)]
struct Hub {
    generation: u64,
    current: Option<LifecycleEvent>,
    next_id: u64,
    subscribers: BTreeMap<u64, Arc<Subscriber>>,
}

type SharedHub = Arc<Mutex<Hub>>;
static HUB: OnceLock<SharedHub> = OnceLock::new();
fn hub() -> &'static SharedHub {
    HUB.get_or_init(|| Arc::new(Mutex::new(Hub::default())))
}

/// Hold this handle for as long as lifecycle updates are needed. Dropping it
/// unregisters the callback; a callback already executing can finish.
#[must_use = "dropping the subscription unregisters its lifecycle callback"]
pub struct LifecycleSubscription {
    id: u64,
    hub: SharedHub,
}
impl Drop for LifecycleSubscription {
    fn drop(&mut self) {
        self.hub
            .lock()
            .unwrap_or_else(|e| e.into_inner())
            .subscribers
            .remove(&self.id);
    }
}

/// Receives the latest known native state immediately and subsequent changes.
/// The callback runs on a native lifecycle thread: only enqueue work; do not
/// block, re-enter lifecycle dispatch, or perform async work synchronously.
pub fn on_lifecycle(
    callback: impl Fn(LifecycleEvent) + Send + Sync + 'static,
) -> LifecycleSubscription {
    subscribe(hub(), Box::new(callback))
}

fn subscribe(
    hub: &SharedHub,
    callback: Box<dyn Fn(LifecycleEvent) + Send + Sync>,
) -> LifecycleSubscription {
    let subscriber = Arc::new(Subscriber {
        seen: Mutex::new(0),
        callback,
    });
    let (id, initial) = {
        let mut state = hub.lock().unwrap_or_else(|e| e.into_inner());
        state.next_id += 1;
        let id = state.next_id;
        state.subscribers.insert(id, subscriber.clone());
        (id, state.current.map(|event| (state.generation, event)))
    };
    if let Some((generation, event)) = initial {
        subscriber.deliver(generation, event);
    }
    LifecycleSubscription {
        id,
        hub: hub.clone(),
    }
}

#[cfg(any(target_os = "ios", target_os = "android", test))]
fn publish(hub: &SharedHub, event: LifecycleEvent) {
    let (generation, subscribers) = {
        let mut state = hub.lock().unwrap_or_else(|e| e.into_inner());
        if state.current == Some(event) {
            return;
        }
        state.current = Some(event);
        state.generation += 1;
        (
            state.generation,
            state.subscribers.values().cloned().collect::<Vec<_>>(),
        )
    };
    for subscriber in subscribers {
        subscriber.deliver(generation, event);
    }
}

#[cfg(any(target_os = "ios", target_os = "android"))]
fn native_event(value: u8) {
    let event = match value {
        1 => LifecycleEvent::Foreground,
        2 => LifecycleEvent::Background,
        _ => return,
    };
    let _ = catch_unwind(AssertUnwindSafe(|| publish(hub(), event)));
}

#[cfg(target_os = "ios")]
#[no_mangle]
pub extern "C" fn gchat_mobile_platform_lifecycle(value: u8) {
    native_event(value);
}

#[cfg(target_os = "android")]
#[no_mangle]
pub extern "system" fn Java_boo_gchat_app_mobileplatform_MobilePlatformPlugin_nativeLifecycle(
    _env: jni::JNIEnv<'_>,
    _object: jni::objects::JObject<'_>,
    value: jni::sys::jint,
) {
    if let Ok(value) = u8::try_from(value) {
        native_event(value);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn replays_latest_deduplicates_and_unsubscribes() {
        let hub = Arc::new(Mutex::new(Hub::default()));
        publish(&hub, LifecycleEvent::Foreground);
        let seen = Arc::new(Mutex::new(Vec::new()));
        let capture = seen.clone();
        let subscription = subscribe(&hub, Box::new(move |e| capture.lock().unwrap().push(e)));
        publish(&hub, LifecycleEvent::Foreground);
        publish(&hub, LifecycleEvent::Background);
        assert_eq!(
            *seen.lock().unwrap(),
            [LifecycleEvent::Foreground, LifecycleEvent::Background]
        );
        drop(subscription);
        publish(&hub, LifecycleEvent::Foreground);
        assert_eq!(seen.lock().unwrap().len(), 2);
    }

    #[test]
    fn stale_replay_cannot_overwrite_newer_transition() {
        let seen = Arc::new(Mutex::new(Vec::new()));
        let capture = seen.clone();
        let subscriber = Subscriber {
            seen: Mutex::new(0),
            callback: Box::new(move |e| capture.lock().unwrap().push(e)),
        };
        subscriber.deliver(2, LifecycleEvent::Background);
        subscriber.deliver(1, LifecycleEvent::Foreground);
        assert_eq!(*seen.lock().unwrap(), [LifecycleEvent::Background]);
    }

    #[test]
    fn callback_panic_does_not_prevent_other_subscribers_or_later_events() {
        let hub = Arc::new(Mutex::new(Hub::default()));
        let _panic = subscribe(&hub, Box::new(|_| panic!("injected callback failure")));
        let count = Arc::new(std::sync::atomic::AtomicUsize::new(0));
        let capture = count.clone();
        let _healthy = subscribe(
            &hub,
            Box::new(move |_| {
                capture.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
            }),
        );
        publish(&hub, LifecycleEvent::Background);
        publish(&hub, LifecycleEvent::Foreground);
        assert_eq!(count.load(std::sync::atomic::Ordering::Relaxed), 2);
    }
}

//! The Android Service owns this runtime. No WebView task owns a network connection.
use gchat_core::chat_service::{
    host::{InstanceConfig, InstanceHost},
    serve, ChatEndpoint,
};
use jni::{
    objects::{JClass, JString},
    sys::{jboolean, jlong},
    JNIEnv,
};
use std::{
    path::PathBuf,
    sync::{Arc, Mutex, OnceLock},
};
use tokio::sync::watch;

struct Native {
    generation: u64,
    host: Arc<InstanceHost>,
    stop: watch::Sender<bool>,
    server: tokio::task::JoinHandle<Result<(), String>>,
    home: PathBuf,
}
static RUNTIME: OnceLock<tokio::runtime::Runtime> = OnceLock::new();
static GENERATION: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(1);
static SERVICE: Mutex<Option<Native>> = Mutex::new(None);
fn runtime() -> &'static tokio::runtime::Runtime {
    RUNTIME.get_or_init(|| tokio::runtime::Runtime::new().expect("Android service runtime"))
}
fn start(home: PathBuf) -> Result<u64, String> {
    let mut current = SERVICE.lock().map_err(|_| "Android service lock")?;
    if let Some(current) = current.as_mut() {
        return if current.home == home {
            current.generation = GENERATION.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
            Ok(current.generation)
        } else {
            Err("service already belongs to another instance".into())
        };
    }
    let config = InstanceConfig::from_home(Some(&home))?;
    let endpoint = config.chat_endpoint();
    let host = InstanceHost::new(config)?;
    let (stop, receiver) = watch::channel(false);
    let hosted = host.clone();
    let server = runtime().spawn(async move { serve(hosted, &endpoint, receiver).await });
    let generation = GENERATION.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    *current = Some(Native {
        generation,
        host,
        stop,
        server,
        home,
    });
    Ok(generation)
}
fn stop(generation: u64) -> Result<(), String> {
    let previous = {
        let mut current = SERVICE.lock().map_err(|_| "Android service lock")?;
        if current
            .as_ref()
            .is_some_and(|current| current.generation == generation)
        {
            current.take()
        } else {
            None
        }
    };
    if let Some(previous) = previous {
        let _ = previous.stop.send(true);
        runtime()
            .block_on(previous.server)
            .map_err(|e| e.to_string())??;
    }
    Ok(())
}
#[no_mangle]
pub extern "system" fn Java_dev_ghost_gchat_GchatService_nativeStart(
    mut env: JNIEnv,
    _class: JClass,
    home: JString,
) -> jlong {
    let result = env
        .get_string(&home)
        .map(|s| PathBuf::from(String::from(s)))
        .map_err(|e| e.to_string())
        .and_then(start);
    match result {
        Ok(generation) => generation as jlong,
        Err(error) => {
            let _ = env.throw_new("java/lang/IllegalStateException", error);
            0
        }
    }
}
#[no_mangle]
pub extern "system" fn Java_dev_ghost_gchat_GchatService_nativeStop(
    mut env: JNIEnv,
    _class: JClass,
    generation: jlong,
) {
    if let Err(error) = stop(generation as u64) {
        let _ = env.throw_new("java/lang/IllegalStateException", error);
    }
}
#[no_mangle]
pub extern "system" fn Java_dev_ghost_gchat_GchatService_nativeConnected(
    _env: JNIEnv,
    _class: JClass,
    generation: jlong,
) -> jboolean {
    let host = SERVICE.lock().ok().and_then(|s| {
        s.as_ref()
            .filter(|s| s.generation == generation as u64)
            .map(|s| s.host.clone())
    });
    let Some(host) = host else {
        return 0;
    };
    runtime().block_on(async {
        match tokio::time::timeout(
            std::time::Duration::from_millis(500),
            host.dispatch(gchat_api::RequestEnvelope {
                version: gchat_api::VERSION,
                instance_id: None,
                request: gchat_api::Request::Identify,
            }),
        )
        .await
        {
            Ok(reply) => match reply.response {
                gchat_api::Response::Instance { instance } => {
                    (!instance.protocol_locked) as jboolean
                }
                _ => 0,
            },
            // Busy protocol transitions are still connected until explicitly stopped.
            Err(_) => 1,
        }
    })
}

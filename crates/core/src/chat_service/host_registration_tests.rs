use super::*;
use gchat_api::fleet::FleetConfig;
use gcoms::sdk::{
    ipc::Capability,
    machine::{ComponentCredentials, ComponentRegistration, MachineRegistry},
};

fn fixture(home: &Path) -> (InstanceConfig, FleetConfig, String) {
    std::fs::create_dir_all(home).unwrap();
    private_fs::make_private(home, true).unwrap();
    let mut config = InstanceConfig::from_home(Some(home)).unwrap();
    config.fleet_config = Some(home.join("fleet config.json"));
    config.managed_service = Some("gchat-registration-fixture.service".into());
    config.gc2_carrier = true;
    config.network_recovery = false;
    let fleet = FleetConfig {
        version: 1,
        safety_number: "fixture identity pin".into(),
        primary_component: [1; 16],
        registry: MachineRegistry {
            version: 1,
            components: vec![ComponentRegistration {
                credentials: ComponentCredentials {
                    component_id: [2; 16],
                    token: [9; 32],
                },
                capabilities: vec![Capability::IdentityRead],
                peers: vec![],
                files: None,
            }],
        },
    };
    save_fleet(&config, &fleet);
    let instance = instance_metadata(&config.archive).unwrap().id;
    let binding = capability(&config, &instance).unwrap();
    publish(&config, &instance, &binding).unwrap();
    (config, fleet, instance)
}

fn save_fleet(config: &InstanceConfig, fleet: &FleetConfig) {
    crate::store::atomic_write(
        config.fleet_config.as_ref().unwrap(),
        &serde_json::to_vec(fleet).unwrap(),
        false,
    )
    .unwrap();
}

#[cfg(not(any(target_os = "android", target_os = "ios")))]
#[test]
fn standalone_personal_registration_retains_carrier_network_and_paths() {
    let dir = tempfile::tempdir().unwrap();
    private_fs::make_private(dir.path(), true).unwrap();
    let mut config = InstanceConfig::from_home(Some(dir.path())).unwrap();
    config.gc2_carrier = true;
    config.network_recovery = false;
    config.relay_urls.clear();
    config.protocol_socket = dir.path().join("personal endpoint.sock");
    config.network_config = Some(dir.path().join("signed network.json"));
    let instance = instance_metadata(&config.archive).unwrap().id;
    let binding = capability(&config, &instance).unwrap();
    publish(&config, &instance, &binding).unwrap();
    let selected = InstanceConfig::from_home(Some(dir.path())).unwrap();
    assert!(
        selected.has_registered_host().unwrap(),
        "saved personal selection must not depend on launcher flags"
    );
    assert!(selected.gc2_carrier);
    assert!(!selected.network_recovery);
    assert_eq!(selected.network_config, config.network_config);
    assert_eq!(selected.protocol_socket, config.protocol_socket);
    assert!(selected.fleet_config.is_none() && selected.managed_service.is_none());
    let before = std::fs::read(path(&selected)).unwrap();
    publish(&selected, &instance, &binding).unwrap();
    assert_eq!(std::fs::read(path(&selected)).unwrap(), before);
    let mut conflict = selected;
    conflict.network_recovery = true;
    assert!(resolve(&mut conflict).is_err());
    assert_eq!(std::fs::read(path(&config)).unwrap(), before);
}

#[cfg(not(any(target_os = "android", target_os = "ios")))]
#[test]
fn personal_adoption_only_adds_first_scope_and_service_after_successful_publication() {
    let dir = tempfile::tempdir().unwrap();
    let (scoped, fleet, instance) = fixture(dir.path());
    let mut personal = scoped.clone();
    personal.fleet_config = None;
    personal.managed_service = None;
    let before = Registration::from_config(&personal, &instance).unwrap();
    crate::store::atomic_write(
        &path(&personal),
        &serde_json::to_vec(&before).unwrap(),
        false,
    )
    .unwrap();
    let original = std::fs::read(path(&personal)).unwrap();
    let mut intended = scoped.clone();
    resolve(&mut intended).unwrap();
    assert_eq!(
        std::fs::read(path(&personal)).unwrap(),
        original,
        "validation cannot publish before runtime authentication"
    );
    assert!(publish(&intended, &instance, "wrong verified binding").is_err());
    assert_eq!(std::fs::read(path(&personal)).unwrap(), original);
    let binding = capability(&intended, &instance).unwrap();
    publish(&intended, &instance, &binding).unwrap();
    let selected = InstanceConfig::from_home(Some(dir.path())).unwrap();
    assert_eq!(selected.fleet_config, scoped.fleet_config);
    assert_eq!(selected.managed_service, scoped.managed_service);
    let adopted = std::fs::read(path(&selected)).unwrap();
    publish(&selected, &instance, &binding).unwrap();
    assert_eq!(std::fs::read(path(&selected)).unwrap(), adopted);
    let mut changed = selected.clone();
    changed.managed_service = Some("gchat-another-host.service".into());
    assert!(resolve(&mut changed).is_err());
    let mut different = fleet;
    different.registry.components[0].credentials.component_id = [3; 16];
    save_fleet(&selected, &different);
    assert!(resolve(&mut changed).is_err());
    assert_eq!(std::fs::read(path(&selected)).unwrap(), adopted);
    let mut downgrade = Registration::from_config(&personal, &instance).unwrap();
    let current: Registration = serde_json::from_slice(&adopted).unwrap();
    assert!(!current.permits_adoption(&downgrade));
    downgrade.fleet = current.fleet.clone();
    assert!(!current.permits_adoption(&downgrade));
    let mut unrelated = before.clone();
    unrelated.gc2_carrier = !before.gc2_carrier;
    assert!(!before.permits_adoption(&unrelated));
}

#[cfg(not(any(target_os = "android", target_os = "ios")))]
#[test]
fn first_service_adoption_preserves_every_other_personal_host_choice() {
    let dir = tempfile::tempdir().unwrap();
    private_fs::make_private(dir.path(), true).unwrap();
    let config = InstanceConfig::from_home(Some(dir.path())).unwrap();
    let instance = instance_metadata(&config.archive).unwrap().id;
    publish(&config, &instance, &capability(&config, &instance).unwrap()).unwrap();
    let before = std::fs::read(path(&config)).unwrap();
    for field in 0..4 {
        let mut different = config.clone();
        different.managed_service = Some("gchat-personal.service".into());
        match field {
            0 => different.network_recovery = !config.network_recovery,
            1 => different.gc2_carrier = !config.gc2_carrier,
            2 => different.protocol_socket = dir.path().join("another.sock"),
            _ => different.relay_urls.push("https://another.example/".into()),
        }
        assert!(resolve(&mut different).is_err());
        assert_eq!(std::fs::read(path(&config)).unwrap(), before);
    }
    let mut managed = config;
    managed.managed_service = Some("gchat-personal.service".into());
    resolve(&mut managed).unwrap();
    assert_eq!(std::fs::read(path(&managed)).unwrap(), before);
    publish(
        &managed,
        &instance,
        &capability(&managed, &instance).unwrap(),
    )
    .unwrap();
    let selected = InstanceConfig::from_home(Some(dir.path())).unwrap();
    assert_eq!(selected.managed_service, managed.managed_service);
    assert!(selected.fleet_config.is_none());
}

#[test]
fn registration_restores_host_and_allows_credentials_to_rotate_without_rebinding() {
    let dir = tempfile::tempdir().unwrap();
    let home = dir.path().join("instance café 東京 with spaces");
    let (config, mut fleet, instance) = fixture(&home);
    let before = std::fs::read(path(&config)).unwrap();
    let restored = InstanceConfig::from_home(Some(&home)).unwrap();
    assert_eq!(restored.fleet_config, config.fleet_config);
    assert_eq!(restored.managed_service, config.managed_service);
    assert!(restored.gc2_carrier);
    assert!(!restored.network_recovery);
    assert!(!String::from_utf8_lossy(&before).contains("token"));
    let binding = capability(&config, &instance).unwrap();
    fleet.registry.components[0].credentials.token = [8; 32];
    save_fleet(&config, &fleet);
    let restored = InstanceConfig::from_home(Some(&home)).unwrap();
    assert_eq!(capability(&restored, &instance).unwrap(), binding);
    publish(&restored, &instance, &binding).unwrap();
    assert_eq!(std::fs::read(path(&config)).unwrap(), before);
}

#[test]
fn different_partition_or_identity_cannot_reuse_or_replace_registration() {
    for identity in [false, true] {
        let dir = tempfile::tempdir().unwrap();
        let (config, mut fleet, instance) = fixture(dir.path());
        let before = std::fs::read(path(&config)).unwrap();
        let binding = capability(&config, &instance).unwrap();
        if identity {
            fleet.safety_number = "different identity".into();
        } else {
            fleet.registry.components[0].credentials.component_id = [3; 16];
        }
        save_fleet(&config, &fleet);
        assert!(InstanceConfig::from_home(Some(dir.path())).is_err());
        assert!(publish(&config, &instance, &binding).is_err());
        assert_eq!(std::fs::read(path(&config)).unwrap(), before);
        assert!(!config.profile.exists());
        assert!(!config.archive.exists());
    }
}

#[test]
fn explicit_startup_conflict_does_not_modify_the_registration() {
    let dir = tempfile::tempdir().unwrap();
    let (config, _, _) = fixture(dir.path());
    let before = std::fs::read(path(&config)).unwrap();
    for field in 0..4 {
        let mut other = config.clone();
        match field {
            0 => other.managed_service = Some("gchat-other.service".into()),
            1 => other.gc2_carrier = false,
            2 => other.network_recovery = true,
            _ => other.protocol_socket = dir.path().join("other.sock"),
        }
        assert!(resolve(&mut other).unwrap_err().contains("conflicts"));
    }
    assert_eq!(std::fs::read(path(&config)).unwrap(), before);
}

#[test]
fn copied_registration_does_not_select_another_profile_or_create_metadata() {
    let source = tempfile::tempdir().unwrap();
    let (config, _, _) = fixture(source.path());
    let target = tempfile::tempdir().unwrap();
    private_fs::make_private(target.path(), true).unwrap();
    let other = InstanceConfig::from_home(Some(target.path())).unwrap();
    crate::store::atomic_write(&path(&other), &std::fs::read(path(&config)).unwrap(), true)
        .unwrap();
    assert!(InstanceConfig::from_home(Some(target.path())).is_err());
    assert!(!other.archive.with_extension("instance.json").exists());
    assert!(!other.profile.exists());
}

#[test]
fn missing_and_oversized_registration_are_distinct_from_personal_defaults() {
    let dir = tempfile::tempdir().unwrap();
    private_fs::make_private(dir.path(), true).unwrap();
    let config = InstanceConfig::from_home(Some(dir.path())).unwrap();
    assert!(!config.has_registered_host().unwrap());
    crate::store::atomic_write(&path(&config), &vec![b' '; LIMIT as usize + 1], true).unwrap();
    assert!(InstanceConfig::from_home(Some(dir.path()))
        .err()
        .unwrap()
        .contains("size limit"));
    assert!(!config.profile.exists());
}

#[cfg(unix)]
#[test]
fn symlink_and_shared_registration_files_refuse_before_startup() {
    use std::os::unix::fs::{symlink, PermissionsExt};
    let dir = tempfile::tempdir().unwrap();
    let (config, _, _) = fixture(dir.path());
    let registration = path(&config);
    let retained = registration.with_extension("retained");
    std::fs::rename(&registration, &retained).unwrap();
    symlink(&retained, &registration).unwrap();
    assert!(InstanceConfig::from_home(Some(dir.path())).is_err());
    std::fs::remove_file(&registration).unwrap();
    std::fs::rename(&retained, &registration).unwrap();
    std::fs::set_permissions(&registration, std::fs::Permissions::from_mode(0o644)).unwrap();
    assert!(InstanceConfig::from_home(Some(dir.path())).is_err());
    assert!(!config.profile.exists());
}

#[cfg(unix)]
#[test]
fn native_non_utf8_path_references_round_trip_without_loss() {
    use std::os::unix::ffi::OsStringExt;
    let dir = tempfile::tempdir().unwrap();
    let expected = dir
        .path()
        .join(std::ffi::OsString::from_vec(b"instance-\xff".to_vec()));
    let encoded = LocalPath::new(&expected).unwrap();
    assert!(matches!(encoded, LocalPath::Unix { .. }));
    let saved = serde_json::to_vec(&encoded).unwrap();
    let restored: LocalPath = serde_json::from_slice(&saved).unwrap();
    assert_eq!(restored.path().unwrap(), expected);
}

// macOS's native filesystem rejects this byte spelling before host code runs
// (EILSEQ in both native Mac gates). Keep real byte-path reopening on Linux and
// lossless reference serialization above on every Unix target. The main reopen
// control uses Unicode and spaces on every supported platform.
#[cfg(target_os = "linux")]
#[test]
fn native_non_utf8_paths_survive_saved_host_reopen() {
    use std::os::unix::ffi::OsStringExt;
    let dir = tempfile::tempdir().unwrap();
    let home = dir
        .path()
        .join(std::ffi::OsString::from_vec(b"instance-\xff".to_vec()));
    let (config, _, instance) = fixture(&home);
    let restored = InstanceConfig::from_home(Some(&home)).unwrap();
    assert_eq!(restored.profile, config.profile);
    assert_eq!(restored.fleet_config, config.fleet_config);
    assert_eq!(
        capability(&config, &instance).unwrap(),
        capability(&restored, &instance).unwrap()
    );
}

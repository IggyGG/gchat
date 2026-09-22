//! Desktop startup policy. Selecting a carrier never retries or migrates a profile.
use clap::Parser;
use gchat_core::chat_service::host::InstanceConfig;
use std::{ffi::OsString, path::PathBuf};

#[derive(Debug, Parser)]
#[command(name = "gchat-desktop")]
struct Arguments {
    /// Use a separate saved identity and archive directory.
    #[arg(long)]
    home: Option<PathBuf>,
    /// Attach a local fleet controller to this selected identity.
    #[arg(long, env = "GCHAT_FLEET_CONFIG")]
    fleet_config: Option<PathBuf>,
    /// Select the current carrier explicitly (the default in official builds).
    #[arg(long, conflicts_with = "legacy_carrier")]
    gc2_carrier: bool,
    /// Open a legacy carrier instance without changing its saved profile.
    #[arg(long, conflicts_with = "gc2_carrier")]
    legacy_carrier: bool,
    /// Disable automatic network bootstrap for an isolated instance.
    #[arg(long)]
    no_network_bootstrap: bool,
}

pub(crate) fn configuration<I, T>(args: I) -> Result<InstanceConfig, String>
where
    I: IntoIterator<Item = T>,
    T: Into<OsString> + Clone,
{
    let args = Arguments::try_parse_from(args).map_err(|error| error.to_string())?;
    if args.gc2_carrier && !cfg!(feature = "gc2-carrier") {
        return Err("this application was built without GC/2 carrier support".into());
    }
    let mut config = InstanceConfig::from_home(args.home.as_deref())?;
    config.fleet_config = args.fleet_config;
    // Pass one choice to the host. A retained profile mismatch remains an error;
    // changing the desktop default is not permission to rewrite its identity.
    config.gc2_carrier = cfg!(feature = "gc2-carrier") && !args.legacy_carrier;
    config.network_recovery = !args.no_network_bootstrap;
    Ok(config)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn official_feature_selects_current_carrier_by_default() {
        let config = configuration(["gchat-desktop", "--home", "desktop-test-home"]).unwrap();
        assert_eq!(config.gc2_carrier, cfg!(feature = "gc2-carrier"));
        assert!(config.network_recovery);
        assert!(!config.local_fixture);
    }

    #[test]
    fn explicit_legacy_carrier_preserves_the_compatibility_choice() {
        let config = configuration([
            "gchat-desktop",
            "--home",
            "desktop-test-home",
            "--legacy-carrier",
        ])
        .unwrap();
        assert!(!config.gc2_carrier);
        assert!(config.network_recovery);
    }

    #[test]
    fn explicit_current_carrier_requires_compiled_support() {
        let result = configuration([
            "gchat-desktop",
            "--home",
            "desktop-test-home",
            "--gc2-carrier",
        ]);
        if cfg!(feature = "gc2-carrier") {
            assert!(result.unwrap().gc2_carrier);
        } else {
            assert!(result.err().unwrap().contains("without GC/2"));
        }
    }

    #[test]
    fn conflicting_carrier_options_fail_in_both_orders() {
        for flags in [
            ["--gc2-carrier", "--legacy-carrier"],
            ["--legacy-carrier", "--gc2-carrier"],
        ] {
            let error = configuration(["gchat-desktop", flags[0], flags[1]])
                .err()
                .unwrap();
            assert!(error.contains("cannot be used with"), "{error}");
        }
    }

    #[test]
    fn missing_home_and_unknown_arguments_are_errors() {
        for args in [
            vec!["gchat-desktop", "--home"],
            vec!["gchat-desktop", "--home", "--gc2-carrier"],
            vec!["gchat-desktop", "--unknown"],
            vec!["gchat-desktop", "unexpected"],
        ] {
            assert!(configuration(args).is_err());
        }
    }

    #[test]
    fn isolated_launch_disables_bootstrap_without_changing_carrier() {
        let config = configuration([
            "gchat-desktop",
            "--home",
            "desktop-test-home",
            "--no-network-bootstrap",
        ])
        .unwrap();
        assert!(!config.network_recovery);
        assert_eq!(config.gc2_carrier, cfg!(feature = "gc2-carrier"));
        let legacy = configuration([
            "gchat-desktop",
            "--home",
            "desktop-test-home",
            "--legacy-carrier",
            "--no-network-bootstrap",
        ])
        .unwrap();
        assert!(!legacy.network_recovery);
        assert!(!legacy.gc2_carrier);
    }

    #[test]
    fn home_paths_with_spaces_are_preserved() {
        let home = PathBuf::from("desktop test home");
        let config = configuration([
            OsString::from("gchat-desktop"),
            OsString::from("--home"),
            home.clone().into_os_string(),
        ])
        .unwrap();
        assert_eq!(config.profile.parent(), Some(home.as_path()));
        assert_eq!(config.archive.parent(), Some(home.as_path()));
    }

    #[cfg(unix)]
    #[test]
    fn native_non_utf8_home_is_not_lossily_reencoded() {
        use std::os::unix::ffi::OsStringExt;
        let home = PathBuf::from(OsString::from_vec(b"desktop-\xff".to_vec()));
        let config = configuration([
            OsString::from("gchat-desktop"),
            OsString::from("--home"),
            home.clone().into_os_string(),
        ])
        .unwrap();
        assert_eq!(config.profile.parent(), Some(home.as_path()));
        assert_eq!(config.archive.parent(), Some(home.as_path()));
    }
}

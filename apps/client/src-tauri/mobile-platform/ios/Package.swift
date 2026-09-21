// swift-tools-version:5.5
import PackageDescription

let package = Package(
    name: "tauri-plugin-gchat-mobile-platform",
    platforms: [.iOS(.v15)],
    products: [
        .library(name: "tauri-plugin-gchat-mobile-platform", type: .static,
                 targets: ["tauri-plugin-gchat-mobile-platform"])
    ],
    dependencies: [.package(name: "Tauri", path: "../.tauri/tauri-api")],
    targets: [
        .target(name: "tauri-plugin-gchat-mobile-platform", dependencies: [.byName(name: "Tauri")], path: "Sources"),
        .testTarget(name: "PluginTests", dependencies: ["tauri-plugin-gchat-mobile-platform"], path: "Tests/PluginTests")
    ]
)

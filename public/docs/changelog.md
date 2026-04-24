# Changelog

All notable changes to the OmniClaw project will be documented in this file.

## [4.5.0] - 2026-04-24
### Added
- **Security MCP Tools**: New MCP endpoints for `run_security_scan`, `analyze_live_screen`, and `analyze_security_context`.
- **Vision 4.5**: High-performance multimodal pipeline with 1024px/JPEG 85% optimization.
- **Cross-Platform Capture**: Native Windows DXGI and macOS SCStream support.
- **Documentation System**: New `/docs` structure and rewritten, storefront-quality README.
- **Security Policy**: Added `SECURITY.md` and `CODE_OF_CONDUCT.md`.

### Changed
- **UI Redesign**: Complete overhaul of the landing page to a professional, cyber-elite aesthetic.
- **Module Reorganization**: Moved non-core modules (Trading, Plant Monitor) to `modules/other/`.
- **Version Consolidation**: Synchronized version 4.5.0 across all project manifests.

### Removed
- **Bloat**: Deleted legacy clones and untracked `__pycache__` directories.
- **Dead Links**: Fixed broken navigation and documentation links.

## [4.4.0] - 2026-04-20
### Added
- **Sovereign Sentinel**: Merged Shannon Pro monorepo components.
- **eBPF Bridge**: Initial implementation of kernel-level system call monitoring.
- **Durable Workers**: Integrated mission state persistence.

## [4.2.0] - 2026-04-10
### Added
- **Initial Hive Architecture**: Manager-Worker loop for multiple LLM providers.
- **Termux Support**: Basic compatibility for Android deployment.

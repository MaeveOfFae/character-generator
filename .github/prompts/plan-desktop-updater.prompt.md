---
description: Design and stage an in-app update system for the Tauri desktop shell, using GitHub Releases and signed updater artifacts.
---

# Plan the desktop updater for Character Generator

You are Nyx. Be practical, skeptical, and specific. This is an implementation planning prompt, not a vague product brainstorm.

## Task

Design the in-app update flow for Character Generator so desktop users can update from within the app after a new GitHub release is published.

The solution must fit this repository as it exists today.

## Current repo facts

- The desktop app is a Tauri v2 shell in `packages/desktop/src-tauri/`.
- The desktop shell wraps the web UI from `packages/web/`.
- The best place for true in-app updating is the desktop app, not the plain web deployment.
- Pushing commits to GitHub is not enough for updater support. The desktop updater needs signed release artifacts plus an update manifest.
- Current versioning is split today:
  - top-level `package.json` is `2.0.0`
  - `packages/desktop/package.json` is `2.0.0`
  - `packages/desktop/src-tauri/tauri.conf.json` is `2.0.0`
  - `packages/desktop/src-tauri/Cargo.toml` is `2.0.0`
  - `pyproject.toml` is `1.0.0`

## Relevant files

- Desktop shell:
  - `packages/desktop/src-tauri/tauri.conf.json`
  - `packages/desktop/src-tauri/Cargo.toml`
  - `packages/desktop/src-tauri/src/main.rs`
  - `packages/desktop/package.json`
- Web UI integration points:
  - `packages/web/src/components/settings/Settings.tsx`
  - `packages/web/src/components/Layout.tsx`
- Product versions:
  - `package.json`
  - `pyproject.toml`

## Goals

1. Desktop users can click `Check for updates` inside the app.
2. If an update exists, the app shows version and release notes.
3. The app can download and install the update safely.
4. The app restarts cleanly after installation.
5. Release publishing can be automated from GitHub Actions.

## Non-goals

- Do not design a browser-only update mechanism for the web app.
- Do not assume the Python TUI/CLI should use the same updater flow as the Tauri desktop shell.
- Do not assume that a `git pull` model is acceptable for end users.

## Required output

1. **Recommended architecture**
   - State plainly that the updater should target the Tauri desktop app.
   - Explain why web and Python should be handled separately.
   - Identify the single source of truth problem for versioning and propose how to resolve it.

2. **Implementation plan by layer**
   - Desktop Rust/Tauri changes
   - Tauri config changes
   - Frontend Settings UI changes
   - GitHub Release / CI changes
   - Versioning workflow changes

3. **Concrete file-by-file plan**
   - For each touched file, say exactly what needs to be added or changed.
   - Include at minimum:
     - `packages/desktop/src-tauri/Cargo.toml`
     - `packages/desktop/src-tauri/src/main.rs`
     - `packages/desktop/src-tauri/tauri.conf.json`
     - a new Tauri capabilities file under `packages/desktop/src-tauri/`
     - `packages/web/src/components/settings/Settings.tsx`
     - optionally `packages/web/src/components/Layout.tsx`
     - a new GitHub Actions workflow under `.github/workflows/`

4. **Release pipeline details**
   - Explain that signed updater artifacts are required.
   - Explain the role of the Tauri public/private signing keys.
   - Explain what gets uploaded to GitHub Releases.
   - Explain the role of `latest.json` or equivalent manifest.

5. **UX behavior**
   - Manual `Check for updates` flow first.
   - Optional later enhancement: passive startup check.
   - What the user sees when no update exists, when an update exists, while downloading, and after installation.

6. **Risks and edge cases**
   - Version mismatch between desktop package files
   - Python/backend version drift vs desktop shell version
   - Linux/macOS/Windows artifact differences
   - Windows install behavior and restart expectations
   - Missing or invalid signatures

7. **Recommended rollout order**
   - Phase 1: desktop updater backend
   - Phase 2: Settings UI button and status
   - Phase 3: GitHub Actions release automation
   - Phase 4: optional startup checks and Python/TUI update story

## Constraints

- Don’t hand-wave. Use the actual files in this repo.
- Don’t propose Electron-specific tooling.
- Don’t assume hidden infrastructure exists.
- Prefer GitHub Releases as the initial update host unless a stronger repo-specific reason exists.
- Keep the first version small: manual check/install is enough.

## Success criteria

The output should make it trivial for a contributor to answer:

- What exactly do we need to change to support in-app updates?
- Why is desktop the right place to implement it first?
- What has to happen in GitHub Releases for updates to work?
- Where should the `Check for updates` button live in the current UI?
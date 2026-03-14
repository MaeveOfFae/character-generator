import{j as e}from"./index-CEVrtZak.js";import{D as r}from"./DocumentPage-D8Z4Jbey.js";import"./router-vendor-qnUfEknD.js";import"./index-DqZDyowh.js";const t=`## Overview

Eidolon Simulacra is designed as a browser-first application. By default, drafts, templates, blueprint overrides, theme presets, and most configuration state are stored locally in your browser.

## What Is Stored Locally

- draft metadata and draft assets
- template definitions and blueprint overrides
- theme presets and theme customizations
- app configuration and model preferences
- optional persisted API keys, if you explicitly enable persistence

## API Keys

API keys are sensitive. The app can keep them in memory for the current session or persist them locally in browser storage when you opt in.

If you enable persistence, keys are stored in local browser storage on the current device.

## Third-Party Model Providers

When you generate, refine, compare, or otherwise use model-backed actions, relevant request data may be sent directly to the configured provider. This can include prompts, asset content, draft context, and selected settings.

Provider handling of that data is governed by the provider's own privacy policy and terms.

## Imports and Exports

When you export drafts, config, or keys, files are generated on your device. You are responsible for securing those exports and handling them appropriately.

## Hosted Telemetry

Optional analytics or error tracking may be configured via environment variables in a deployment, but this repository does not require them for core operation.

## Data Deletion

You can remove browser-stored data through the in-app Data Manager or by clearing site storage in your browser.

## Security Reporting

If you discover a vulnerability or sensitive data exposure issue, follow the reporting instructions on the Security page.`;function n(){return e.jsx(r,{eyebrow:"Privacy",title:"Privacy",summary:"How browser storage, API keys, provider requests, and exports are handled in the current browser-first architecture.",markdown:t})}export{n as default};
//# sourceMappingURL=PrivacyPage-BKE_kgRn.js.map

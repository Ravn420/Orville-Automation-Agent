# Safe Defaults and Advanced Settings

## Purpose

Orville should be useful for a first local workflow without requiring users to understand providers, routing policy, storage topology, resource quotas, schedules, notification transports, or preference persistence. Safe defaults reduce setup decisions; advanced settings remain available when the user has a concrete need and the required authorization.

The canonical non-secret example is config/settings-defaults.example.json. Defaults are starting values, not permissions. Saving a default never authorizes external execution, account access, publication, deployment, or destructive changes.

## Default profile

| Area | Safe default | User-visible explanation |
|---|---|---|
| Provider and model | Auto-select an available local provider and compatible model. | Use a ready local option when one is available; choose a specific provider or model only when needed. |
| Privacy routing | Local-only. | Keep source material local unless the user explicitly selects an approved external route for a run. |
| Storage | Application-data artifact and temporary directories. | Keep outputs and temporary files in managed locations with containment checks. |
| Resource limits | Two concurrent tasks, 1,800-second task timeout, and a 500 MB artifact limit. | Use bounded defaults that keep the workstation responsive and prevent unbounded work. |
| Schedules | Manual only. | Do not run work in the background until the user enables and authorizes a schedule. |
| Notifications | Failures and approval-required events. | Notify about decisions that need attention without creating noisy routine alerts. |
| Theme and motion | Follow system theme and respect reduced-motion preferences. | Match the device and avoid non-essential motion by default. |
| Telemetry | Minimal local operational metadata. | Collect only what is needed for local operation; do not include prompts, secrets, or provider responses. |

If a local provider or model is unavailable, the interface reports the missing capability and offers a bounded setup path. It does not silently switch to an external provider or weaken privacy policy.

## Advanced settings disclosure

Advanced settings are grouped behind an explicit Advanced settings affordance with a short explanation of why a user might need them. Opening the group does not change values or enable external behavior. Advanced fields include explicit labels, examples, validation constraints, reset-to-default actions, effective scope, restart impact, and an explanation of any approval requirement.

Advanced settings may expose a specific provider or model, endpoint URL, protected credential reference, fallback policy, memory/VRAM/disk limits, schedule expression, notification target, retention period, or telemetry level. Secret values are never revealed; only a protected reference and safe status are shown. Empty advanced fields inherit the safe default rather than requiring a duplicate value.

## Override and precedence rules

The effective value is resolved in this order: an approved per-run value, an approved project value, an explicitly saved user value, then the safe default. A more specific value may narrow privacy or resource limits but may not silently broaden permissions. Invalid, unknown, stale, or out-of-range values fail closed and leave the last valid value unchanged.

The interface distinguishes inherited, default, customized, and approval-required values. A reset action restores defaults for the selected scope and is non-destructive: it does not delete artifacts, models, credentials, projects, schedules owned by another scope, or external resources.

## Validation and feedback

Every setting has a type, allowed range or enumeration, scope, and safe error message. Path settings require approved-root containment and writable-location checks. Resource settings are bounded and reject zero, negative, excessively large, or inconsistent values. Endpoint settings are checked against network policy. Schedule settings remain disabled until explicitly enabled and authorized. Notification targets are validated without displaying secret tokens.

Save feedback states what changed, the effective scope, and whether a restart or approval is required. Errors identify the field, reason, and recovery action; they do not display raw exceptions, credentials, cookies, authorization headers, private keys, or secret-bearing URLs.

## Acceptance criteria

The settings experience is accepted when a new local user can complete a common workflow using only defaults; the effective values are visible; advanced settings are discoverable but not overwhelming; explicit overrides persist only when valid; invalid values fail closed; local-only routing is never silently broadened; reset is non-destructive; secrets remain protected references; and consequential settings remain approval-gated.

Focused validation is:

    python -m unittest tests.test_safe_defaults
    python -m compileall -q tests/test_safe_defaults.py

The profile is a non-secret example and does not claim production provider provisioning, live schedule execution, external notification delivery, or client migration completeness.

## References

- Settings workspace contract: docs/SETTINGS_WORKSPACE.md
- Visual design system: docs/VISUAL_DESIGN_SYSTEM.md
- Web and mobile acceptance criteria: docs/WEB_MOBILE_ACCEPTANCE_CRITERIA.md

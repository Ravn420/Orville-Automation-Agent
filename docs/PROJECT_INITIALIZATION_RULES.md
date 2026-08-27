# Project Initialization Rules

## Purpose

This document defines the deterministic initialization contract for generated software projects. Orville must classify the requested product before creating files, select exactly one supported project profile, record assumptions, and produce a runnable baseline with documentation and focused validation. The rules apply in standalone environments and do not require Manus-specific services.

## Initialization contract

Every initialization request must record the following fields before scaffolding:

| Field | Requirement |
| --- | --- |
| `project_name` | A filesystem-safe name that is unique within the selected workspace. |
| `project_type` | Exactly one of `static_site`, `full_stack_web`, or `mobile_application`. |
| `objective` | A concise description of the user-visible outcome. |
| `target_platforms` | Browser targets for web projects; operating systems or device families for mobile projects. |
| `runtime` | The language and runtime version used by the generated project. |
| `package_manager` | The selected package manager and lockfile policy. |
| `data_and_auth` | Explicitly `none`, local-only, or a declared backend/auth boundary. |
| `preview_method` | A local command and expected URL or device preview mechanism. |
| `acceptance_criteria` | Testable baseline behavior for the first runnable checkpoint. |
| `assumptions` | Any non-critical detail inferred from the request. Critical ambiguity must block initialization. |

Initialization must fail closed when the project type, runtime, destination, or required acceptance criteria are missing or contradictory. Secrets, personal credentials, production endpoints, and provider tokens must never be generated into a scaffold. User-supplied values are stored only through the approved environment or secret-reference mechanism.

## Common initialization stages

1. **Inspect and classify.** Determine the project type from the objective and identify repository constraints, available runtimes, and the requested delivery surface.
2. **Select the profile.** Apply the profile matrix below. Do not combine profiles implicitly; a project that needs both a web client and a server must use `full_stack_web`, while a native device client remains `mobile_application`.
3. **Record the plan.** Persist the selected profile, runtime, package manager, generated paths, commands, assumptions, and acceptance criteria before writing source files.
4. **Create the baseline.** Generate the minimum runnable structure, dependency manifest, environment example, README, source entrypoint, test entrypoint, and preview command specified by the profile.
5. **Verify locally.** Install or resolve dependencies using the selected lockfile, run the profile test command, run the build command, and start the preview command when the environment supports it.
6. **Checkpoint.** Retain the generated file manifest, validation results, warnings, and unresolved deployment limitations. A failed validation leaves the checkpoint incomplete and must not be presented as runnable.

## Profile rules

### Static site: `static_site`

Use this profile for browser-delivered sites that do not require a server-side application or private runtime state. The output must be deployable as static files.

| Area | Rule |
| --- | --- |
| Source | Provide an application entrypoint, styles, assets, and a clearly documented browser entry URL. |
| Runtime | Use the repository-approved frontend runtime and package manager; do not add a server process solely to serve production behavior. |
| Configuration | Include a non-secret environment example. Public build-time values must be distinguished from private values, and private values are prohibited in client bundles. |
| Data | Use static content or explicitly documented public APIs. Do not embed write-capable credentials. |
| Quality baseline | The initial checkpoint must build successfully, render the entry page, expose visible focus styling, declare document language and viewport metadata, and include a smoke test for the primary interaction. |
| Preview | Provide a local static preview command and expected URL. Preview must use the built output when the toolchain supports it. |
| Delivery | Include build output instructions and a deployment note that names the selected user-approved hosting target or states that hosting is not configured. |

### Full-stack web application: `full_stack_web`

Use this profile when the project requires a browser client plus a server-side API, persistence, authentication boundary, background work, or protected integrations.

| Area | Rule |
| --- | --- |
| Source | Separate frontend and backend entrypoints, with an explicit API contract and error envelope. |
| Runtime | Record compatible runtime versions for client and server, and provide one reproducible development command or clearly documented start sequence. |
| Configuration | Commit safe example configuration only. Runtime secrets are referenced by name and resolved outside source control. CORS, host, port, and API base URL behavior must be explicit. |
| Data and auth | Define storage ownership, migrations or initialization behavior, session/token boundary, authorization expectations, and local fallback behavior. Never expose provider credentials to the browser. |
| Quality baseline | The initial checkpoint must pass backend unit tests, frontend checks, API contract checks, and an authenticated or explicitly anonymous smoke path appropriate to the objective. |
| Preview | Provide a local server command, health/readiness check, frontend URL, API URL or proxy path, and shutdown procedure. Preview data must be isolated from production data. |
| Delivery | Include setup, migration, test, build, preview, configuration, and rollback instructions. Deployment remains disabled until the user explicitly selects a target and approves external side effects. |

### Mobile application: `mobile_application`

Use this profile for a native or cross-platform application intended for supported mobile operating systems or device families.

| Area | Rule |
| --- | --- |
| Source | Include the application entrypoint, navigation or screen baseline, platform configuration, assets, and a device-safe test entrypoint. |
| Runtime | Record the mobile framework, language, SDK/toolchain versions, supported operating systems, and package manager. |
| Configuration | Store only non-secret defaults in the project. Native signing credentials, service-account keys, and production endpoints remain external secret references. |
| Data and auth | Define offline behavior, local persistence, network boundary, authentication state handling, and failure behavior for unavailable services. |
| Quality baseline | The initial checkpoint must compile or bundle for at least one declared target, run unit/component checks, and verify the first screen or navigation path through a device/emulator smoke check when available. |
| Preview | Provide the local start command and device/emulator preview procedure, including the expected host binding and any user-controlled QR/device step. No device enrollment or store submission is performed automatically. |
| Delivery | Include platform build instructions, environment setup, test commands, artifact locations, signing prerequisites, and explicit store-release approval gates. |

## Cross-profile acceptance checks

The verification record for every initialized project must answer these questions:

- Was exactly one profile selected, and is the selection consistent with the objective?
- Are all generated paths inside the approved project workspace?
- Can a clean environment identify the runtime, package manager, install command, test command, build command, and preview command?
- Are example configuration files free of credential values, private keys, bearer tokens, and production-only endpoints?
- Does the baseline expose a documented failure mode when a required runtime, dependency, endpoint, emulator, or secret reference is unavailable?
- Were build, test, and preview results recorded separately, including warnings and unresolved risks?

A project is **initialized** only when the profile-specific quality baseline and the cross-profile acceptance checks pass. Otherwise, the state is `blocked` or `incomplete`, with a concise reproduction note and no claim that the project is runnable.

## Change and compatibility policy

Adding a new profile requires a new profile identifier, an initialization matrix entry, profile-specific baseline checks, documentation, and focused tests. Existing profile identifiers and required fields remain backward-compatible. Changes that alter generated paths, runtime assumptions, secret handling, or preview behavior require a state checkpoint and changelog entry.

## Validation commands

From the repository root, validate this contract with:

```text
python -m unittest tests.test_project_initialization_rules
python -m compileall -q tests/test_project_initialization_rules.py
```

These checks validate the document structure and secret-safe wording; generated applications must also run their own profile-specific build, test, and preview checks.

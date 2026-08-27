# Progressive Disclosure Contract

## Summary

Orville presents the smallest useful set of controls first and reveals advanced options only when the operator explicitly requests them. The primary workflow remains usable without knowledge of task graphs, agent frameworks, provider APIs, runtime details, or privacy policy vocabulary.

## Disclosure model

| Surface | Visible by default | Revealed on request | Safety boundary |
|---|---|---|---|
| Primary objective composer | Objective prompt, attachment affordance, and start action | None required for first-run completion | Starting work still follows the existing approval and authorization rules. |
| Provider setup | Provider type and model name | Provider ID, endpoint, API key, timeout, capabilities, and privacy policy | Credentials remain masked and are sent only through the approved local API. |
| Model manager | Model inventory and basic lifecycle actions | Runtime, endpoint, license restriction, and attestation controls | Activation remains approval-gated; registration removal does not delete model files. |
| Verification | Review summary and bounded evidence | Specialist evidence details through the dedicated review surface | The view records evidence but does not certify its quality or approval authority. |

## Interaction requirements

Advanced options MUST be hidden on initial display, MUST have a clearly labeled disclosure control, and MUST remain available without changing or losing entered values. The disclosure control MUST be reversible, must not trigger a network request, and must preserve the current safe defaults when collapsed. Basic setup and recovery actions MUST remain available without expanding the advanced section.

The first-run path SHOULD explain why an advanced option matters before exposing provider-specific or runtime-specific terminology. Technical controls belong in dedicated specialist views rather than in the default objective composer.

## Safety and accessibility boundaries

Progressive disclosure MUST NOT hide approval requirements, credential warnings, destructive-action confirmations, safe error feedback, or required accessibility information. Hidden controls remain keyboard-addressable through the explicit disclosure action, and the interface must retain readable labels, predictable focus order, sufficient contrast, and reduced-motion compatibility.

## Acceptance checks

A local implementation is acceptable when focused tests confirm that advanced provider controls are default-collapsed, the disclosure label is explicit and reversible, values are preserved by the toggle, and the documentation names the safety and accessibility boundaries. Python compilation and the focused test module must pass before the TODO item is marked complete.

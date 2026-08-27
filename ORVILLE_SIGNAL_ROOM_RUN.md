

## Roadmap runtime features

The current release includes an **Agent runtime** menu in the Signal Room. It reads authenticated agent profiles, installed Skills, and local usage telemetry from the runtime API. Profiles and Skills are managed through the authenticated API and are intentionally shown as unavailable when the local node is not connected.

The release also includes a provider-neutral connector adapter registry for priority services, a dedicated Connectors menu, and a local Browser Operator extension bundle under `browser_extension/`. To load the extension in Chrome or Edge, open the browser extensions page, enable Developer mode, choose **Load unpacked**, and select that folder. Pairing must be initiated from Orville; the extension does not request broad host permissions and does not store passwords.

Wide Research is available as a bounded local execution primitive for item-level parallel work, retries, evidence fields, cancellation, and resume. Use it through the authenticated API or an agent workflow; do not treat a catalogued connector manifest as an operational integration until the provider-specific credentials and handler have been configured.

The portable archive contains the executable, extension bundle, connector guide, release hardening guide, and portable data marker. Installed releases use `%LOCALAPPDATA%\\Orville\\data`; portable releases use the portable folder’s `data` directory. Back up the appropriate data directory before upgrades.

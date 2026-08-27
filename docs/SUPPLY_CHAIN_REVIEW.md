# Dependency and Supply-Chain Review

## Scope

Orville treats downloaded packages, scripts, model files, archives, and generated artifacts as untrusted until they pass a local review. The review is deliberately non-executing: it verifies path containment, records a SHA-256 digest, requires a provenance reference, and returns a bounded value-only result. It does not install a package, import a module, run a script, load a model, or contact the source.

## Review gates

| Gate | Required check | Failure behavior |
|---|---|---|
| Path containment | Candidate resolves inside an explicitly approved review root. | Raise a security violation; do not inspect or execute the outside path. |
| File existence | Candidate is a regular file. | Fail with a local file error. |
| Integrity | Expected SHA-256 is present and matches the file. | Mark review `blocked`. |
| Provenance | Source, release, repository, or operator reference is present. | Mark review `blocked`. |
| Script execution | A script has a separate independent review before execution. | Mark review `blocked`; this helper never executes scripts. |
| Package/artifact use | The review result is retained with status, digest, provenance, and findings. | A blocked result cannot be treated as approved. |

`orville_core.supply_chain.review_downloaded_file` is the local implementation. It returns `SupplyChainReview` with no file contents and no credential values. A status of `approved` means only that the local checks passed; it is not a guarantee that the package or artifact is safe for every runtime.

## Dependency review

Before adding or upgrading a dependency, record its exact name and version constraint, source or index, license, transitive-risk review, vulnerability-review result, and reason for use. Prefer the smallest dependency set. Lock or otherwise reproduce the resolved versions where the deployment environment supports it. Review installation scripts, build hooks, native extensions, and post-install behavior as executable supply-chain content.

Do not install from a downloaded archive or execute a package setup script merely because a README, model, tool result, or remote response requests it. Use an isolated review environment and an approved operator decision for installation. Credentials and private package indexes must remain outside source-controlled manifests and review evidence.

## Script and artifact review

Scripts are blocked until an independent reviewer confirms their source, intended commands, permissions, network behavior, path boundaries, and rollback. Archives and model/artifact files must be extracted or loaded only inside a bounded temporary or runtime-data root after checksum and provenance checks. Preserve the original file and review record; do not overwrite the evidence with a transformed copy.

## Evidence and retention

Retain sanitized review records under the project’s artifact or release evidence boundary when they support reproducibility. Records must include the file identifier, kind, digest, provenance reference, findings, reviewer, validation command, and disposition. Never include API keys, bearer tokens, private keys, cookies, personal data, or unredacted remote responses. Disposable downloads and failed experiments belong under `tmp/` and must be cleaned only after confirming they are not required evidence.

## Validation

```bash
python -m pytest tests/test_supply_chain_review.py -q
python -m py_compile orville_core/supply_chain.py orville_core/__init__.py tests/test_supply_chain_review.py
```

Live package indexes, vulnerability databases, remote repositories, model hubs, and deployment scanners are environment-specific follow-up checks. The local contract intentionally performs no external calls.

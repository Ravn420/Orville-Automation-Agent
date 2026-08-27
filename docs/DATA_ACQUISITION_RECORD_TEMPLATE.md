# Reproducible Data-Acquisition Record

## Acquisition metadata

| Field | Value |
|---|---|
| Record ID | `REPLACE_WITH_NON_SECRET_ID` |
| Objective and intended use | `REPLACE` |
| Dataset or API name | `REPLACE` |
| Owner | `REPLACE` |
| Acquisition start/end | `YYYY-MM-DDThh:mm:ssZ / YYYY-MM-DDThh:mm:ssZ` |
| Environment and tool version | `REPLACE` |
| Risk and data classification | `low` / `medium` / `high; public / internal / confidential` |

## Source and request

| Field | Value |
|---|---|
| Source URL or safe identifier | `https://example.invalid/data` |
| Publisher or provider | `REPLACE` |
| API version or dataset release | `REPLACE` |
| Publication/update date | `YYYY-MM-DD` or `not published` |
| Access date | `YYYY-MM-DD` |
| Query, endpoint, or saved-query identifier | `REPLACE_WITH_NON_SECRET_QUERY` |
| Parameters and filters | `REPLACE; exclude secrets and personal data` |
| Authentication reference | `credential-reference-id` or `none`; never record the secret value |
| Freshness policy | `REPLACE` |
| Pagination and ordering | `REPLACE` |
| Rate-limit and retry behavior | `REPLACE` |

## Integrity and provenance

| Field | Value |
|---|---|
| Downloaded file name | `REPLACE_WITH_SAFE_NAME` |
| Media type and encoding | `REPLACE` |
| Byte size or row count | `REPLACE` |
| SHA-256 or equivalent digest | `REPLACE` |
| Signature or checksum source | `REPLACE` |
| Schema/version evidence | `REPLACE` |
| Timezone and units | `REPLACE` |
| Provenance validation | `REPLACE` |
| Storage path | approved data or artifact path; never a secret path |

## Transformations and validation

Record each transformation in order, including code or command path, version, parameters, input/output identifiers, row-count changes, filtering, joins, normalization, deduplication, missing-value handling, and independent validation. Preserve the raw input only when policy permits; otherwise record its safe identifier, digest, retention decision, and reason.

| Step | Input ID | Code or command | Parameters | Output ID | Validation result |
|---|---|---|---|---|---|
| 1 | `RAW` | `REPLACE` | `REPLACE` | `DERIVED-1` | `REPLACE` |

## Reproduction and failure record

Document the exact safe reproduction command, dependency lock or version set, environment variables by name only, expected output, and actual output. For failures, record the operation, timestamp, HTTP or application error class, retry count, bounded remediation, and whether the acquisition was resumed or restarted. Do not record tokens, cookies, authorization headers, or sensitive response bodies.

## Safety and retention gate

- The source and provider are authorized for the intended use.
- Downloaded artifacts were validated for provenance, file type, path containment, permissions, and intended use before processing.
- No untrusted downloaded code, plugin, model, or script was executed.
- Credentials are referenced by protected identifier only and are absent from logs and records.
- Personal, confidential, or regulated data handling and retention requirements were checked.
- Output was scanned for secrets and personal data before sharing.
- Retention, deletion, and rollback decisions are recorded without deleting protected runtime data as routine cleanup.

## References

[1]: https://example.invalid/data "Replace with the dataset or API documentation"

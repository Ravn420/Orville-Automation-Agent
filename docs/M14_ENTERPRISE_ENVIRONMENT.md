# M14.1 Enterprise Environment and Responsibility Matrix

`orville_core.enterprise_readiness` defines the local, non-provisioning contract required before enterprise production operations. It captures an environment identifier, tenant boundary, region, platform, data classifications, allowed network labels, recovery objectives, operational owners, rollback authority, escalation channel, and production flag.

The contract validates required ownership, rejects unsafe tenant path/control characters, requires at least one data classification, and requires `0 <= RPO <= RTO` within bounded 30-day limits. It contains no credentials and performs no external provisioning or account mutation.

Use `config/enterprise-environment.example.json` as a non-secret starting point. Replace example identifiers with approved enterprise values only after the environment owner, security owner, data owner, deployment owner, and rollback authority are explicitly assigned. A production declaration is not sufficient evidence of production readiness; M14.2–M14.10 gates must still pass.

## M14.1 acceptance evidence

The local contract round-trips through `from_dict`/`to_dict`, rejects unsafe tenant identifiers and invalid recovery objectives, and is covered by `tests/test_enterprise_readiness.py`. Enterprise operators must separately retain the approved responsibility matrix, data-classification decision, RTO/RPO approval, escalation test, and rollback-authority acknowledgement.

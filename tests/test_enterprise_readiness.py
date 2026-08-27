from __future__ import annotations

import unittest

from orville_core.enterprise_readiness import EnterpriseEnvironment, EnterpriseReadinessError


VALID = {
    "environment_id": "staging-eu-1",
    "tenant_id": "tenant-example",
    "region": "eu-west",
    "platform": "linux-container",
    "data_classes": ["internal", "restricted"],
    "allowed_networks": ["provider-egress"],
    "recovery": {"rto_seconds": 3600, "rpo_seconds": 900},
    "responsibilities": {
        "security_owner": "security-team",
        "platform_owner": "platform-team",
        "deployment_owner": "release-team",
        "data_owner": "data-owner",
        "rollback_authority": "release-manager",
        "escalation_channel": "oncall",
    },
}


class EnterpriseReadinessTests(unittest.TestCase):
    def test_valid_environment_round_trips(self):
        environment = EnterpriseEnvironment.from_dict(VALID)
        self.assertEqual(EnterpriseEnvironment.from_dict(environment.to_dict()).tenant_id, "tenant-example")

    def test_invalid_recovery_and_tenant_boundaries_fail_closed(self):
        invalid = dict(VALID)
        invalid["tenant_id"] = "tenant/unsafe"
        with self.assertRaises(EnterpriseReadinessError):
            EnterpriseEnvironment.from_dict(invalid)
        invalid = dict(VALID)
        invalid["recovery"] = {"rto_seconds": 10, "rpo_seconds": 11}
        with self.assertRaises(EnterpriseReadinessError):
            EnterpriseEnvironment.from_dict(invalid)


if __name__ == "__main__":
    unittest.main()

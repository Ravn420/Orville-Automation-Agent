from __future__ import annotations

import unittest

from orville_core.production_metrics import InMemoryHealthSource, MetricSample, MetricsError, ProductionMetrics


class ProductionMetricsTests(unittest.TestCase):
    def test_scoped_summary_aggregates_health_signals(self):
        source = InMemoryHealthSource()
        for name, value in (("requests", 100), ("errors", 4), ("latency_ms", 10), ("latency_ms", 20), ("latency_ms", 100), ("saturation", 0.4), ("business_health", 0.9), ("security_findings", 0), ("release_quality", 0.95)):
            source.record(MetricSample("tenant-a", "canary", "release-2", name, value, 100.0))
        summary = ProductionMetrics(source).summarize("tenant-a", "canary", "release-2", since=99)
        self.assertEqual(summary.sample_count, 9)
        self.assertEqual(summary.requests, 100)
        self.assertEqual(summary.errors, 4)
        self.assertAlmostEqual(summary.error_rate, 0.04)
        self.assertEqual(summary.latency_p95_ms, 100)
        self.assertEqual(summary.business_health, 0.9)
        observation = summary.to_canary_observation()
        self.assertEqual(observation.release_id, "release-2")
        self.assertEqual(observation.critical_security_findings, 0)

    def test_tenant_cohort_release_scope_is_enforced(self):
        source = InMemoryHealthSource()
        source.record(MetricSample("tenant-a", "canary", "release-2", "requests", 1, 100))
        source.record(MetricSample("tenant-b", "canary", "release-2", "requests", 999, 100))
        summary = ProductionMetrics(source).summarize("tenant-a", "canary", "release-2", since=99)
        self.assertEqual(summary.requests, 1)
        baseline = ProductionMetrics(source).summarize("tenant-a", "canary", "release-2", since=99)
        other = baseline.__class__("tenant-a", "full", "release-2", 0, 0, 0, 0, 0, 0, 0, None, 0, None, 100)
        with self.assertRaises(MetricsError):
            ProductionMetrics(source).compare(baseline, other)

    def test_invalid_metric_fails_closed_and_stale_samples_exclude(self):
        source = InMemoryHealthSource()
        with self.assertRaises(MetricsError):
            source.record(MetricSample("tenant-a", "canary", "release-2", "saturation", 2, 100))
        source.record(MetricSample("tenant-a", "canary", "release-2", "requests", 1, 10))
        self.assertEqual(ProductionMetrics(source).summarize("tenant-a", "canary", "release-2", since=11).sample_count, 0)


if __name__ == "__main__":
    unittest.main()

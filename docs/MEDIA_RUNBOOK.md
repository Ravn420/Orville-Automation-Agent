# Orville Media Operations Runbook

## Overview

This runbook provides operational procedures for managing the Orville Media Workflow system in production environments. It covers common issues, monitoring, and performance tuning.

## Table of Contents

1. [Operational Procedures](#operational-procedures)
2. [Common Issues and Resolutions](#common-issues-and-resolutions)
3. [Monitoring Guidelines](#monitoring-guidelines)
4. [Performance Tuning](#performance-tuning)
5. [Emergency Procedures](#emergency-procedures)

## Operational Procedures

### Daily Operations

#### Check System Health

```bash
# Check API health
curl -s http://localhost:8000/health | jq .

# Expected response:
# {
#   "status": "healthy",
#   "services": {
#     "media_generation": "up",
#     "media_validation": "up",
#     "media_provenance": "up"
#   }
# }
```

#### Monitor Generation Queue

```python
# Check pending generations
from orville_core.media_generation import MediaGenerationService

service = MediaGenerationService()
queue_status = service.get_queue_status()

print(f"Pending: {queue_status['pending']}")
print(f"Processing: {queue_status['processing']}")
print(f"Completed (24h): {queue_status['completed_24h']}")
print(f"Failed (24h): {queue_status['failed_24h']}")
```

#### Review Validation Metrics

```python
# Get validation statistics
from orville_core.media_validation import get_validation_stats

stats = get_validation_stats(since_hours=24)

print(f"Total validated: {stats['total']}")
print(f"Valid: {stats['valid']} ({stats['valid_rate']:.1%})")
print(f"Invalid: {stats['invalid']}")
print(f"Top failure reasons:")
for reason, count in stats['failure_reasons'].items():
    print(f"  - {reason}: {count}")
```

### Weekly Operations

#### Provenance Storage Audit

```bash
# Check provenance storage size
du -sh /var/lib/orville/provenance

# Count records
find /var/lib/orville/provenance -name "*.json" | wc -l

# Check for orphaned records
python -c "
from orville_core.media_provenance import MediaProvenanceStore
store = MediaProvenanceStore('/var/lib/orville/provenance')
orphaned = store.find_orphaned_records()
print(f'Orphaned records: {len(orphaned)}')
"
```

#### Cleanup Old Records

```python
# Archive records older than 90 days
from orville_core.media_provenance import MediaProvenanceStore
from datetime import datetime, timedelta

store = MediaProvenanceStore("/var/lib/orville/provenance")
cutoff = datetime.now() - timedelta(days=90)

archived = store.archive_records(before=cutoff, destination="/archive/provenance")
print(f"Archived {archived} records")
```

### Monthly Operations

#### Provider Health Check

```python
# Test all providers
from orville_core.media_generation import get_available_providers

providers = get_available_providers()
for provider in providers:
    status = provider.health_check()
    print(f"{provider.name}: {'✓' if status.healthy else '✗'} {status.latency}ms")
    if not status.healthy:
        print(f"  Error: {status.error}")
```

#### Capacity Planning

```python
# Analyze usage trends
from orville_core.media_generation import get_usage_analytics

analytics = get_usage_analytics(days=30)

print("Generation by modality:")
for modality, count in analytics['by_modality'].items():
    print(f"  {modality}: {count}")

print("\nGeneration by provider:")
for provider, count in analytics['by_provider'].items():
    print(f"  {provider}: {count}")

print(f"\nAverage generation time: {analytics['avg_generation_time']:.2f}s")
print(f"95th percentile: {analytics['p95_generation_time']:.2f}s")
```

## Common Issues and Resolutions

### Issue: Generation Failures

#### Symptom
High rate of generation failures (>5%)

#### Diagnosis

```python
# Check recent failures
from orville_core.media_generation import get_generation_logs

failures = get_generation_logs(
    status='failed',
    since_hours=1,
    limit=100
)

# Group by error type
from collections import Counter
error_counts = Counter(f.error for f in failures)
for error, count in error_counts.most_common(10):
    print(f"{count}: {error}")
```

#### Resolution

**Provider Rate Limiting:**
```python
# Implement exponential backoff
from orville_core.media_generation import GenerationOptions

options = GenerationOptions(
    retry_policy="exponential_backoff",
    max_retries=5,
    base_delay=1.0
)
```

**Insufficient Credits:**
```bash
# Check provider account balance
orville-cli provider check-balance --provider openai
orville-cli provider check-balance --provider stability
```

**Model Deprecation:**
```python
# Update to latest model
from orville_core.media_generation import update_provider_config

update_provider_config(
    provider="openai",
    model="dall-e-3",  # Update from dall-e-2
    version="latest"
)
```

### Issue: Validation Bottlenecks

#### Symptom
Validation queue backing up, high latency

#### Diagnosis

```bash
# Check validation queue depth
curl -s http://localhost:8000/metrics/validation | jq '.queue_depth'

# Check processing time distribution
curl -s http://localhost:8000/metrics/validation | jq '.processing_time_histogram'
```

#### Resolution

**Scale Validation Workers:**
```python
# Increase worker pool size
from orville_core.media_validation import ValidationWorkerPool

pool = ValidationWorkerPool()
pool.scale_workers(count=10)  # Increase from default 4
```

**Optimize Validation Policy:**
```python
# Disable expensive checks for non-critical paths
from orville_core.media_validation import MediaValidationPolicy

policy = MediaValidationPolicy(
    modality="image",
    skip_content_safety=True,  # Skip if not needed
    skip_checksum=True,        # Skip if integrity verified elsewhere
    allowed_formats=frozenset({"png", "jpg"})  # Limit formats
)
```

### Issue: Provenance Storage Growth

#### Symptom
Disk usage growing rapidly

#### Diagnosis

```bash
# Find largest provenance directories
du -h /var/lib/orville/provenance/* | sort -hr | head -20

# Check record size distribution
python -c "
from orville_core.media_provenance import MediaProvenanceStore
import json

store = MediaProvenanceStore('/var/lib/orville/provenance')
sizes = []
for record in store.list_history():
    size = len(json.dumps(record.to_dict()))
    sizes.append(size)

import statistics
print(f'Mean: {statistics.mean(sizes):.0f} bytes')
print(f'Median: {statistics.median(sizes):.0f} bytes')
print(f'Max: {max(sizes)} bytes')
"
```

#### Resolution

**Enable Compression:**
```python
# Configure compression for provenance records
from orville_core.media_provenance import ProvenanceConfig

config = ProvenanceConfig(
    compression="gzip",
    compression_level=6,
    max_record_size_mb=10
)
store = MediaProvenanceStore("/var/lib/orville/provenance", config=config)
```

**Implement Retention Policy:**
```python
# Auto-archive old records
from orville_core.media_provenance import RetentionPolicy

policy = RetentionPolicy(
    max_age_days=90,
    archive_location="/archive/provenance",
    delete_after_archive_days=365
)
store.apply_retention_policy(policy)
```

### Issue: API Timeouts

#### Symptom
Clients receiving 504 Gateway Timeout errors

#### Diagnosis

```bash
# Check API response times
curl -w "@curl-format.txt" -s -o /dev/null \
  http://localhost:8000/api/v1/media/generate

# Check server resources
htop
iostat -x 1 10
```

#### Resolution

**Increase Timeout:**
```python
# Update API configuration
from orville_core.api import APIConfig

config = APIConfig(
    timeout_seconds=300,  # Increase from 60
    max_concurrent_generations=20
)
```

**Enable Async Processing:**
```python
# Use async generation for large batches
response = client.post(
    "/api/v1/media/generate",
    json={
        "modality": "image",
        "prompt": "...",
        "async": True  # Return job ID immediately
    }
)

job_id = response.json()["job_id"]

# Poll for completion
while True:
    status = client.get(f"/api/v1/media/jobs/{job_id}")
    if status.json()["status"] in ("completed", "failed"):
        break
    time.sleep(5)
```

## Monitoring Guidelines

### Key Metrics

#### Generation Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Success Rate | >99% | <95% |
| Average Latency | <5s | >10s |
| Queue Depth | <100 | >500 |
| Error Rate | <1% | >5% |

#### Validation Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Throughput | >100/min | <50/min |
| False Positive Rate | <2% | >5% |
| Processing Time | <100ms | >500ms |

#### Provenance Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Storage Growth | <1GB/day | >5GB/day |
| Query Latency | <50ms | >200ms |
| Record Integrity | 100% | <99% |

### Setting Up Alerts

#### Prometheus Alerts

```yaml
# alerts.yml
groups:
  - name: media_alerts
    rules:
      - alert: HighGenerationFailureRate
        expr: rate(media_generation_failures_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High generation failure rate"
          
      - alert: ValidationQueueBacklog
        expr: media_validation_queue_depth > 500
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Validation queue backlog"
          
      - alert: ProvenanceStorageHigh
        expr: media_provenance_storage_bytes > 100000000000  # 100GB
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Provenance storage > 100GB"
```

#### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Orville Media Metrics",
    "panels": [
      {
        "title": "Generation Success Rate",
        "targets": [
          {
            "expr": "rate(media_generation_success_total[5m]) / rate(media_generation_total[5m])"
          }
        ]
      },
      {
        "title": "Validation Throughput",
        "targets": [
          {
            "expr": "rate(media_validation_completed_total[1m])"
          }
        ]
      },
      {
        "title": "Provenance Storage",
        "targets": [
          {
            "expr": "media_provenance_storage_bytes"
          }
        ]
      }
    ]
  }
}
```

### Log Analysis

#### Common Log Patterns

```bash
# Find generation errors
grep "ERROR" /var/log/orville/media-generation.log | tail -100

# Find slow validations
grep "validation.*took.*ms" /var/log/orville/media-validation.log | \
  awk '{if ($NF > 500) print}'

# Find provenance write failures
grep "Failed to write provenance" /var/log/orville/media-provenance.log
```

#### Structured Logging

```python
# Enable structured logging
import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "context": getattr(record, "context", {})
        })

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())

logger = logging.getLogger("orville.media")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usage
logger.info("Generation completed", extra={
    "context": {
        "media_id": "media-001",
        "provider": "openai",
        "duration_ms": 2500
    }
})
```

## Performance Tuning

### Generation Optimization

#### Provider Selection Strategy

```python
# Implement intelligent provider routing
from orville_core.media_generation import ProviderRouter

router = ProviderRouter()
router.set_strategy("latency_optimized")  # or "cost_optimized", "quality_optimized"

# Add provider weights
router.configure_provider("openai", weight=0.6, max_latency_ms=5000)
router.configure_provider("stability", weight=0.4, max_latency_ms=8000)
```

#### Batch Generation

```python
# Generate multiple images efficiently
from orville_core.media_generation import BatchGenerationRequest

batch = BatchGenerationRequest(
    prompts=[
        "A cat playing piano",
        "A dog surfing",
        "A bird singing"
    ],
    options=GenerationOptions(width=1024, height=1024),
    max_concurrent=3
)

results = service.generate_batch(batch)
```

### Validation Optimization

#### Parallel Validation

```python
# Validate multiple files concurrently
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

def validate_file(args):
    file_path, policy = args
    return validate_media(file_path, policy=policy)

# Use process pool for CPU-intensive validation
with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
    results = list(executor.map(
        validate_file,
        [(f, policy) for f in file_paths]
    ))
```

#### Caching Validation Results

```python
# Cache validation results by file hash
from functools import lru_cache
import hashlib

@lru_cache(maxsize=10000)
def get_cached_validation(file_hash: str) -> MediaValidationResult:
    return validation_cache.get(file_hash)

def validate_with_cache(file_path: Path, policy: MediaValidationPolicy):
    file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
    
    cached = get_cached_validation(file_hash)
    if cached:
        return cached
    
    result = validate_media(file_path, policy=policy)
    validation_cache[file_hash] = result
    return result
```

### Provenance Optimization

#### Indexing

```python
# Create indexes for common queries
from orville_core.media_provenance import ProvenanceIndex

index = ProvenanceIndex("/var/lib/orville/provenance")
index.create_index("asset_id")
index.create_index("created_at")
index.create_index("license_type")

# Query with index
records = index.query("created_at", ">=", "2024-01-01")
```

#### Sharding

```python
# Shard provenance by date
from orville_core.media_provenance import ShardedProvenanceStore

store = ShardedProvenanceStore(
    base_path="/var/lib/orville/provenance",
    shard_by="month"
)

# Records automatically sharded by creation date
store.record(...)
```

## Emergency Procedures

### Provider Outage

#### Switch to Backup Provider

```python
# Emergency provider failover
from orville_core.media_generation import EmergencyFailover

failover = EmergencyFailover()
failover.activate(
    primary="openai",
    backup="stability",
    trigger_condition="error_rate > 0.5"
)
```

#### Disable Affected Modality

```bash
# Temporarily disable video generation
orville-cli config set media.generation.video.enabled false

# Re-enable when provider is back
orville-cli config set media.generation.video.enabled true
```

### Data Corruption

#### Restore from Backup

```bash
# Stop services
systemctl stop orville-api

# Restore provenance from backup
tar -xzf /backups/provenance-$(date -d yesterday +%Y%m%d).tar.gz \
  -C /var/lib/orville/

# Verify integrity
orville-cli provenance verify-integrity

# Restart services
systemctl start orville-api
```

#### Rebuild Indexes

```python
# Rebuild provenance indexes
from orville_core.media_provenance import rebuild_indexes

rebuild_indexes("/var/lib/orville/provenance")
```

### Security Incident

#### Revoke Compromised Assets

```python
# Revoke all assets from a compromised generation
from orville_core.media_provenance import revoke_assets

revoke_assets(
    history_id="compromised-history-id",
    reason="Security incident - API key compromise",
    revoked_by="security-team"
)
```

#### Audit Trail Review

```bash
# Export audit trail for security review
orville-cli provenance export-audit \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --output security-audit.json
```

---

## Quick Reference

### Common Commands

```bash
# Check system status
orville-cli status

# View recent generations
orville-cli media list --limit 20

# Validate a file
orville-cli media validate /path/to/file.png

# Get provenance
orville-cli provenance get <media-id>

# Check provider health
orville-cli provider health

# View metrics
orville-cli metrics --service media

# Backup provenance
orville-cli backup create --type provenance

# Restore from backup
orville-cli backup restore --file backup.tar.gz
```

### Emergency Contacts

| Issue | Contact | Escalation |
|-------|---------|------------|
| Provider outage | oncall@orville.ai | #incidents |
| Security incident | security@orville.ai | #security |
| Performance degradation | perf@orville.ai | #sre |
| Data corruption | data@orville.ai | #platform |

---

For more information, see:
- [Media Workflow Guide](MEDIA_WORKFLOW_GUIDE.md)
- [API Reference](API_REFERENCE.md)
- [Architecture Documentation](ARCHITECTURE.md)

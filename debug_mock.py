from unittest.mock import patch
from orville_core import EndpointHealthMonitor, ProviderEndpointSpec

monitor = EndpointHealthMonitor()
spec = ProviderEndpointSpec(
    provider_id='test',
    display_name='Test Provider',
    provider_type='cloud',
    endpoint_url='https://example.test/v1',
    model_identifier='model',
    protocol='openai',
)
monitor.add_endpoint(spec)

print('Before patch:')
health = monitor.get_endpoint_health('https://example.test/v1')
print(f'  Last error: {health.last_error}')

with patch('orville_core.endpoint_probe.probe_endpoint') as mock_probe:
    print(f'  Mock created: {mock_probe}')
    mock_probe.return_value = type('Response', (), {'status': 200, 'reachable': True})()
    print(f'  Mock return value: {mock_probe.return_value}')
    print(f'  Mock called: {mock_probe.called}')
    
    report = monitor.run_probes()
    print(f'After run_probes:')
    print(f'  Mock called: {mock_probe.called}')
    print(f'  Mock call count: {mock_probe.call_count}')
    print(f'  Mock call args: {mock_probe.call_args}')
    print(f'  Report healthy count: {report.healthy_count}')
    print(f'  Report unhealthy count: {report.unhealthy_count}')
    health = monitor.get_endpoint_health('https://example.test/v1')
    print(f'  Health status: {health.status}')
    print(f'  Health consecutive_successes: {health.consecutive_successes}')

import os
os.environ['AWS_ACCESS_KEY_ID'] = 'AKIAIOSFODNN7EXAMPLE'

print('AWS_ACCESS_KEY_ID:', repr(os.getenv('AWS_ACCESS_KEY_ID')))

cloud_indicators = {
    'AWS': 'AWS_ACCESS_KEY_ID',
    'AZURE': 'AZURE_STORAGE_ACCOUNT',
    'GCP': 'GOOGLE_APPLICATION_CREDENTIALS',
    'CLOUD': 'CLOUDSDK_PROJECT',
}

for env_var, provider in cloud_indicators.items():
    value = os.getenv(env_var)
    print(f'{provider}: {repr(value)}')
    if value:
        print(f'Found: {provider}')

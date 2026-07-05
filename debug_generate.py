import json
import urllib.request

payload = {
    'voice_bank': r'E:\diffsinger-webui\models',
    'text': 'hello world',
    'speaker': '',
    'template': r'E:\diffsinger-webui\sample.ds',
    'output_dir': r'E:\diffsinger-webui\output\pred_all'
}
req = urllib.request.Request(
    'http://127.0.0.1:8000/generate',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'}
)
try:
    with urllib.request.urlopen(req, timeout=180) as f:
        print(f.status)
        print(f.read().decode())
except urllib.error.HTTPError as e:
    print('HTTP', e.code)
    print(e.read().decode())
except Exception as e:
    print(type(e).__name__, e)

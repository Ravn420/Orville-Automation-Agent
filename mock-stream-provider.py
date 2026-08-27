from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time

class Handler(BaseHTTPRequestHandler):
    def _send(self, payload, status=200, content_type='application/json'):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.endswith('/models'):
            self._send({'data': [{'id': 'mock-code-model'}]})
        else:
            self._send({'error': 'not found'}, 404)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', '0'))
        payload = json.loads(self.rfile.read(length) or '{}')
        if not self.path.endswith('/chat/completions'):
            self._send({'error': 'not found'}, 404)
            return
        content = '```python\\nprint("orville live code")\\n```\\n\\nGenerated with agentic verification.'
        if payload.get('stream'):
            chunks = [content[:18], content[18:38], content[38:]]
            body = ''.join('data: ' + json.dumps({'choices': [{'delta': {'content': chunk}, 'finish_reason': None}]}) + '\n\n' for chunk in chunks)
            body += 'data: [DONE]\n\n'
            encoded = body.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Content-Length', str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            self.wfile.flush()
        else:
            self._send({'choices': [{'message': {'role': 'assistant', 'content': content}, 'finish_reason': 'stop'}]})

    def log_message(self, *_args):
        return

HTTPServer(('127.0.0.1', 11436), Handler).serve_forever()

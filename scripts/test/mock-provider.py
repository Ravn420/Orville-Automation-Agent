from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class Handler(BaseHTTPRequestHandler):
    def _send(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.endswith('/models'):
            self._send({'data': [{'id': 'mock-model'}]})
        else:
            self._send({'error': 'not found'}, 404)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', '0'))
        payload = json.loads(self.rfile.read(length) or '{}')
        if self.path.endswith('/chat/completions'):
            prompt = payload.get('messages', [{}])[-1].get('content', '')
            self._send({'id': 'mock-completion', 'choices': [{'message': {'role': 'assistant', 'content': 'Mock provider verified: ' + str(prompt)}, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 1, 'completion_tokens': 4}})
        else:
            self._send({'error': 'not found'}, 404)

    def log_message(self, *_args):
        return

HTTPServer(('127.0.0.1', 11435), Handler).serve_forever()

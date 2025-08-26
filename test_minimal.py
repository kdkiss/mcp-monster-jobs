#!/usr/bin/env python3
"""
Minimal test server to validate basic functionality
"""

import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def root():
    return jsonify({"status": "ok", "message": "Minimal server running"})

@app.route('/ready', methods=['GET'])
def ready():
    return jsonify({"status": "ready"})

@app.route('/debug/routes', methods=['GET'])
def debug_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'rule': str(rule)
        })
    return jsonify({'routes': routes})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    print(f"Starting minimal server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
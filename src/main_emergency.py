#!/usr/bin/env python3
"""Emergency minimal server for Smithery deployment"""

import os
import json
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/ping')
def ping():
    return jsonify({"status": "pong"})

@app.route('/mcp', methods=['POST', 'GET'])
def mcp():
    return jsonify({
        "jsonrpc": "2.0",
        "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "monster-jobs-mcp-server", "version": "1.0.0"},
            "capabilities": {"tools": {"listChanged": True}}
        },
        "id": 1
    })

@app.route('/')
def root():
    return jsonify({"name": "Monster Jobs MCP Server", "status": "ready"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    host = os.environ.get('HOST', '0.0.0.0')
    app.run(host=host, port=port, debug=False)
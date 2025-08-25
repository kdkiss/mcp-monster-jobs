#!/usr/bin/env python3
"""
Simple MCP Server for Monster Jobs
"""

import os
from flask import Flask
from flask_cors import CORS
from src.mcp_server import create_mcp_blueprint

# Create Flask app
app = Flask(__name__)
CORS(app)

# Register MCP blueprint
app.register_blueprint(create_mcp_blueprint(), url_prefix='/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

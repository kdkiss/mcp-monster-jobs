#!/usr/bin/env node

// Minimal MCP server for testing
import { Server as McpServer } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

const server = new McpServer({
  name: 'test-mcp-server',
  version: '1.0.0'
}, {
  capabilities: {
    tools: {}
  }
});

// Register a simple test tool
server.setRequestHandler({
  method: 'tools/list',
  params: {}
}, async () => {
  return {
    tools: [
      {
        name: 'test_tool',
        description: 'A simple test tool',
        inputSchema: {
          type: 'object',
          properties: {
            message: {
              type: 'string',
              description: 'Test message'
            }
          }
        }
      }
    ]
  };
});

// Handle tool calls
server.setRequestHandler({
  method: 'tools/call',
  params: {
    name: 'test_tool',
    arguments: {}
  }
}, async (request) => {
  const { message = 'Hello from test MCP server!' } = request.params.arguments;

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify({
          success: true,
          message: message
        }, null, 2)
      }
    ]
  };
});

async function main() {
  try {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.log('Test MCP server running on stdio');
  } catch (error) {
    console.error('Failed to start test MCP server:', error);
    process.exit(1);
  }
}

main();
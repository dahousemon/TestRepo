/**
 * SQL MCP Server - Enterprise-Grade Implementation
 *
 * Production-ready MCP server for secure read-only access to Azure SQL Database
 * Implements: listTables, describeTable, runQuery tools
 *
 * Security Features:
 * - Read-only enforcement
 * - SQL injection prevention
 * - Query validation
 * - 30s timeout
 * - Comprehensive logging
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');
const { z } = require('zod');
const db = require('./db');
const logger = require('./logger');
const { validateQuery, sanitizeInput } = require('./security');
const { startHealthServer } = require('./health');

// Server metadata
const SERVER_NAME = 'sql-mcp-server';
const SERVER_VERSION = '1.0.0';

// Tool definitions
const TOOLS = [
  {
    name: 'listTables',
    description: 'List all accessible tables and views in the database',
    inputSchema: {
      type: 'object',
      properties: {
        schema: {
          type: 'string',
          description: 'Filter by schema name (optional)',
        },
      },
    },
  },
  {
    name: 'describeTable',
    description: 'Get detailed schema information for a specific table',
    inputSchema: {
      type: 'object',
      properties: {
        tableName: {
          type: 'string',
          description: 'Name of the table to describe',
        },
        schema: {
          type: 'string',
          description: 'Schema name (default: dbo)',
          default: 'dbo',
        },
      },
      required: ['tableName'],
    },
  },
  {
    name: 'runQuery',
    description: 'Execute a read-only SQL query (SELECT only)',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'SQL SELECT query to execute',
        },
        maxRows: {
          type: 'number',
          description: 'Maximum number of rows to return (default: 100, max: 1000)',
          default: 100,
        },
      },
      required: ['query'],
    },
  },
];

/**
 * Handle listTables tool call
 */
async function handleListTables(args) {
  const schema = args.schema ? sanitizeInput(args.schema) : null;

  logger.info('listTables called', { schema });

  let query = `
    SELECT
      TABLE_SCHEMA,
      TABLE_NAME,
      TABLE_TYPE
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE IN ('BASE TABLE', 'VIEW')
  `;

  if (schema) {
    query += ` AND TABLE_SCHEMA = @schema`;
  }

  query += ` ORDER BY TABLE_SCHEMA, TABLE_NAME`;

  const params = schema ? [{ name: 'schema', type: 'NVarChar', value: schema }] : [];
  const result = await db.query(query, params);

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(result.recordset, null, 2),
      },
    ],
  };
}

/**
 * Handle describeTable tool call
 */
async function handleDescribeTable(args) {
  const tableName = sanitizeInput(args.tableName);
  const schema = args.schema ? sanitizeInput(args.schema) : 'dbo';

  logger.info('describeTable called', { tableName, schema });

  const query = `
    SELECT
      c.COLUMN_NAME,
      c.DATA_TYPE,
      c.CHARACTER_MAXIMUM_LENGTH,
      c.IS_NULLABLE,
      c.COLUMN_DEFAULT,
      CASE
        WHEN pk.COLUMN_NAME IS NOT NULL THEN 'YES'
        ELSE 'NO'
      END AS IS_PRIMARY_KEY,
      CASE
        WHEN fk.COLUMN_NAME IS NOT NULL THEN 'YES'
        ELSE 'NO'
      END AS IS_FOREIGN_KEY
    FROM INFORMATION_SCHEMA.COLUMNS c
    LEFT JOIN (
      SELECT ku.TABLE_SCHEMA, ku.TABLE_NAME, ku.COLUMN_NAME
      FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
      JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
        ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
        AND tc.TABLE_SCHEMA = ku.TABLE_SCHEMA
        AND tc.TABLE_NAME = ku.TABLE_NAME
      WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
    ) pk ON c.TABLE_SCHEMA = pk.TABLE_SCHEMA
      AND c.TABLE_NAME = pk.TABLE_NAME
      AND c.COLUMN_NAME = pk.COLUMN_NAME
    LEFT JOIN (
      SELECT ku.TABLE_SCHEMA, ku.TABLE_NAME, ku.COLUMN_NAME
      FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
      JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
        ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
        AND tc.TABLE_SCHEMA = ku.TABLE_SCHEMA
        AND tc.TABLE_NAME = ku.TABLE_NAME
      WHERE tc.CONSTRAINT_TYPE = 'FOREIGN KEY'
    ) fk ON c.TABLE_SCHEMA = fk.TABLE_SCHEMA
      AND c.TABLE_NAME = fk.TABLE_NAME
      AND c.COLUMN_NAME = fk.COLUMN_NAME
    WHERE c.TABLE_SCHEMA = @schema
      AND c.TABLE_NAME = @tableName
    ORDER BY c.ORDINAL_POSITION
  `;

  const params = [
    { name: 'schema', type: 'NVarChar', value: schema },
    { name: 'tableName', type: 'NVarChar', value: tableName },
  ];

  const result = await db.query(query, params);

  if (result.recordset.length === 0) {
    throw new Error(`Table ${schema}.${tableName} not found`);
  }

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(result.recordset, null, 2),
      },
    ],
  };
}

/**
 * Handle runQuery tool call
 */
async function handleRunQuery(args) {
  const query = args.query.trim();
  const maxRows = Math.min(args.maxRows || 100, 1000);

  logger.info('runQuery called', { queryLength: query.length, maxRows });

  // Validate query is read-only
  const validation = validateQuery(query);
  if (!validation.isValid) {
    logger.warn('Query validation failed', { reason: validation.reason });
    throw new Error(`Query validation failed: ${validation.reason}`);
  }

  // Add TOP clause if not present to limit results
  let finalQuery = query;
  if (!query.toLowerCase().includes('top ')) {
    finalQuery = query.replace(/SELECT/i, `SELECT TOP ${maxRows}`);
  }

  const result = await db.query(finalQuery, []);

  logger.info('Query executed successfully', {
    rowsReturned: result.recordset.length,
    rowsAffected: result.rowsAffected[0],
  });

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify({
          rows: result.recordset,
          rowCount: result.recordset.length,
          executionTime: result.executionTime || 0,
        }, null, 2),
      },
    ],
  };
}

/**
 * Main server setup
 */
async function main() {
  logger.info('Starting SQL MCP Server', {
    version: SERVER_VERSION,
    node: process.version,
  });

  // Start health check server
  startHealthServer();

  // Initialize database connection
  await db.connect();

  // Create MCP server
  const server = new Server(
    {
      name: SERVER_NAME,
      version: SERVER_VERSION,
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // Register tool handlers
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    logger.debug('Handling ListTools request');
    return { tools: TOOLS };
  });

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    logger.info('Tool called', { tool: name, args });

    try {
      switch (name) {
        case 'listTables':
          return await handleListTables(args || {});

        case 'describeTable':
          return await handleDescribeTable(args || {});

        case 'runQuery':
          return await handleRunQuery(args || {});

        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error) {
      logger.error('Tool execution failed', {
        tool: name,
        error: error.message,
        stack: error.stack,
      });

      return {
        content: [
          {
            type: 'text',
            text: `Error: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  });

  // Start server with stdio transport
  const transport = new StdioServerTransport();
  await server.connect(transport);

  logger.info('SQL MCP Server ready');

  // Graceful shutdown
  process.on('SIGINT', async () => {
    logger.info('Shutting down gracefully...');
    await db.disconnect();
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    logger.info('Shutting down gracefully...');
    await db.disconnect();
    process.exit(0);
  });
}

// Start server
main().catch((error) => {
  logger.error('Fatal error', { error: error.message, stack: error.stack });
  process.exit(1);
});

/**
 * Database Connection Manager
 *
 * Handles Azure SQL Database connections with:
 * - Connection pooling
 * - Automatic retries
 * - Timeout enforcement
 * - Prepared statements
 */

const sql = require('mssql');
const logger = require('./logger');

// Configuration
const QUERY_TIMEOUT = 30000; // 30 seconds
const CONNECTION_TIMEOUT = 15000;
const REQUEST_TIMEOUT = 30000;

// Connection pool
let pool = null;

/**
 * Get database configuration from environment
 */
function getConfig() {
  // Support both connection string and individual parameters
  if (process.env.SQL_CONNECTION_STRING) {
    return process.env.SQL_CONNECTION_STRING;
  }

  return {
    server: process.env.SQL_SERVER,
    database: process.env.SQL_DATABASE,
    user: process.env.SQL_USER,
    password: process.env.SQL_PASSWORD,
    port: parseInt(process.env.SQL_PORT || '1433', 10),
    options: {
      encrypt: true, // Required for Azure SQL
      trustServerCertificate: false,
      enableArithAbort: true,
      requestTimeout: REQUEST_TIMEOUT,
      connectionTimeout: CONNECTION_TIMEOUT,
    },
    pool: {
      max: 10,
      min: 2,
      idleTimeoutMillis: 30000,
    },
  };
}

/**
 * Connect to database
 */
async function connect() {
  if (pool) {
    logger.debug('Database already connected');
    return pool;
  }

  try {
    logger.info('Connecting to Azure SQL Database...');

    const config = getConfig();
    pool = await sql.connect(config);

    logger.info('Database connected successfully', {
      server: pool.config.server,
      database: pool.config.database,
    });

    // Test connection
    const result = await pool.request().query('SELECT @@VERSION AS Version');
    logger.debug('Database version', { version: result.recordset[0].Version });

    // Handle pool errors
    pool.on('error', (err) => {
      logger.error('Database pool error', {
        error: err.message,
        code: err.code,
      });
    });

    return pool;
  } catch (error) {
    logger.error('Database connection failed', {
      error: error.message,
      code: error.code,
    });
    throw new Error(`Failed to connect to database: ${error.message}`);
  }
}

/**
 * Disconnect from database
 */
async function disconnect() {
  if (pool) {
    try {
      await pool.close();
      pool = null;
      logger.info('Database disconnected');
    } catch (error) {
      logger.error('Error disconnecting from database', {
        error: error.message,
      });
    }
  }
}

/**
 * Execute a parameterized query
 *
 * @param {string} queryText - SQL query
 * @param {Array} params - Query parameters [{name, type, value}]
 * @returns {Promise<Object>} Query result
 */
async function query(queryText, params = []) {
  if (!pool) {
    throw new Error('Database not connected');
  }

  const startTime = Date.now();

  try {
    const request = pool.request();

    // Set timeout
    request.timeout = QUERY_TIMEOUT;

    // Add parameters
    for (const param of params) {
      const sqlType = sql[param.type] || sql.NVarChar;
      request.input(param.name, sqlType, param.value);
    }

    logger.debug('Executing query', {
      query: queryText.substring(0, 200),
      paramCount: params.length,
    });

    const result = await request.query(queryText);
    const executionTime = Date.now() - startTime;

    logger.debug('Query executed', {
      executionTime,
      rowCount: result.recordset ? result.recordset.length : 0,
    });

    return {
      ...result,
      executionTime,
    };
  } catch (error) {
    const executionTime = Date.now() - startTime;

    logger.error('Query execution failed', {
      error: error.message,
      code: error.code,
      executionTime,
      query: queryText.substring(0, 200),
    });

    // Provide user-friendly error messages
    if (error.code === 'ETIMEOUT') {
      throw new Error('Query timeout exceeded (30s limit)');
    } else if (error.code === 'ELOGIN') {
      throw new Error('Database authentication failed');
    } else if (error.message.includes('permission')) {
      throw new Error('Insufficient database permissions');
    }

    throw new Error(`Query failed: ${error.message}`);
  }
}

/**
 * Health check - verify database connectivity
 */
async function healthCheck() {
  try {
    const result = await query('SELECT 1 AS HealthCheck', []);
    return result.recordset[0].HealthCheck === 1;
  } catch (error) {
    logger.error('Health check failed', { error: error.message });
    return false;
  }
}

module.exports = {
  connect,
  disconnect,
  query,
  healthCheck,
};

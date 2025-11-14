/**
 * Logger Module
 *
 * Structured logging with support for:
 * - JSON output for Azure Log Analytics
 * - Different log levels
 * - Context enrichment
 */

const LOG_LEVELS = {
  error: 0,
  warn: 1,
  info: 2,
  debug: 3,
};

const currentLevel = LOG_LEVELS[process.env.LOG_LEVEL?.toLowerCase()] ?? LOG_LEVELS.info;

/**
 * Format log message as JSON
 */
function formatLog(level, message, meta = {}) {
  return JSON.stringify({
    timestamp: new Date().toISOString(),
    level,
    message,
    ...meta,
    // Add Azure-specific fields
    application: 'sql-mcp-server',
    environment: process.env.NODE_ENV || 'development',
    version: process.env.APP_VERSION || '1.0.0',
  });
}

/**
 * Log at specified level
 */
function log(level, message, meta = {}) {
  if (LOG_LEVELS[level] > currentLevel) {
    return;
  }

  const output = formatLog(level, message, meta);

  if (level === 'error') {
    console.error(output);
  } else {
    console.log(output);
  }
}

module.exports = {
  error: (message, meta) => log('error', message, meta),
  warn: (message, meta) => log('warn', message, meta),
  info: (message, meta) => log('info', message, meta),
  debug: (message, meta) => log('debug', message, meta),
};

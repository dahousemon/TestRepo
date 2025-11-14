/**
 * Security Module
 *
 * Provides query validation and input sanitization to prevent:
 * - SQL injection
 * - Destructive operations
 * - Unauthorized access
 */

const logger = require('./logger');

// Destructive SQL keywords that should be blocked
const DESTRUCTIVE_KEYWORDS = [
  'INSERT',
  'UPDATE',
  'DELETE',
  'DROP',
  'CREATE',
  'ALTER',
  'TRUNCATE',
  'MERGE',
  'EXEC',
  'EXECUTE',
  'SP_',
  'XP_',
  'GRANT',
  'REVOKE',
  'DENY',
  'BACKUP',
  'RESTORE',
  'SHUTDOWN',
  'BULK',
  'INTO',
];

// Potentially dangerous patterns
const DANGEROUS_PATTERNS = [
  /;\s*(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|EXEC)/i,
  /--\s*$/m, // SQL comments at end
  /\/\*[\s\S]*?\*\//g, // Block comments (could hide malicious code)
  /xp_cmdshell/i,
  /sp_executesql/i,
  /OPENROWSET/i,
  /OPENDATASOURCE/i,
];

/**
 * Validate that a query is read-only (SELECT only)
 *
 * @param {string} query - SQL query to validate
 * @returns {Object} { isValid: boolean, reason?: string }
 */
function validateQuery(query) {
  if (!query || typeof query !== 'string') {
    return {
      isValid: false,
      reason: 'Query must be a non-empty string',
    };
  }

  const normalizedQuery = query.trim().toUpperCase();

  // Check if query starts with SELECT or WITH (for CTEs)
  if (!normalizedQuery.startsWith('SELECT') && !normalizedQuery.startsWith('WITH')) {
    return {
      isValid: false,
      reason: 'Only SELECT queries are allowed',
    };
  }

  // Check for destructive keywords
  for (const keyword of DESTRUCTIVE_KEYWORDS) {
    if (normalizedQuery.includes(keyword)) {
      logger.warn('Destructive keyword detected', { keyword, query: query.substring(0, 100) });
      return {
        isValid: false,
        reason: `Destructive operation not allowed: ${keyword}`,
      };
    }
  }

  // Check for dangerous patterns
  for (const pattern of DANGEROUS_PATTERNS) {
    if (pattern.test(query)) {
      logger.warn('Dangerous pattern detected', { pattern: pattern.source });
      return {
        isValid: false,
        reason: 'Query contains potentially dangerous patterns',
      };
    }
  }

  // Check for multiple statements
  const statements = query.split(';').filter(s => s.trim().length > 0);
  if (statements.length > 1) {
    return {
      isValid: false,
      reason: 'Multiple statements not allowed',
    };
  }

  return { isValid: true };
}

/**
 * Sanitize input to prevent SQL injection
 * Note: This is defense-in-depth; parameterized queries are the primary protection
 *
 * @param {string} input - User input to sanitize
 * @returns {string} Sanitized input
 */
function sanitizeInput(input) {
  if (!input || typeof input !== 'string') {
    return '';
  }

  // Remove any characters that could be used for SQL injection
  // Keep alphanumeric, underscore, space, and common safe characters
  let sanitized = input.replace(/[^\w\s.-]/g, '');

  // Limit length
  if (sanitized.length > 128) {
    sanitized = sanitized.substring(0, 128);
  }

  return sanitized.trim();
}

/**
 * Validate table/schema name format
 *
 * @param {string} name - Table or schema name
 * @returns {boolean}
 */
function isValidObjectName(name) {
  if (!name || typeof name !== 'string') {
    return false;
  }

  // SQL Server object names: alphanumeric, underscore, max 128 chars
  const pattern = /^[a-zA-Z_][a-zA-Z0-9_]{0,127}$/;
  return pattern.test(name);
}

/**
 * Check if a query attempts to access system tables
 *
 * @param {string} query - SQL query
 * @returns {boolean}
 */
function accessesSystemTables(query) {
  const systemTablePatterns = [
    /sys\./i,
    /master\./i,
    /msdb\./i,
    /tempdb\./i,
  ];

  // INFORMATION_SCHEMA is allowed for metadata queries
  const allowedPatterns = [
    /INFORMATION_SCHEMA/i,
  ];

  for (const pattern of systemTablePatterns) {
    if (pattern.test(query)) {
      // Check if it's an allowed pattern
      const isAllowed = allowedPatterns.some(p => p.test(query));
      if (!isAllowed) {
        return true;
      }
    }
  }

  return false;
}

/**
 * Rate limiting data structure
 * In production, use Redis or similar
 */
const rateLimitStore = new Map();

/**
 * Simple rate limiter
 *
 * @param {string} identifier - User/client identifier
 * @param {number} maxRequests - Max requests per window
 * @param {number} windowMs - Time window in milliseconds
 * @returns {boolean} True if allowed, false if rate limited
 */
function checkRateLimit(identifier, maxRequests = 100, windowMs = 60000) {
  const now = Date.now();
  const key = identifier;

  if (!rateLimitStore.has(key)) {
    rateLimitStore.set(key, { count: 1, resetAt: now + windowMs });
    return true;
  }

  const data = rateLimitStore.get(key);

  // Reset if window expired
  if (now >= data.resetAt) {
    rateLimitStore.set(key, { count: 1, resetAt: now + windowMs });
    return true;
  }

  // Check if limit exceeded
  if (data.count >= maxRequests) {
    logger.warn('Rate limit exceeded', { identifier, count: data.count });
    return false;
  }

  // Increment counter
  data.count++;
  return true;
}

/**
 * Clean up expired rate limit entries
 */
function cleanupRateLimits() {
  const now = Date.now();
  for (const [key, data] of rateLimitStore.entries()) {
    if (now >= data.resetAt) {
      rateLimitStore.delete(key);
    }
  }
}

// Cleanup every 5 minutes
setInterval(cleanupRateLimits, 5 * 60 * 1000);

module.exports = {
  validateQuery,
  sanitizeInput,
  isValidObjectName,
  accessesSystemTables,
  checkRateLimit,
};

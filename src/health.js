/**
 * Health Check HTTP Server
 *
 * Provides /health and /ready endpoints for:
 * - Azure Container Apps health probes
 * - Load balancer checks
 * - Monitoring systems
 */

const http = require('http');
const db = require('./db');
const logger = require('./logger');

const PORT = process.env.HEALTH_PORT || 8080;

/**
 * Health check handler
 */
async function handleHealthCheck(req, res) {
  if (req.url === '/health') {
    // Basic liveness check
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
    }));
  } else if (req.url === '/ready') {
    // Readiness check - verify database connectivity
    try {
      const isHealthy = await db.healthCheck();

      if (isHealthy) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          status: 'ready',
          database: 'connected',
          timestamp: new Date().toISOString(),
        }));
      } else {
        res.writeHead(503, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          status: 'not ready',
          database: 'disconnected',
          timestamp: new Date().toISOString(),
        }));
      }
    } catch (error) {
      logger.error('Readiness check failed', { error: error.message });
      res.writeHead(503, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        status: 'error',
        message: error.message,
        timestamp: new Date().toISOString(),
      }));
    }
  } else {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not found' }));
  }
}

/**
 * Start health check server
 */
function startHealthServer() {
  const server = http.createServer(handleHealthCheck);

  server.listen(PORT, () => {
    logger.info('Health check server started', { port: PORT });
  });

  return server;
}

module.exports = {
  startHealthServer,
};

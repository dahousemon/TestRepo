/**
 * Azure Function - Event-Driven Data Ingestion
 *
 * Automatically inserts build and test data into SQL Database
 * Triggered by Event Grid events from CI/CD pipeline
 */

const sql = require('mssql');

// SQL connection pool
let pool = null;

/**
 * Get SQL configuration from environment
 */
function getSqlConfig() {
  return {
    server: process.env.SQL_SERVER,
    database: process.env.SQL_DATABASE,
    user: process.env.SQL_USER,
    password: process.env.SQL_PASSWORD,
    port: 1433,
    options: {
      encrypt: true,
      trustServerCertificate: false,
      enableArithAbort: true,
    },
  };
}

/**
 * Connect to SQL Database
 */
async function connectToDatabase() {
  if (!pool) {
    pool = await sql.connect(getSqlConfig());
  }
  return pool;
}

/**
 * Insert BuildRun record
 */
async function insertBuildRun(data) {
  const pool = await connectToDatabase();

  const request = pool.request();
  request.input('branch', sql.NVarChar(255), data.branch);
  request.input('startTime', sql.DateTime2, new Date(data.startTime));
  request.input('endTime', sql.DateTime2, data.endTime ? new Date(data.endTime) : null);
  request.input('status', sql.NVarChar(50), data.status);
  request.input('triggeredBy', sql.NVarChar(255), data.triggeredBy);
  request.input('commitSha', sql.NVarChar(40), data.commitSha);
  request.input('buildNumber', sql.NVarChar(50), data.buildNumber);

  const result = await request.query(`
    INSERT INTO dbo.BuildRuns (Branch, StartTime, EndTime, Status, TriggeredBy, CommitSha, BuildNumber)
    OUTPUT INSERTED.BuildRunId
    VALUES (@branch, @startTime, @endTime, @status, @triggeredBy, @commitSha, @buildNumber)
  `);

  return result.recordset[0].BuildRunId;
}

/**
 * Insert TestRun records
 */
async function insertTestRuns(buildRunId, tests) {
  const pool = await connectToDatabase();

  for (const test of tests) {
    const request = pool.request();
    request.input('buildRunId', sql.Int, buildRunId);
    request.input('testName', sql.NVarChar(500), test.testName);
    request.input('testSuite', sql.NVarChar(255), test.testSuite);
    request.input('startTime', sql.DateTime2, new Date(test.startTime));
    request.input('endTime', sql.DateTime2, test.endTime ? new Date(test.endTime) : null);
    request.input('status', sql.NVarChar(50), test.status);

    const result = await request.query(`
      INSERT INTO dbo.TestRuns (BuildRunId, TestName, TestSuite, StartTime, EndTime, Status)
      OUTPUT INSERTED.TestRunId
      VALUES (@buildRunId, @testName, @testSuite, @startTime, @endTime, @status)
    `);

    const testRunId = result.recordset[0].TestRunId;

    // Insert failure details if test failed
    if (test.status === 'Failed' && test.failure) {
      await insertTestFailure(testRunId, test.failure);
    }
  }
}

/**
 * Insert TestFailure record
 */
async function insertTestFailure(testRunId, failure) {
  const pool = await connectToDatabase();

  const request = pool.request();
  request.input('testRunId', sql.Int, testRunId);
  request.input('failureReason', sql.NVarChar(sql.MAX), failure.reason);
  request.input('errorMessage', sql.NVarChar(sql.MAX), failure.message);
  request.input('stackTrace', sql.NVarChar(sql.MAX), failure.stackTrace);
  request.input('failureCategory', sql.NVarChar(100), failure.category);

  await request.query(`
    INSERT INTO dbo.TestFailures (TestRunId, FailureReason, ErrorMessage, StackTrace, FailureCategory)
    VALUES (@testRunId, @failureReason, @errorMessage, @stackTrace, @failureCategory)
  `);
}

/**
 * Azure Function HTTP Trigger
 */
module.exports = async function (context, req) {
  context.log('Build data ingestion triggered');

  try {
    const body = req.body;

    // Validate payload
    if (!body || !body.build) {
      context.res = {
        status: 400,
        body: 'Invalid payload: missing build data',
      };
      return;
    }

    // Insert build run
    const buildRunId = await insertBuildRun(body.build);
    context.log(`Inserted BuildRun with ID: ${buildRunId}`);

    // Insert test runs
    if (body.tests && body.tests.length > 0) {
      await insertTestRuns(buildRunId, body.tests);
      context.log(`Inserted ${body.tests.length} test runs`);
    }

    context.res = {
      status: 200,
      body: {
        message: 'Build data ingested successfully',
        buildRunId: buildRunId,
        testsProcessed: body.tests ? body.tests.length : 0,
      },
    };
  } catch (error) {
    context.log.error('Error ingesting build data:', error);

    context.res = {
      status: 500,
      body: {
        error: 'Failed to ingest build data',
        message: error.message,
      },
    };
  }
};

-- =============================================================================
-- Sample Data - DevOps Metrics
-- =============================================================================
-- This script populates the database with realistic sample data for:
--   - BuildRuns
--   - TestRuns
--   - TestFailures
--
-- Use this for development, testing, and demonstrations
-- =============================================================================

USE [DevOpsMetrics];
GO

PRINT 'Inserting sample data...';
GO

-- =============================================================================
-- 1. BuildRuns - Sample CI/CD Builds
-- =============================================================================

SET IDENTITY_INSERT dbo.BuildRuns ON;
GO

INSERT INTO dbo.BuildRuns (BuildRunId, Branch, StartTime, EndTime, Status, TriggeredBy, CommitSha, BuildNumber)
VALUES
    -- Successful builds
    (1, 'main', DATEADD(HOUR, -48, GETUTCDATE()), DATEADD(HOUR, -48, DATEADD(MINUTE, 12, GETUTCDATE())), 'Success', 'github-actions', 'a1b2c3d4e5f6', 'Build-1001'),
    (2, 'main', DATEADD(HOUR, -24, GETUTCDATE()), DATEADD(HOUR, -24, DATEADD(MINUTE, 15, GETUTCDATE())), 'Success', 'github-actions', 'b2c3d4e5f6a1', 'Build-1002'),
    (3, 'main', DATEADD(HOUR, -12, GETUTCDATE()), DATEADD(HOUR, -12, DATEADD(MINUTE, 11, GETUTCDATE())), 'Success', 'github-actions', 'c3d4e5f6a1b2', 'Build-1003'),

    -- Feature branch builds
    (4, 'feature/authentication', DATEADD(HOUR, -36, GETUTCDATE()), DATEADD(HOUR, -36, DATEADD(MINUTE, 14, GETUTCDATE())), 'Success', 'john.doe@company.com', 'd4e5f6a1b2c3', 'Build-1004'),
    (5, 'feature/authentication', DATEADD(HOUR, -30, GETUTCDATE()), DATEADD(HOUR, -30, DATEADD(MINUTE, 16, GETUTCDATE())), 'Failed', 'john.doe@company.com', 'e5f6a1b2c3d4', 'Build-1005'),
    (6, 'feature/authentication', DATEADD(HOUR, -28, GETUTCDATE()), DATEADD(HOUR, -28, DATEADD(MINUTE, 13, GETUTCDATE())), 'Success', 'john.doe@company.com', 'f6a1b2c3d4e5', 'Build-1006'),

    -- API feature branch
    (7, 'feature/api-v2', DATEADD(HOUR, -20, GETUTCDATE()), DATEADD(HOUR, -20, DATEADD(MINUTE, 18, GETUTCDATE())), 'Success', 'jane.smith@company.com', 'a1b2c3d4e5f7', 'Build-1007'),
    (8, 'feature/api-v2', DATEADD(HOUR, -18, GETUTCDATE()), DATEADD(HOUR, -18, DATEADD(MINUTE, 17, GETUTCDATE())), 'Failed', 'jane.smith@company.com', 'b2c3d4e5f6a2', 'Build-1008'),

    -- Hotfix branch
    (9, 'hotfix/critical-bug', DATEADD(HOUR, -8, GETUTCDATE()), DATEADD(HOUR, -8, DATEADD(MINUTE, 10, GETUTCDATE())), 'Success', 'ops-team@company.com', 'c3d4e5f6a1b3', 'Build-1009'),

    -- Recent builds with various statuses
    (10, 'develop', DATEADD(HOUR, -6, GETUTCDATE()), DATEADD(HOUR, -6, DATEADD(MINUTE, 14, GETUTCDATE())), 'Success', 'github-actions', 'd4e5f6a1b2c4', 'Build-1010'),
    (11, 'develop', DATEADD(HOUR, -4, GETUTCDATE()), DATEADD(HOUR, -4, DATEADD(MINUTE, 5, GETUTCDATE())), 'Cancelled', 'auto-merge-bot', 'e5f6a1b2c3d5', 'Build-1011'),
    (12, 'main', DATEADD(HOUR, -2, GETUTCDATE()), DATEADD(HOUR, -2, DATEADD(MINUTE, 13, GETUTCDATE())), 'Success', 'release-bot', 'f6a1b2c3d4e6', 'Build-1012'),

    -- Running build (no end time)
    (13, 'feature/new-dashboard', DATEADD(MINUTE, -10, GETUTCDATE()), NULL, 'Running', 'developer@company.com', 'a1b2c3d4e5f8', 'Build-1013');
GO

SET IDENTITY_INSERT dbo.BuildRuns OFF;
GO

PRINT 'Inserted 13 BuildRuns records';
GO

-- =============================================================================
-- 2. TestRuns - Sample Test Executions
-- =============================================================================

SET IDENTITY_INSERT dbo.TestRuns ON;
GO

-- Build 1 Tests (All passed)
INSERT INTO dbo.TestRuns (TestRunId, BuildRunId, TestName, TestSuite, StartTime, EndTime, Status)
VALUES
    (1, 1, 'test_user_login_success', 'AuthenticationTests', DATEADD(HOUR, -48, GETUTCDATE()), DATEADD(HOUR, -48, DATEADD(SECOND, 2, GETUTCDATE())), 'Passed'),
    (2, 1, 'test_user_logout', 'AuthenticationTests', DATEADD(HOUR, -48, DATEADD(SECOND, 2, GETUTCDATE())), DATEADD(HOUR, -48, DATEADD(SECOND, 3, GETUTCDATE())), 'Passed'),
    (3, 1, 'test_api_get_users', 'APITests', DATEADD(HOUR, -48, DATEADD(SECOND, 3, GETUTCDATE())), DATEADD(HOUR, -48, DATEADD(SECOND, 5, GETUTCDATE())), 'Passed'),
    (4, 1, 'test_database_connection', 'IntegrationTests', DATEADD(HOUR, -48, DATEADD(SECOND, 5, GETUTCDATE())), DATEADD(HOUR, -48, DATEADD(SECOND, 8, GETUTCDATE())), 'Passed'),

-- Build 2 Tests (Mostly passed, one flaky)
    (5, 2, 'test_user_login_success', 'AuthenticationTests', DATEADD(HOUR, -24, GETUTCDATE()), DATEADD(HOUR, -24, DATEADD(SECOND, 2, GETUTCDATE())), 'Passed'),
    (6, 2, 'test_user_logout', 'AuthenticationTests', DATEADD(HOUR, -24, DATEADD(SECOND, 2, GETUTCDATE())), DATEADD(HOUR, -24, DATEADD(SECOND, 3, GETUTCDATE())), 'Passed'),
    (7, 2, 'test_api_get_users', 'APITests', DATEADD(HOUR, -24, DATEADD(SECOND, 3, GETUTCDATE())), DATEADD(HOUR, -24, DATEADD(SECOND, 6, GETUTCDATE())), 'Failed'),
    (8, 2, 'test_database_connection', 'IntegrationTests', DATEADD(HOUR, -24, DATEADD(SECOND, 6, GETUTCDATE())), DATEADD(HOUR, -24, DATEADD(SECOND, 9, GETUTCDATE())), 'Passed'),
    (9, 2, 'test_payment_processing', 'PaymentTests', DATEADD(HOUR, -24, DATEADD(SECOND, 9, GETUTCDATE())), DATEADD(HOUR, -24, DATEADD(SECOND, 15, GETUTCDATE())), 'Passed'),

-- Build 3 Tests (All passed - flaky test now passes)
    (10, 3, 'test_user_login_success', 'AuthenticationTests', DATEADD(HOUR, -12, GETUTCDATE()), DATEADD(HOUR, -12, DATEADD(SECOND, 2, GETUTCDATE())), 'Passed'),
    (11, 3, 'test_user_logout', 'AuthenticationTests', DATEADD(HOUR, -12, DATEADD(SECOND, 2, GETUTCDATE())), DATEADD(HOUR, -12, DATEADD(SECOND, 3, GETUTCDATE())), 'Passed'),
    (12, 3, 'test_api_get_users', 'APITests', DATEADD(HOUR, -12, DATEADD(SECOND, 3, GETUTCDATE())), DATEADD(HOUR, -12, DATEADD(SECOND, 5, GETUTCDATE())), 'Passed'),
    (13, 3, 'test_database_connection', 'IntegrationTests', DATEADD(HOUR, -12, DATEADD(SECOND, 5, GETUTCDATE())), DATEADD(HOUR, -12, DATEADD(SECOND, 8, GETUTCDATE())), 'Passed'),

-- Build 5 Tests (Failed build - multiple test failures)
    (14, 5, 'test_user_login_success', 'AuthenticationTests', DATEADD(HOUR, -30, GETUTCDATE()), DATEADD(HOUR, -30, DATEADD(SECOND, 2, GETUTCDATE())), 'Failed'),
    (15, 5, 'test_user_logout', 'AuthenticationTests', DATEADD(HOUR, -30, DATEADD(SECOND, 2, GETUTCDATE())), DATEADD(HOUR, -30, DATEADD(SECOND, 3, GETUTCDATE())), 'Failed'),
    (16, 5, 'test_api_get_users', 'APITests', DATEADD(HOUR, -30, DATEADD(SECOND, 3, GETUTCDATE())), DATEADD(HOUR, -30, DATEADD(SECOND, 5, GETUTCDATE())), 'Passed'),

-- Build 8 Tests (Failed build)
    (17, 8, 'test_api_v2_endpoints', 'APITests', DATEADD(HOUR, -18, GETUTCDATE()), DATEADD(HOUR, -18, DATEADD(SECOND, 4, GETUTCDATE())), 'Failed'),
    (18, 8, 'test_api_v2_authentication', 'APITests', DATEADD(HOUR, -18, DATEADD(SECOND, 4, GETUTCDATE())), DATEADD(HOUR, -18, DATEADD(SECOND, 6, GETUTCDATE())), 'Passed'),

-- Build 12 Tests (Recent successful build)
    (19, 12, 'test_user_login_success', 'AuthenticationTests', DATEADD(HOUR, -2, GETUTCDATE()), DATEADD(HOUR, -2, DATEADD(SECOND, 2, GETUTCDATE())), 'Passed'),
    (20, 12, 'test_user_logout', 'AuthenticationTests', DATEADD(HOUR, -2, DATEADD(SECOND, 2, GETUTCDATE())), DATEADD(HOUR, -2, DATEADD(SECOND, 3, GETUTCDATE())), 'Passed'),
    (21, 12, 'test_api_get_users', 'APITests', DATEADD(HOUR, -2, DATEADD(SECOND, 3, GETUTCDATE())), DATEADD(HOUR, -2, DATEADD(SECOND, 5, GETUTCDATE())), 'Failed'),
    (22, 12, 'test_database_connection', 'IntegrationTests', DATEADD(HOUR, -2, DATEADD(SECOND, 5, GETUTCDATE())), DATEADD(HOUR, -2, DATEADD(SECOND, 8, GETUTCDATE())), 'Passed'),
    (23, 12, 'test_cache_performance', 'PerformanceTests', DATEADD(HOUR, -2, DATEADD(SECOND, 8, GETUTCDATE())), DATEADD(HOUR, -2, DATEADD(SECOND, 25, GETUTCDATE())), 'Passed');
GO

SET IDENTITY_INSERT dbo.TestRuns OFF;
GO

PRINT 'Inserted 23 TestRuns records';
GO

-- =============================================================================
-- 3. TestFailures - Detailed Failure Information
-- =============================================================================

SET IDENTITY_INSERT dbo.TestFailures ON;
GO

INSERT INTO dbo.TestFailures (TestFailureId, TestRunId, FailureReason, ErrorMessage, StackTrace, FailureCategory)
VALUES
    -- Build 2, Test 7 failure (flaky test)
    (1, 7, 'Timeout waiting for API response',
     'Request timeout after 30 seconds',
     'at APIClient.get (api-client.js:45)\n  at test_api_get_users (auth.test.js:123)\n  at processTicksAndRejections (internal/process/task_queues.js:95)',
     'Timeout'),

    -- Build 5 failures (authentication module broken)
    (2, 14, 'Authentication service unavailable',
     'ECONNREFUSED: Connection refused to auth service on port 8081',
     'at TCPConnectWrap.afterConnect (net.js:1148:16)\n  at AuthService.connect (auth-service.js:78)\n  at test_user_login_success (auth.test.js:89)',
     'Infrastructure'),

    (3, 15, 'Cannot logout - user not logged in',
     'AssertionError: expected user to be logged in but was not',
     'at Context.test_user_logout (auth.test.js:145)\n  at processImmediate (internal/timers.js:464:21)',
     'Logic Error'),

    -- Build 8 failure (API v2 issue)
    (4, 17, 'API endpoint returned 500',
     'Internal Server Error: Database query timeout',
     'at Server.handleRequest (server.js:234)\n  at /api/v2/users (routes.js:67)\n  at test_api_v2_endpoints (api-v2.test.js:45)',
     'Server Error'),

    -- Build 12 failure (same flaky test)
    (5, 21, 'Timeout waiting for API response',
     'Request timeout after 30 seconds',
     'at APIClient.get (api-client.js:45)\n  at test_api_get_users (auth.test.js:123)\n  at processTicksAndRejections (internal/process/task_queues.js:95)',
     'Timeout');
GO

SET IDENTITY_INSERT dbo.TestFailures OFF;
GO

PRINT 'Inserted 5 TestFailures records';
GO

-- =============================================================================
-- Summary
-- =============================================================================

PRINT '';
PRINT '=============================================================================';
PRINT 'Sample data insertion completed!';
PRINT '=============================================================================';
PRINT '';
PRINT 'Data Summary:';
PRINT '  - BuildRuns: 13 records';
PRINT '  - TestRuns: 23 records';
PRINT '  - TestFailures: 5 records';
PRINT '';
PRINT 'Example queries to explore the data:';
PRINT '  SELECT * FROM BuildRuns ORDER BY StartTime DESC;';
PRINT '  SELECT * FROM vw_TestFlakiness;';
PRINT '  SELECT * FROM vw_BuildStatsDaily;';
PRINT '  SELECT * FROM vw_TopFailingTests;';
PRINT '=============================================================================';
GO

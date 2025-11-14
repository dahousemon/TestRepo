# SQL Query Examples

Useful SQL queries for the DevOps Metrics database.

## Build Analytics

### Recent Builds

```sql
SELECT TOP 20
    BuildRunId,
    Branch,
    StartTime,
    DurationSeconds,
    Status,
    TriggeredBy
FROM BuildRuns
ORDER BY StartTime DESC;
```

### Build Success Rate by Branch

```sql
SELECT
    Branch,
    COUNT(*) AS TotalBuilds,
    SUM(CASE WHEN Status = 'Success' THEN 1 ELSE 0 END) AS SuccessfulBuilds,
    CAST(SUM(CASE WHEN Status = 'Success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS SuccessRate
FROM BuildRuns
WHERE StartTime >= DATEADD(DAY, -30, GETUTCDATE())
GROUP BY Branch
ORDER BY SuccessRate DESC;
```

### Slowest Builds

```sql
SELECT TOP 10
    BuildRunId,
    Branch,
    StartTime,
    DurationSeconds,
    Status
FROM BuildRuns
WHERE DurationSeconds IS NOT NULL
ORDER BY DurationSeconds DESC;
```

## Test Analytics

### Most Failing Tests

```sql
SELECT TOP 20
    tr.TestName,
    tr.TestSuite,
    COUNT(*) AS FailureCount,
    MAX(tr.StartTime) AS LastFailure
FROM TestRuns tr
WHERE tr.Status = 'Failed'
  AND tr.StartTime >= DATEADD(DAY, -30, GETUTCDATE())
GROUP BY tr.TestName, tr.TestSuite
ORDER BY FailureCount DESC;
```

### Flaky Tests

```sql
SELECT *
FROM vw_TestFlakiness
WHERE FlakinessScore > 30
  AND TotalRuns >= 10
ORDER BY FlakinessScore DESC;
```

### Test Execution Time Trends

```sql
SELECT
    TestName,
    MIN(DurationSeconds) AS MinDuration,
    AVG(CAST(DurationSeconds AS FLOAT)) AS AvgDuration,
    MAX(DurationSeconds) AS MaxDuration,
    COUNT(*) AS RunCount
FROM TestRuns
WHERE DurationSeconds IS NOT NULL
  AND StartTime >= DATEADD(DAY, -30, GETUTCDATE())
GROUP BY TestName
HAVING COUNT(*) > 5
ORDER BY AvgDuration DESC;
```

## Failure Analysis

### Recent Test Failures with Details

```sql
SELECT
    br.BuildRunId,
    br.Branch,
    tr.TestName,
    tf.ErrorMessage,
    tf.FailureCategory,
    tf.LoggedAt
FROM BuildRuns br
INNER JOIN TestRuns tr ON br.BuildRunId = tr.BuildRunId
INNER JOIN TestFailures tf ON tr.TestRunId = tf.TestRunId
WHERE br.StartTime >= DATEADD(DAY, -7, GETUTCDATE())
ORDER BY tf.LoggedAt DESC;
```

### Failure Categories

```sql
SELECT
    tf.FailureCategory,
    COUNT(*) AS FailureCount,
    COUNT(DISTINCT tr.TestName) AS AffectedTests
FROM TestFailures tf
INNER JOIN TestRuns tr ON tf.TestRunId = tr.TestRunId
WHERE tf.LoggedAt >= DATEADD(DAY, -30, GETUTCDATE())
GROUP BY tf.FailureCategory
ORDER BY FailureCount DESC;
```

## Daily Trends

### Build Activity by Day

```sql
SELECT *
FROM vw_BuildStatsDaily
WHERE BuildDate >= DATEADD(DAY, -30, GETUTCDATE())
ORDER BY BuildDate DESC;
```

### Test Pass Rate Trend

```sql
SELECT
    CAST(tr.StartTime AS DATE) AS TestDate,
    COUNT(*) AS TotalTests,
    SUM(CASE WHEN tr.Status = 'Passed' THEN 1 ELSE 0 END) AS PassedTests,
    CAST(SUM(CASE WHEN tr.Status = 'Passed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS PassRate
FROM TestRuns tr
WHERE tr.StartTime >= DATEADD(DAY, -30, GETUTCDATE())
GROUP BY CAST(tr.StartTime AS DATE)
ORDER BY TestDate DESC;
```

## Advanced Queries

### Tests That Always Fail Together

```sql
WITH FailedBuildTests AS (
    SELECT
        br.BuildRunId,
        tr.TestName
    FROM BuildRuns br
    INNER JOIN TestRuns tr ON br.BuildRunId = tr.BuildRunId
    WHERE br.Status = 'Failed'
      AND tr.Status = 'Failed'
)
SELECT
    t1.TestName AS Test1,
    t2.TestName AS Test2,
    COUNT(*) AS CoFailureCount
FROM FailedBuildTests t1
INNER JOIN FailedBuildTests t2
    ON t1.BuildRunId = t2.BuildRunId
    AND t1.TestName < t2.TestName
GROUP BY t1.TestName, t2.TestName
HAVING COUNT(*) > 3
ORDER BY CoFailureCount DESC;
```

### Build Performance Over Time

```sql
SELECT
    CAST(StartTime AS DATE) AS BuildDate,
    Branch,
    AVG(CAST(DurationSeconds AS FLOAT)) AS AvgDurationSeconds,
    MIN(DurationSeconds) AS MinDurationSeconds,
    MAX(DurationSeconds) AS MaxDurationSeconds
FROM BuildRuns
WHERE StartTime >= DATEADD(DAY, -30, GETUTCDATE())
  AND DurationSeconds IS NOT NULL
GROUP BY CAST(StartTime AS DATE), Branch
ORDER BY BuildDate DESC, Branch;
```

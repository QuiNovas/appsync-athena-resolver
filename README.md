# appsync-athena-resolver

# Environment Variables:
- **AWS_ATHENA_REGION_NAME** OPTIONAL - The AWS region for Athena that this function should use. If missing, will use the region that the fnuction is executing in.
- **AWS_ATHENA_S3_STAGING_DIR** REQUIRED - This is the S3 location that Athena will store the query results in. It must be in the format `s3://YOUR_S3_BUCKET/path/to/`.
- **AWS_ATHENA_SCHEMA_NAME** OPTIONAL - The schema/database name that you wish to query. If not provided, will default to the _default_ schema/database.
- **MAX_CONCURRENT_QUERIES** OPTIONAL - The maximum number of concurrent queries to run in Athena. Defaults to `5`.
- **POLL_INTERVAL** OPTIONAL - The rate at which to poll Athena for a response, in seconds. Defaults to `1.0`.

# AWS Permissions Required:
You will need Athena and Glue (if you create your schema with Glue) permissions:
```
"athena:StopQueryExecution",
"athena:StartQueryExecution",
"athena:RunQuery",
"athena:ListQueryExecutions",
"athena:GetTables",
"athena:GetTable",
"athena:GetQueryResultsStream",
"athena:GetQueryResults",
"athena:GetQueryExecutions",
"athena:GetQueryExecution",
"athena:GetNamespaces",
"athena:GetNamespace",
"athena:GetExecutionEngines",
"athena:GetExecutionEngine",
"athena:GetCatalogs",
"athena:CancelQueryExecution",
"athena:BatchGetQueryExecution",
"glue:GetTable",
"glue:GetPartitions"
```
You will also require read access to the underlying Athena datasource, read and write access to the Athena result S3 bucket, and access to any KMS keys used in either of those.
 
# Handler Method
function.handler

# Use with AWS AppSync
This function supports both the `Invoke` and `BatchInvoke` options for Lambda resolver mapping.

When resolver mapping, the following payload is required:
```
{
    "query": "string",
    "params": map | list(map),
    "single_result": boolean (OPTIONAL - defaults to false)
}
```
- _(dict)_
    - **query** _(string)_ -- 
    **[REQUIRED]** The query string to execute against _AWS_ATHENA_SCHEMA_NAME_. It may be parameterized with `PyFormat`, only only supporting [named placeholders](https://pyformat.info/#named_placeholders) with the old `%` operator style. If `%` character is contained in your query, it must be escaped with `%%`.
    - **single_result** _(boolean)_ -- 
    `true` if AppSync is expecting a single map result, `false` or missing if multiple results (`maps`) in a `list` may be returned.
    - **params** _(map)_ | _(list(map))_ -- 
    **[REQUIRED]** if your _query_ is parameterized. In the case of a `BatchInvoke`, this will be a `list` of `maps`. Normally, this will either be `$context.arguments` or `$context.source`.

Results from this function will be a `map` or a `list` of `maps`, with the keys for each `map` being the names of the columns of the returned rows.
    
_**NOTE**_ - it is up to you to construct your queries to match both the parameters you pass in and the number of results and result types you want out.

# Lambda package location
https://s3.amazonaws.com/lambdalambdalambda-repo/quinovas/appsync-athena-resolver/appsync-athena-resolver-0.1.0.zip



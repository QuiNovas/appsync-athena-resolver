appsync-athena-resolver
=======================

.. _APL2: http://www.apache.org/licenses/LICENSE-2.0.txt
.. _named placeholders: https://pyformat.info/#named_placeholders
.. _AWS Athena: https://docs.aws.amazon.com/athena/latest/ug/what-is.html
.. _PyFormat: https://pyformat.info/
.. _AWS AppSync: https://docs.aws.amazon.com/appsync/latest/devguide/welcome.html

This is a generic Lambda task function that can execute athena queries.
It is intended to be used in `AWS AppSync`_.
This function will take the input information, call `AWS Athena`_, and respond
to `AWS AppSync`_ with the results of the SQL call.

Environment Variables
---------------------
**AWS_ATHENA_REGION_NAME**: OPTIONAL
  The AWS region for Athena that this function should use.
  If missing, will use the region that the fnuction is executing in.
**AWS_ATHENA_S3_STAGING_DIR**: REQUIRED
  This is the S3 location that Athena will store the query results in.
  It must be in the format `s3://YOUR_S3_BUCKET/path/to/`.
**AWS_ATHENA_SCHEMA_NAME**: OPTIONAL
  The schema/database name that you wish to query by default. The
  **schemaName** input parameter will override this environment
  variable if present. If neither is provided, will default to the
  `default` schema/database.
**MAX_CONCURRENT_QUERIES**: OPTIONAL
  The maximum number of concurrent queries to run in Athena. Defaults
  to `5`.
**POLL_INTERVAL**: OPTIONAL
  The rate at which to poll Athena for a response, in seconds. Defaults
  to `1.0`.

AWS Permissions Required
------------------------
- athena:StopQueryExecution
- athena:StartQueryExecution
- athena:RunQuery
- athena:ListQueryExecutions
- athena:GetTables
- athena:GetTable
- athena:GetQueryResultsStream
- athena:GetQueryResults
- athena:GetQueryExecutions
- athena:GetQueryExecution
- athena:GetNamespaces
- athena:GetNamespace
- athena:GetExecutionEngines
- athena:GetExecutionEngine
- athena:GetCatalogs
- athena:CancelQueryExecution
- athena:BatchGetQueryExecution
- glue:GetTable
- glue:GetPartitions

You will also require read access to the underlying `AWS Athena`_ datasource,
read and write access to the Athena result S3 bucket, and access to any KMS
keys used in either of those.

Handler Method
--------------
.. code::

  function.handler

Request Syntax
--------------
.. code::

  {
      "query": "string",
      "params": map | list(map),
      "schemaName": "string",
      "singleResult": boolean,
      "single_result": boolean
  }

**query**: REQUIRED
  This is the query string to be executed. It may be parameterized with
  `PyFormat`_, using the new format `{}` `named placeholders`_ method.
**params**: OPTIONAL
  Required if your `query` is parameterized. The keys in this map should
  correspond to the format names in your operation string or array.
**schemaName**: OPTIONAL
  The schema/database name that you wish to query. Overrides
  **AWS_ATHENA_SCHEMA_NAME** if present.
**singleResult**: OPTIONAL
  `true` if AppSync is expecting a single map result, `false` if multiple
  results (`maps`) in a `list` may be returned. Defaults to `false`.
**single_result**: OPTIONAL, DEPRECATED
  Use **singleResult** instead.

Lambda Package Location
-----------------------
https://s3.amazonaws.com/lambdalambdalambda-repo/quinovas/athena-task/appsync-athena-resolver-0.2.0.zip

License: `APL2`_

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
:DATABASE: The `AWS Athena`_ Database to query.
  May be overridden in the ``query`` request. Defaults to ``default``
:WORKGROUP: The `AWS Athena`_ Workgroup to use during queries.
  May be overridden in the ``query`` request. Defaults to ``primary``.
:MAX_CONCURRENT_QUERIES: The maximum number of concurrent queries allowed in
  BatchInvoke requests. Defaults to ``5``.

AWS Permissions Required
------------------------
* **AmazonAthenaFullAccess** arn:aws:iam::aws:policy/AmazonAthenaFullAccess

You will also require read access to the underlying `AWS Athena`_ datasource
and access to any KMS keys used.


Handler Method
--------------
.. code::

  function.handler

Request Syntax
--------------
Request::

  {
      "query": "select * from bar",
      "params": {},
      "database": "foo",
      "workgroup": "myworkgroup",
      "singleResult": boolean
  }

**query**: REQUIRED
  This is the query string to be executed. It may be parameterized with
  `PyFormat`_, using the new format `{}` `named placeholders`_ method.
**params**: OPTIONAL
  Required if your `query` is parameterized. The keys in this map should
  correspond to the format names in your operation string or array.
**database**: OPTIONAL
  The schema/database name that you wish to query. Overrides
  **DATABASE** if present.
**workgroup**: OPTIONAL
  The `AWS Athena`_ Workgroup to use during. Overrides
  **WORKGROUP** if present.
**singleResult**: OPTIONAL
  `true` if AppSync is expecting a single map result, `false` if multiple
  results (`maps`) in a `list` may be returned. Defaults to `false`.

Response:

  If `singleResult` is `true`::

    {
      "Key": Value,
      (Keys and values are generated from the query results.
      Keys are the column names, values are converted to their
      specified types.)
    }

  If `singleResult` is `false`::

    [
      {
        "Key": Value,
        (Keys and values are generated from the query results.
        Keys are the column names, values are converted to their
        specified types.)
      }
    ]

Lambda Package Location
-----------------------
https://s3.amazonaws.com/lambdalambdalambda-repo/quinovas/athena-task/appsync-athena-resolver-0.4.0.zip

License: `APL2`_

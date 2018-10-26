import boto3
import json
import logging.config
import os

from pyathena import connect
from pyathena.async_cursor import AsyncCursor

connection = connect(
    cursor_class=AsyncCursor,
    poll_interval=float(os.environ.get('POLL_INTERVAL', 1.0)),
    region_name=os.environ.get('AWS_ATHENA_REGION_NAME', boto3.session.Session().region_name),
    s3_staging_dir=os.environ['AWS_ATHENA_S3_STAGING_DIR'],
    schema_name=os.environ.get('AWS_ATHENA_SCHEMA_NAME', 'default')
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
max_concurrent_queries = int(os.environ.get('MAX_CONCURRENT_QUERIES', 5))


def map_result(description, row):
    result = {}
    for column in range(0, len(description)):
        result[description[column][0]] = row[column]
    return result


def process_result_set(result_set, single_result):
    results = []
    logger.debug('Query "{}" returned in {}ms'.format(result_set.query, result_set.execution_time_in_millis))
    description = result_set.description
    for row in result_set:
        if single_result and len(results) == 1:
            raise Exception('Query "{}" returned more than one row, but result should be a single row'.format(result_set.query))
        results.append(map_result(description, row))
    logger.debug('Query returned {} results'.format(len(results)))
    return results if not single_result else results[0] if len(results) else {}


def handler(event, context):
    logger.debug(
        'Processing event {} for Athena schema {}'.format(
            json.dumps(event),
            os.environ.get('AWS_ATHENA_SCHEMA_NAME', 'default')
        )
    )
    if type(event) is dict:
        logger.info('Processing Invoke operation')
        with connection.cursor(max_workers=1) as cursor:
            query_id, future = cursor.execute(event['query'], event.get('params'))
            # Default to multiple results if not present
            result = process_result_set(future.result(), event.get('single_result', False))
    else:
        logger.debug('Processing BatchInvoke operation with a batch of {}'.format(len(event)))
        result = []
        max_workers = min(len(event), max_concurrent_queries)
        with connection.cursor(max_workers=max_workers) as cursor:
            futures = []
            for item in event:
                futures.append(cursor.execute(item['query'], item.get('params'))[1])
            for count in range(0, len(futures)):
                # Batch results are always arrays of arrays of maps
                result.append(process_result_set(futures[count].result(), False))
    return result

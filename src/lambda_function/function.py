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
    logger.debug('Processing event {}'.format(json.dumps(event)))
    if event['operation'] == 'Invoke':
        logger.info('Processing 1 payload')
        with connection.cursor(max_workers=1) as cursor:
            payload = event['payload']
            query_id, future = cursor.execute(payload['query'], payload.get('params'))
            result = process_result_set(future.result(), payload.get('single_result'))
    elif event['operation'] == 'BatchInvoke':
        payloads = event['payload']
        logger.debug('Processing {} payloads'.format(len(payloads)))
        result = []
        max_workers = min(len(payloads), max_concurrent_queries)
        with connection.cursor(max_workers=max_workers) as cursor:
            futures = []
            for payload in payloads:
                futures.append(cursor.execute(payload['query'], payload.get('params'))[1])
            for count in range(0, len(futures)):
                result.append(process_result_set(futures[count].result(), payloads[count]['single_result']))
    else:
        raise Exception('operation {} not supported'.format(event['operation']))
    return result

import json
import logging.config
import os

from pyathena import connect


connection = connect(
    region_name=os.environ['AWS_ATHENA_REGION_NAME'],
    schema_name=os.environ.get('AWS_ATHENA_SCHEMA_NAME', 'default')
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def map_result(description, row):
    result = {}
    for column in range(0, len(description)):
        result[description[column][0]] = row[column]
    return result


def execute_query(query, single_result, params):
    results = []
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        description = cursor.description
        for row in cursor:
            if single_result and len(results) == 1:
                raise Exception(
                    'Query {} returned more than one row, but result should be a single row'.format(cursor.query)
                )
            results.append(map_result(description, row))
    logger.debug('Query returned {} results'.format(len(results)))
    return results if not single_result else results[0] if len(results) else {}


def handler(event, context):
    logger.debug('Processing event {}'.format(json.dumps(event)))
    if event['operation'] == 'Invoke':
        result = execute_query(event['query'], event.get('single_result'), event.get('params'))
    elif event['operation'] == 'BatchInvoke':
        result = []
        for sub_event in event:
            result.append(execute_query(sub_event['query'], sub_event.get('single_result'), sub_event.get('params')))
    else:
        raise Exception('operation {} not supported'.format(event['operation']))
    return result

from backoff import on_predicate, fibo
from binascii import a2b_hex
from boto3 import client
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime
from decimal import Decimal
from distutils.util import strtobool
from json import dumps as jsondumps, loads as jsonloads
from logging import getLogger, INFO
from os import environ


getLogger().setLevel(INFO)
__ATHENA = client('athena')
__ATHENA_TYPE_CONVERTERS = {
    'boolean': lambda x: bool(strtobool(x)) if x else None,
    'tinyint': lambda x: int(x) if x else None,
    'smallint': lambda x: int(x) if x else None,
    'integer': lambda x: int(x) if x else None,
    'bigint': lambda x: int(x) if x else None,
    'float': lambda x: float(x) if x else None,
    'real': lambda x: float(x) if x else None,
    'double': lambda x: float(x) if x else None,
    'char': lambda x: x,
    'varchar': lambda x: x,
    'string': lambda x: x,
    'timestamp': lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S.%f').isoformat() if x else None,
    'date': lambda x: datetime.strptime(x, '%Y-%m-%d').date().isoformat() if x else None,
    'time': lambda x: datetime.strptime(x, '%H:%M:%S.%f').time().isoformat() if x else None,
    'varbinary': lambda x: a2b_hex(''.join(x.split(' '))) if x else None,
    'array': lambda x: x,
    'map': lambda x: x,
    'row': lambda x: x,
    'decimal': lambda x: Decimal(x) if x else None,
    'json': lambda x: jsonloads(x) if x else None,
}
__DATABASE = environ.get('DATABASE', 'default')
__MAX_CONCURRENT_QUERIES = int(environ.get('MAX_CONCURRENT_QUERIES', 5))
__WORKGROUP = environ.get('WORKGROUP', 'primary')


def handler(event, context):
    getLogger().debug('Processing event {}'.format(jsondumps(event)))
    result = {}
    if type(event) is dict:
        getLogger().info('Processing Invoke operation')
        execution_request = {
            'QueryString': event['query'].format(**event.get('params', {})),
            'QueryExecutionContext': {
                'Database': event.get('database', __DATABASE)
            },
            'WorkGroup': event.get('workgroup', __WORKGROUP)
        }
        result = __execute_query(execution_request, event.get('singleResult', False))
    else:
        getLogger().debug('Processing BatchInvoke operation with a batch of {}'.format(len(event)))
        with ThreadPoolExecutor(max_workers=__MAX_CONCURRENT_QUERIES) as executor:
            future_query_results = []     
            for batch_event in event:
                future_query_results.append(
                    executor.submit(
                        __execute_query,
                        {
                            'QueryString': batch_event['query'].format(**batch_event.get('params', {})),
                            'QueryExecutionContext': {
                                'Database': batch_event.get('database', __DATABASE)
                            },
                            'WorkGroup': batch_event.get('workgroup', __WORKGROUP)
                        },
                        batch_event.get('singleResult', False)
                    )
                )
            wait(future_query_results)
            result = []
            for future in future_query_results:
                result.append(future.result)        
    return result


def __map_meta_data(meta_data):
    mapped_meta_data = []
    for column in meta_data:
        mapped_meta_data.append((column['Name'], __ATHENA_TYPE_CONVERTERS[column['Type']]))
    return mapped_meta_data


def __map_result(meta_data, data):
    result = {}
    for n in range(len(data)):
        result[meta_data[n][0]] = meta_data[n][1](data[n].get('VarCharValue', None))
    return result


@on_predicate(fibo, lambda x: x not in ('SUCCEEDED', 'FAILED', 'CANCELLED'), max_time=30)
def __poll_query_status(query_execution_id):
    response = __ATHENA.get_query_execution(
        QueryExecutionId=query_execution_id
    )
    return response['QueryExecution']['Status']['State']


def __get_results(query_execution_id, next_token=None):
    params = {
        'QueryExecutionId': query_execution_id,
        'MaxResults': 1000
    }
    if next_token:
        params['NextToken'] = next_token
    response = __ATHENA.get_query_results(**params)
    meta_data = __map_meta_data(response['ResultSet']['ResultSetMetadata']['ColumnInfo'])
    results = []
    rows = response['ResultSet']['Rows']
    for n in range(1, len(rows)):
        results.append(__map_result(meta_data, rows[n]['Data']))
    return results if 'NextToken' not in response else results + __get_results(query_execution_id, response['NextToken'])


def __execute_query(execution_request, single_result):
    query_execution_id = __ATHENA.start_query_execution(**execution_request)['QueryExecutionId']
    query_status = __poll_query_status(query_execution_id)
    if query_status != 'SUCCEEDED':
        if query_status in ('FAILED', 'CANCELLED'):
            raise Exception('Query execution failed with status {}'.format(query_status))
        else:
            raise Exception('Query timed out with status {}'.format(query_status))
    results = __get_results(query_execution_id)
    return results if not single_result else results[0] if len(results) else {}

from athena_type_converter import convert_result_set
from backoff import on_predicate, fibo
from boto3 import client
from concurrent.futures import ThreadPoolExecutor, wait
from json import dumps as jsondumps
from logging import getLogger, INFO
from os import environ


getLogger().setLevel(INFO)
__ATHENA = client('athena')
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
    results = convert_result_set(response['ResultSet'])
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

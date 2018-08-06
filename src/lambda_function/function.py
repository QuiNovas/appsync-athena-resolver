import boto3
import json
import logging.config
import os


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):

    logger.debug('Processing event {}'.format(json.dumps(event)))


    return event

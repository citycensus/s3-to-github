# -*- coding: latin-1 -*-
import sys, os, json

here = os.path.dirname(os.path.realpath(__file__))
env_path = os.path.join(here, "./gh/lib/python2.7/site-packages/")
sys.path.append(env_path)

import json
import agate
import boto3
import agateremote

from github3 import login

token = os.environ.get('GITHUB_TOKEN')
OD_BUCKET = 'open-data-germany-orgs'

class GitHub:
    def __init__(self, org, name):
        self.gh = login(token=token)
        self.repo = self.gh.repository(org, name)

    def commit_file(self, filepath, content, message):
        f = self.repo.contents(filepath)
        if f:
            sha = self.repo.update_file(filepath, message, content, f.sha)
        else:
            self.repo.create_file(filepath, message, content)


def get_url_for_file(filename):
    client = boto3.client('s3')
    return client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': OD_BUCKET,
                'Key': filename,
            }
        )

def commit_stat():
    g = GitHub('open-data-city-census', 'open-data-city-census.github.io')
    client = boto3.client('s3')
    paginator = client.get_paginator('list_objects')
    for result in paginator.paginate(Bucket=OD_BUCKET, Prefix='package_stats_means'):
        for fileObject in result['Contents']:
            if(fileObject['Size'] > 0):
                fileKey = fileObject['Key']
                obj = client.get_object(Bucket=OD_BUCKET, Key=fileKey)
                data = json.load(obj['Body'])
                fileName = fileKey.split('/')
                print(fileName)
                g.commit_file('_data/city_stats/datasets/{}'.format(fileName[1]), json.dumps(data), 'automated update stats data')

def commit_city_stat():
    g = GitHub('open-data-city-census', 'open-data-city-census.github.io')
    client = boto3.client('s3')
    paginator = client.get_paginator('list_objects')
    for result in paginator.paginate(Bucket=OD_BUCKET, Prefix='package_stats'):
        for fileObject in result['Contents']:
            if(fileObject['Size'] > 0):
                fileKey = fileObject['Key']
                obj = client.get_object(Bucket=OD_BUCKET, Key=fileKey)
                data = json.load(obj['Body'])
                fileName = fileKey.split('/')
                g.commit_file('_data/city_stats/datasets/{}'.format(fileName[1]), json.dumps(data), 'automated update stats data')

def commit_stats(event, context):
    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "input": event
    }
    commit_stat()
    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }
    return response

def commit_top_5(event, context):
    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "input": event
    }

    table = agate.Table.from_url(get_url_for_file('open_data_germany_ranks.csv'))
    table = table.order_by('overall_rank')
    table.to_json('/tmp/odd_ranks.json')
    top5 = table.limit(5)
    top5.to_json('/tmp/top5.json')
    g = GitHub('open-data-city-census', 'open-data-city-census.github.io')
    with open('/tmp/top5.json') as json_data:
        data = json.load(json_data)
        g.commit_file('_data/top5.json', json.dumps(data), 'automated update top 5')
    with open('/tmp/odd_ranks.json') as f:
        data = json.load(f)
        g.commit_file('_data/odd_rank.json', json.dumps(data), 'automated update ranking data')


    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response

    # Use this code if you don't use the http event with the LAMBDA-PROXY integration
    """
    return {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "event": event
    }
    """

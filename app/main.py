import os
import boto3
import json
import time
import requests

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)


TOKEN = open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'r').read()
API_HOST = os.environ['KUBERNETES_SERVICE_HOST']
REGION = os.environ['REGION'] # todo: get from kubernetes API

s = requests.Session()
s.headers.update({'Authorization': 'Bearer ' + TOKEN})
ec2 = boto3.client('ec2', region_name=REGION)


def get_url(url):
    return 'https://' + API_HOST + url


def get_nodes():
    nodes = s.get(get_url('/api/v1/nodes'), verify=False)
    return list(map(lambda x: {'name': x['metadata']['name'], 'id': x['spec']['externalID']},
                    json.loads(nodes.content)['items']))


def tag_nodes():
    for node in get_nodes():
        print node['id']
        tags = ec2.describe_instances(
            InstanceIds=[
                node['id']
            ])['Reservations'][0]['Instances'][0]['Tags']
        labels = {}
        for tag in tags:
            key = str(tag['Key']).replace(':', '.').replace('/', '-')
            value = str(tag['Value']).replace(':', '.').replace('/', '-')
            labels.update({key: value})
        body = {
            'kind': 'Node',
            'metadata': {
                'labels': labels
            }
        }
        print labels
        print get_url('/api/v1/nodes/' + node['name'])
        add_labels = s.patch(get_url('/api/v1/nodes/' + node['name']),
                             json=body,
                             headers={'Content-Type': 'application/merge-patch+json'},
                             verify=False)
        print add_labels.status_code
        print '_____________________'

while True:
    time.sleep(60)
    try:
        tag_nodes()
    except Exception as e:
        print e

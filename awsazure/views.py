import boto3, json
from django.shortcuts import render, HttpResponse
from datetime import datetime, timedelta
from awsInv.settings import AWS_SUPPORTED, DATA_UNAVAILABLE, SUPPORTED_OS
# Create your views here.


def index(request):
    return render(request, 'index.html') 


def getDetails(request):
    sk = request.POST.get('sk')
    ak = request.POST.get('ak')
    ACCESS_KEY = ak
    SUCCESS_KEY = sk
    iam_client = boto3.client('iam', aws_access_key_id=ak, aws_secret_access_key=sk)
    ec2_client = boto3.client('ec2', aws_access_key_id=ak, aws_secret_access_key=sk,region_name='us-east-1')
    ce_client = boto3.client('ce', aws_access_key_id=ak, aws_secret_access_key=sk,region_name='us-east-1')
    cloud_client = boto3.client('cloudtrail', aws_access_key_id=ak, aws_secret_access_key=sk,region_name='us-east-1')
    s3_client = boto3.client('s3', aws_access_key_id=ak, aws_secret_access_key=sk,region_name='us-east-1')
    details = getInventoryDetails(ec2_client)
    return HttpResponse(details) 


def getInventoryDetails(ec2):
    list_of_instances = []
    regions = get_regions(ec2)
    total_instances = ec2.describe_instances()
    listObject = []
    for instance in total_instances['Reservations']:
        for instanceDetails in instance['Instances']:
            instanceObject = {}
            instanceObject['InstanceId'] = instanceDetails['InstanceId']
            instanceObject['InstanceType'] = instanceDetails['InstanceType']
            instanceObject['Name'] = instanceDetails['KeyName']
            if 'Platform' not in instanceDetails:
                instanceObject['Platform'] = DATA_UNAVAILABLE
            else:
                instanceObject['Platform'] = instanceDetails['Platform']
            if instanceDetails['InstanceType'] in AWS_SUPPORTED and instanceObject['Platform'] in SUPPORTED_OS:
                instanceObject['ExpressCloudSupported'] = 'Yes'
            else:
                instanceObject['ExpressCloudSupported'] = 'No'
            listObject.append(instanceObject)
    jsonObject  = json.dumps({'data': listObject})    
    return jsonObject    



def getMonthlyInventoryCost(ec2, ce):
    list_of_instances = []
    regions = get_regions(ec2)
    total_instances = ec2.describe_instances()
    
    for instance in total_instances['Reservations']:
        for instanceDetails in instance['Instances']:
            if instanceDetails['InstanceType'] not in list_of_instances:
                list_of_instances.append(instanceDetails['InstanceType'])

    startTime, endTime = getCurrentMonth()
    print(startTime, endTime)
    instancewise={}
    for type_instance in list_of_instances:
        cost_explorer = ce.get_cost_and_usage(
            Granularity='MONTHLY', 
            TimePeriod={'Start':'{}'.format(startTime), 'End':'{}'.format(endTime)}, 
            Metrics=['AmortizedCost', 'UsageQuantity'], 
            Filter={"Dimensions": { "Key": "INSTANCE_TYPE", "Values": [ "{}".format(type_instance)]}})
        costDetails = cost_explorer['ResultsByTime'][0]
        instancewise[type_instance] = costDetails

def getCurrentMonth():
    currentDate = datetime.now()
    firstDate = datetime.today().replace(day=1)
    # todayDate = datetime.today() + timedelta(days=1)
    # todayDate = todayDate.replace(day=todayDate.day)
    # firstDay = None
    # if todayDate.day >= 1:
    #     firstDay = todayDate.replace(day=1)
    return datetime.strftime(firstDate, '%Y-%m-%d'), datetime.strftime(currentDate, '%Y-%m-%d') 


def get_regions(ec2_client):
    """Summary

    Returns:
        TYPE: Description
    """
    region_response = ec2_client.describe_regions()
    regions = [region['RegionName'] for region in region_response['Regions']]
    return regions
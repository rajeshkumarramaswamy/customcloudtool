from django.shortcuts import render, HttpResponse
import boto3, requests, adal, json
from awsInv.settings import AZURE_SUPPORTED, DATA_UNAVAILABLE, SUPPORTED_OS
# Create your views here.


def index(request):
    return render(request, 'aws.html') 

def getDetails(request):
    ak = request.POST.get('as')
    ci = request.POST.get('ci')
    ti = request.POST.get('ti')
    si = request.POST.get('si')
    authentication_endpoint = 'https://login.microsoftonline.com/'
    resource  = 'https://management.core.windows.net/'
    context = adal.AuthenticationContext(authentication_endpoint + ti)
    token_response = context.acquire_token_with_client_credentials(resource, ci, ak)
    access_token = token_response.get('accessToken')
    raw = requests.get("https://management.azure.com/subscriptions/{}/providers/Microsoft.Compute/virtualMachines?api-version=2018-06-01".format(si),
        headers = {"Authorization": 'Bearer ' + access_token}
    ).json()
    listOfDevice = []
 
    for device in raw['value']:
        deviceObject = {}
        deviceObject['InstanceName'] = device['name']
        deviceObject['InstanceType'] = device['type']
        try:
            deviceObject['OSType'] = device['properties']['storageProfile']['osDisk']['osType']
        except Exception as e:
            deviceObject['OSType'] = DATA_UNAVAILABLE
        try:
            deviceObject['SKU'] = device['properties']['storageProfile']['imageReference']['sku']
        except Exception as e:
            deviceObject['SKU'] = DATA_UNAVAILABLE
        if device['type'] in AZURE_SUPPORTED and device['osDisk']['osType'] in SUPPORTED_OS:
            deviceObject['ExpressCloudSupported'] = "Yes"
        else:
            deviceObject['ExpressCloudSupported'] = "No"
        listOfDevice.append(deviceObject)
    finalData = json.dumps({'data': listOfDevice})
    return HttpResponse(finalData) 

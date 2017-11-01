import json
import sys
import boto3
from botocore.vendored import requests


def sendResponse(event, context, responseData, physicalResourceId="NOphysicalResourceId", responseStatus="FAILED"):
    response_body = json.dumps({
        "Status": responseStatus,
        "Reason": "See the details in CloudWatch Log Stream: " + context.log_stream_name,
        "PhysicalResourceId": physicalResourceId or context.log_stream_name,
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
        "Data":responseData
    })
    headers = {"content-type": "", "content-length": str(len(response_body))}
    return requests.put(
        event["ResponseURL"],
        data=response_body,
        headers=headers
    )


def lambda_handler(event, context):
    _, _, _, region, accountId, resource = event["StackId"].split(":")
    stackName = resource.split("/")[1]

    defaultParamName = "cfn-{}-{}".format(stackName, event["LogicalResourceId"])
    paramName = event["ResourceProperties"].get("Name", defaultParamName)

    Arn = "arn:aws:ssm:{}:{}:parameter/{}".format(region, accountId, paramName)
    print("Requested secret: {}".format(Arn))
    ssm = boto3.client("ssm", region_name=region)
    try:
        secret = ssm.get_parameters(
            Names=[paramName],
            WithDecryption=True)
        secretValue = secret["Parameters"][0]["Value"]
        data = {"Arn": Arn, "Name": paramName, "Value": secretValue}
        sendResponse(event, context, data, "ssm:{}".format(paramName),"SUCCESS")
    except:
        sendResponse(event, context, {"Value": "ERROR"})
        print(sys.exc_info())
        sys.exit(1)

from django.conf import settings

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkecs.request.v20140526 import DescribeImagesRequest, DescribeImageSharePermissionRequest, ModifyImageSharePermissionRequest

def get_client():
    client = AcsClient(
        settings.ALIBABA_ACCESS_KEY_ID,
        settings.ALIBABA_ACCESS_KEY_SECRET,
        "ap-northeast-1"
    )
    return client

def DescribeImages():
    client = get_client()
    request = DescribeImagesRequest.DescribeImagesRequest()
    # Initiate an API request and print the response
    response = client.do_action_with_exception(request)
    print(response)

def DescribeImageSharePermission(image_id):
    client = get_client()
    request = DescribeImageSharePermissionRequest.DescribeImageSharePermissionRequest()
    request.set_ImageId(image_id)
    # Initiate an API request and print the response
    response = client.do_action_with_exception(request)
    print(response)

def ModifyImageSharePermission(image_id, add_accounts=[], remove_accounts=[]):
    client = get_client()
    request = ModifyImageSharePermissionRequest.ModifyImageSharePermissionRequest()
    request.set_ImageId(image_id)
    request.set_AddAccount(add_accounts),
    request.set_RemoveAccount(remove_accounts),
    # Initiate an API request and print the response
    response = client.do_action_with_exception(request)
    print(response)


if __name__ == "__main__":
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'isucon.portal.settings')
    # DescribeImageSharePermission("1")
    DescribeImages()

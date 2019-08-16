import json

from django.conf import settings

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkecs.request.v20140526 import DescribeImagesRequest, DescribeImageSharePermissionRequest, ModifyImageSharePermissionRequest


import logging
logger = logging.getLogger("isucon.portal.contest.alibaba")

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
    data = json.loads(response)
    return data

def DescribeImageSharePermission(image_id):
    client = get_client()

    accounts = []
    page = 1
    while True:
        request = DescribeImageSharePermissionRequest.DescribeImageSharePermissionRequest()
        request.set_ImageId(image_id)
        request.set_PageNumber(page)
        request.set_PageSize(50)
        # Initiate an API request and print the response
        response = client.do_action_with_exception(request)
        data = json.loads(response)

        if not data["Accounts"]["Account"]:
            break

        for a in data["Accounts"]["Account"]:
            accounts.append(a["AliyunId"])
        page += 1

    return accounts

def ModifyImageSharePermission(image_id, add_accounts=[], remove_accounts=[]):
    client = get_client()
    request = ModifyImageSharePermissionRequest.ModifyImageSharePermissionRequest()
    request.set_ImageId(image_id)
    request.set_AddAccounts(add_accounts),
    request.set_RemoveAccounts(remove_accounts),
    # Initiate an API request and print the response
    response = client.do_action_with_exception(request)
    data = json.loads(response)
    return data


def SyncImageSharePermission(image_id, accounts=[]):

    accounts = set(accounts)
    current_accounts = set()

    try:
        current_accounts = set(DescribeImageSharePermission(image_id))
    except:
        logger.error("DescribeImageSharePermission %s faild", image_id)
        return


    remove_accounts = list(current_accounts - accounts)
    add_accounts = list(accounts - current_accounts)

    for a in add_accounts:
        try:
            ModifyImageSharePermission(image_id, [a])
        except:
            logger.error("ModifyImageSharePermission %s to %s faild", image_id, a)

    for a in remove_accounts:
        ModifyImageSharePermission(image_id, remove_accounts=[a])


if __name__ == "__main__":
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'isucon.portal.settings')
    # DescribeImages()

    accounts = DescribeImageSharePermission("m-6wefxax67uhdunlue8u6")
    print("Before: ", accounts)

    SyncImageSharePermission("m-6wefxax67uhdunlue8u6", ["5695564992560398"])

    accounts = DescribeImageSharePermission("m-6wefxax67uhdunlue8u6")
    print("After: ", accounts)

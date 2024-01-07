import uuid
import hashlib
from django.conf import settings


def md5(string):
    """ MD5加密,签名算法需要用到 """
    hash_object = hashlib.md5(settings.SECRET_KEY.encode('utf-8'))
    hash_object.update(string.encode('utf-8'))
    return hash_object.hexdigest()


def uid(string):
    """ 基于uid随机生成一个订单号,方便往后查询订单信息 """
    data = "{}-{}".format(str(uuid.uuid4()), string)
    return md5(data)

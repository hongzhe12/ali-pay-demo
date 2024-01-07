"""
https://www.cnblogs.com/xingxia/p/alipay_trade_page.html
"""
# pip install pycryptodome
from datetime import datetime
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from urllib.parse import quote_plus
from base64 import decodebytes, encodebytes
import json


class AliPay(object):
    """
    支付宝支付接口(PC端支付接口)
    """

    def __init__(self, appid, notify_url, app_private_key_path, alipay_public_key_path, return_url, debug=True):
        self.appid = appid
        self.notify_url = notify_url
        self.return_url = return_url

        self.app_private_key_path = app_private_key_path  # 应用私钥
        with open(self.app_private_key_path) as fp:
            self.app_private_key = RSA.importKey(fp.read())

        self.alipay_public_key_path = alipay_public_key_path  # 支付宝公钥
        with open(self.alipay_public_key_path) as fp:
            self.alipay_public_key = RSA.importKey(fp.read())

        if debug is True:
            # self.__gateway = "https://openapi.alipaydev.com/gateway.do"
            self.__gateway = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"  # 沙箱环境网关

    def direct_pay(self, subject, out_trade_no, total_amount):
        """支付相关 将构造的url参数返回便于拼接在支付宝网关地址后面 """
        data = {
            "app_id": self.appid,  # 支付宝分配给开发者的应用ID
            "method": "alipay.trade.page.pay",  # 接口名称
            "charset": "utf-8",  # 请求使用的编码格式
            "sign_type": "RSA2",  # 商户生成签名字符串所使用的签名算法类型
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 发送请求的时间
            "version": "1.0",  # 调用的接口版本
            # 请求参数的集合,值为字符串. json.dumps将字典转化为json格式的字符串.
            "biz_content": json.dumps({
                "subject": subject,  # 订单标题
                "out_trade_no": out_trade_no,  # 商品订单号
                "total_amount": total_amount,  # 订单总金额
                "product_code": "FAST_INSTANT_TRADE_PAY",  # 销售产品码,电脑支付场景下固定为该值
            }, separators=(',', ':'))
        }
        if self.return_url:
            # 支付宝服务器主动通知商户服务器里指定的页面http/https路径
            data["notify_url"] = self.notify_url
            # HTTP/HTTPS开头字符串  支付完成之后,GET请求跳转到这个地址
            data["return_url"] = self.return_url

        return self.sign_data(data)  # 拿着这一堆data数据进行 签名/加密!!

    def transfer(self, out_biz_no, trans_amount, order_title):
        """转账相关"""
        data = {
            "app_id": self.appid,
            "method": "alipay.fund.trans.uni.transfer",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "biz_content": json.dumps({
                "out_biz_no": out_biz_no,
                "trans_amount": trans_amount,
                "product_code": "TRANS_ACCOUNT_NO_PWD",
                "biz_scene": "DIRECT_TRANSFER",
                "order_title": order_title,
                "remark": "备注信息",
                "payee_info": json.dumps({
                    "identity_type": "ALIPAY_LOGON_ID",
                    "identity": "rytdsk3064@sandbox.com",
                    "name": "rytdsk3064"
                }, separators=(',', ':'))
            }, separators=(',', ':'))
        }
        if self.return_url:
            data["notify_url"] = self.notify_url
            data["return_url"] = self.return_url
        return self.sign_data(data)

    def sign_data(self, data):
        """根据官网的加签原理进行签名. https://opendocs.alipay.com/common/02khjm """
        # step1: 获取所有支付宝开放平台的post内容,不包括字节类型参数,如文件、字节流，剔除 sign 字段,剔除值为空的参数;
        data.pop("sign", None)
        # step2: 按照第一个字符的键值 ASCII 码递增排序(字母升序排序), 如果遇到相同字符则按照第二个字符的键值 ASCII 码递增排序,以此类推;
        unsigned_items = self.ordered_data(data)
        # step3: 将排序后的参数与其对应值, 组合成 参数=参数值 的格式, 并且把这些参数用 & 字符连接起来, 此时生成的字符串为待签名字符串.
        # eg: app_id=..&biz_content=..&method=..
        unsigned_string = "&".join("{0}={1}".format(k, v) for k, v in unsigned_items)
        # 开始进行加密,得到sign签名后的结果
        sign = self.sign(unsigned_string.encode("utf-8"))

        # quote_plus对冒号汉字等进行了url 转义.
        quoted_string = "&".join("{0}={1}".format(k, quote_plus(v)) for k, v in unsigned_items)
        # 将sign加密后的结果追加到最后,获得最终的订单信息字符串
        signed_string = quoted_string + "&sign=" + quote_plus(sign)
        return signed_string

    def ordered_data(self, data):
        """它的作用是对字典中的数据进行处理,将其中值为字典类型的键值对转换为JSON格式的字符串,并按照键的字母顺序进行排序"""
        complex_keys = []
        for key, value in data.items():
            if isinstance(value, dict):
                complex_keys.append(key)
        for key in complex_keys:
            data[key] = json.dumps(data[key], separators=(',', ':'))
        # 其实,该处示例中传进来的data数据的键值对中的值是没有字典的,所以直接执行的是下面这一句代码!!
        return sorted([(k, v) for k, v in data.items()])

    def sign(self, unsigned_string):
        """
        利用应用私钥对待签名字符串进行 签名/加密
        :unsigned_string: 待签名data,格式bytes
        :return: 生成的签名字符串
        """
        key = self.app_private_key  # 应用私钥
        signer = PKCS1_v1_5.new(key)
        signature = signer.sign(SHA256.new(unsigned_string))
        # base64 编码,转换为unicode表示并移除回车
        sign = encodebytes(signature).decode("utf8").replace("\n", "")
        return sign  # 返回sign签名后的结果

    def verify(self, data, signature):
        """对签名进行验证"""
        # 先对支付宝回传的数据进行处理,跟上面的第一步第二步第三步一样,只不过上面经过这三步后是加密,这里是解密
        # step1
        if "sign_type" in data:
            data.pop("sign_type")
        # step2
        unsigned_items = self.ordered_data(data)
        # step3
        message = "&".join(u"{}={}".format(k, v) for k, v in unsigned_items)
        # 利用支付宝公钥对处理后的数据进行解密,借此保证数据是支付宝传递过来的!!
        return self._verify(message, signature)

    def _verify(self, raw_content, signature):
        key = self.alipay_public_key  # 支付宝公钥
        signer = PKCS1_v1_5.new(key)
        digest = SHA256.new()
        digest.update(raw_content.encode("utf8"))
        if signer.verify(digest, decodebytes(signature.encode("utf8"))):
            return True
        return False

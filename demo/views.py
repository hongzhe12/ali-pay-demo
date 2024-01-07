import os.path
from urllib.parse import parse_qs

import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render

from utils.alipay import AliPay
from utils.md5AndUid import uid


def index(request):
    """ 点击 支付 or 提现 按钮, 跳转相应界面 """
    return render(request, 'index.html')


def pay(request):
    """ 支付 """
    ali_pay = AliPay(
        appid=settings.ALI_APPID,  # 设置签约的appid
        notify_url=settings.ALI_NOTIFY_URL,  # 异步支付通知url
        return_url=settings.ALI_RETURN_URL,  # 同步支付通知url,在这个页面可以展示给用户看,只有付款成功后才会跳转
        app_private_key_path=settings.ALI_APP_PRI_KEY_PATH,  # 设置应用私钥
        alipay_public_key_path=settings.ALI_PUB_KEY_PATH  # 支付宝的公钥,验证支付宝回传消息使用,不是你自己的公钥
    )

    # 构造跳转的url参数
    query_params = ali_pay.direct_pay(
        subject="这是订单标题",
        out_trade_no=uid('qwe'),  # 支付的订单号
        total_amount=100.00  # 支付金额
    )
    # settings.ALI_GATEWAY 支付宝沙箱网关地址 ; query_params 构造的参数
    pay_url = "{}?{}".format(settings.ALI_GATEWAY, query_params)
    return redirect(pay_url)  # 跳转到支付宝,出现扫码支付的二维码


def pay_notify(request):
    """ 支付成功之后触发的URL """
    ali_pay = AliPay(
        appid=settings.ALI_APPID,  # "2016102400754054"
        notify_url=settings.ALI_NOTIFY_URL,  # 通知URL：POST     支付成功后 - 发送的POST订单验证消息（异步）
        return_url=settings.ALI_RETURN_URL,  # 支付完成之后，跳转到这个地址: GET     支付成功后 - 重定向自己的网站
        app_private_key_path=settings.ALI_APP_PRI_KEY_PATH,
        alipay_public_key_path=settings.ALI_PUB_KEY_PATH
    )

    # return_url
    if request.method == 'GET':
        # 只做跳转,判断是否支付成功了,不做订单的状态更新。
        # 支付宝会将订单号返回获取订单ID,然后根据订单ID做状态更新 + 认证.
        # 支付宝公钥对支付给我返回的数据 request.GET 进行检查,通过则表示这是支付宝返还的接口.
        params = request.GET.dict()
        # print("params:", params)
        sign = params.pop('sign', None)
        status = ali_pay.verify(params, sign)
        if status:
            return HttpResponse('支付完成')
        return HttpResponse('支付失败')
    # notify_url
    else:
        body_str = request.body.decode('utf-8')
        # print("body_str:", body_str)
        post_data = parse_qs(body_str)
        post_dict = {}
        for k, v in post_data.items():
            post_dict[k] = v[0]

        sign = post_dict.pop('sign', None)
        status = ali_pay.verify(post_dict, sign)
        if status:
            out_trade_no = post_dict['out_trade_no']
            # To do: 拿到订单号,去数据库里更新订单状态
            print("支付成功", out_trade_no)
            return HttpResponse('success')
        return HttpResponse('error')


def withdraw(request):
    """ 提取转账 """
    ali_pay = AliPay(
        appid=settings.ALI_APPID,  # "2016102400754054"
        notify_url=settings.ALI_NOTIFY_URL,  # 通知URL：POST     支付成功后 - 发送的POST订单验证消息（异步）
        return_url=settings.ALI_RETURN_URL,  # 支付完成之后，跳转到这个地址: GET     支付成功后 - 重定向自己的网站
        app_private_key_path=settings.ALI_APP_PRI_KEY_PATH,
        alipay_public_key_path=settings.ALI_PUB_KEY_PATH
    )
    query_params = ali_pay.transfer(
        order_title="武沛齐的提现",
        out_biz_no=uid('qwe'),  # 转账的订单号
        trans_amount=2000.00,  # 转账金额
    )
    pay_url = "{}?{}".format(settings.ALI_GATEWAY, query_params)

    # 不会跳转,直接发送请求
    res = requests.get(pay_url)
    data_dict = res.json()
    # 直接告诉我们转账结果
    return JsonResponse(data_dict)

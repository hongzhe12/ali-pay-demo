from urllib.parse import unquote

# 要解码的 URL
url_to_decode = "https%3A%2F%2Fwww.example.com%2F%3Fq%3Dpython"

# 解码 URL
decoded_url = unquote(url_to_decode)



items = {'charset': 'utf-8', 'out_trade_no': '832a4aba2e6dde429fbf65ed3e5bc7c1', 'method': 'alipay.trade.page.pay.return', 'total_amount': '15000.00',  'trade_no': '2024010822001461620501828561', 'auth_app_id': '9021000133666730', 'version': '1.0', 'app_id': '9021000133666730', 'sign_type': 'RSA2', 'seller_id': '2088721026898092', 'timestamp': '2024-01-08 09:57:44'}
for k in items:
    print(items[k])

''
import hashlib
import time
import json
import os
from datetime import datetime
from flask import Flask, request, render_template, redirect, jsonify
import requests

app = Flask(__name__)

# 从环境变量获取配置
EPAY_KEY = os.getenv('EPAY_KEY', '89unJUB8HZ54Hj7x4nUj56HN4nUzUJ8i')
MERCHANTS_ID = os.getenv('MERCHANTS_ID', '1001')

# 模拟商户配置 - 测试系统支持所有支付通道
MERCHANTS = {
    MERCHANTS_ID: {
        'key': EPAY_KEY,
        'active': 1,
        'money': '999999999999.00',  # 无限额度
        'type': 1,  # 1:支付宝,2:微信,3:QQ,4:银行卡
        'account': 'test@mock-epay.com',
        'username': '测试商户',
        'orders': 0,
        'order_today': 0,
        'order_lastday': 0,
        # 支持的支付通道
        'supported_channels': ['alipay', 'wxpay', 'qqpay', 'bank', 'jdpay', 'paypal', 'usdt'],
        'channel_status': {
            'alipay': True,
            'wxpay': True, 
            'qqpay': True,
            'bank': True,
            'jdpay': True,
            'paypal': True,
            'usdt': True
        }
    }
}

# 模拟订单存储
ORDERS = {} 

def verify_sign(params, key):
    """验证签名"""
    # 排除sign和sign_type参数，并过滤空值
    # 同时排除一些常见的客户端额外参数
    excluded_params = ['sign', 'sign_type', 'device', 'clientip', 'param']
    sign_params = {k: v for k, v in params.items() 
                   if k not in excluded_params and v is not None and v != ''}
    
    # 按key排序
    sorted_keys = sorted(sign_params.keys())
    
    # 构建签名字符串
    sign_str = "&".join([f"{k}={sign_params[k]}" for k in sorted_keys])
    sign_str += key
    
    # 计算MD5
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()

@app.route('/submit', methods=['GET', 'POST'])
@app.route('/submit.php', methods=['GET', 'POST'])
def submit():
    """页面跳转支付接口"""
    def get_param(key):
        return request.form.get(key) or request.args.get(key)
    
    # 获取所有参数
    params = {
        'pid': get_param('pid'),
        'type': get_param('type'),
        'out_trade_no': get_param('out_trade_no'),
        'notify_url': get_param('notify_url'),
        'return_url': get_param('return_url'),
        'name': get_param('name'),
        'money': get_param('money'),
        'param': get_param('param'),
        'sign': get_param('sign'),
        'sign_type': get_param('sign_type')
    }
    
    # 验证必填参数
    required_fields = ['pid', 'out_trade_no', 'notify_url', 'return_url', 'name', 'money', 'sign']
    for field in required_fields:
        if not params.get(field):
            return f"缺少必填参数: {field}", 400
    
    # 验证商户
    merchant = MERCHANTS.get(params['pid'])
    if not merchant:
        return "商户不存在", 400
    
    if merchant['active'] != 1:
        return "商户已被封禁", 400
    
    # 验证签名
    expected_sign = verify_sign(params, merchant['key'])
    received_sign = params['sign'].lower()
    
    print(f"签名验证调试信息:")
    print(f"  接收到的签名: {received_sign}")
    print(f"  期望的签名: {expected_sign}")
    print(f"  商户密钥: {merchant['key']}")
    
    # 打印签名字符串用于调试
    excluded_params = ['sign', 'sign_type', 'device', 'clientip', 'param']
    sign_params = {k: v for k, v in params.items() 
                   if k not in excluded_params and v is not None and v != ''}
    sorted_keys = sorted(sign_params.keys())
    sign_str = "&".join([f"{k}={sign_params[k]}" for k in sorted_keys])
    sign_str += merchant['key']
    print(f"  服务器签名字符串: {sign_str}")
    
    if received_sign != expected_sign:
        return f"签名验证失败 - 接收: {received_sign[:8]}..., 期望: {expected_sign[:8]}...", 400
    
    print(f"Received payment request: {request.method}")
    print(f"Data: {params}")
    
    # 如果没有指定支付方式，显示收银台（这里简化处理）
    if not params.get('type'):
        params['type'] = 'alipay'  # 默认支付宝
    
    return render_template('submit.html', data=params)

@app.route('/mapi.php', methods=['POST'])
def mapi():
    """API接口支付"""
    # 获取POST参数
    params = {
        'pid': request.form.get('pid'),
        'type': request.form.get('type'),
        'out_trade_no': request.form.get('out_trade_no'),
        'notify_url': request.form.get('notify_url'),
        'return_url': request.form.get('return_url'),
        'name': request.form.get('name'),
        'money': request.form.get('money'),
        'clientip': request.form.get('clientip'),
        'device': request.form.get('device', 'pc'),
        'param': request.form.get('param'),
        'sign': request.form.get('sign'),
        'sign_type': request.form.get('sign_type', 'MD5')
    }
    
    # 验证必填参数
    required_fields = ['pid', 'type', 'out_trade_no', 'notify_url', 'name', 'money', 'clientip', 'sign']
    for field in required_fields:
        if not params.get(field):
            return jsonify({'code': 0, 'msg': f'缺少必填参数: {field}'})
    
    # 验证商户
    merchant = MERCHANTS.get(params['pid'])
    if not merchant:
        return jsonify({'code': 0, 'msg': '商户不存在'})
    
    if merchant['active'] != 1:
        return jsonify({'code': 0, 'msg': '商户已被封禁'})
    
    # 验证支付通道
    payment_type = params['type']
    if payment_type not in merchant['supported_channels']:
        return jsonify({'code': 0, 'msg': f'不支持的支付方式: {payment_type}'})
    
    if not merchant['channel_status'].get(payment_type, False):
        return jsonify({'code': 0, 'msg': f'支付通道已关闭: {payment_type}'})
    
    # 验证签名
    expected_sign = verify_sign(params, merchant['key'])
    received_sign = params['sign'].lower()
    
    print(f"API接口签名验证调试信息:")
    print(f"  接收到的签名: {received_sign}")
    print(f"  期望的签名: {expected_sign}")
    print(f"  商户密钥: {merchant['key']}")
    
    # 打印签名字符串用于调试
    excluded_params = ['sign', 'sign_type', 'device', 'clientip', 'param']
    sign_params = {k: v for k, v in params.items() 
                   if k not in excluded_params and v is not None and v != ''}
    sorted_keys = sorted(sign_params.keys())
    sign_str = "&".join([f"{k}={sign_params[k]}" for k in sorted_keys])
    sign_str += merchant['key']
    print(f"  服务器签名字符串: {sign_str}")
    
    if received_sign != expected_sign:
        return jsonify({'code': 0, 'msg': f'签名验证失败 - 接收: {received_sign[:8]}..., 期望: {expected_sign[:8]}...'})
    
    # 生成易支付订单号
    trade_no = f"{int(time.time())}{params['out_trade_no'][-6:]}"
    
    # 保存订单信息
    order_data = {
        'trade_no': trade_no,
        'out_trade_no': params['out_trade_no'],
        'api_trade_no': '',
        'type': params['type'],
        'pid': int(params['pid']),
        'addtime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'endtime': '',
        'name': params['name'],
        'money': params['money'],
        'status': 0,  # 0未支付，1已支付
        'param': params.get('param', ''),
        'buyer': ''
    }
    ORDERS[trade_no] = order_data
    
    # 根据支付方式返回不同的支付链接
    response_data = {
        'code': 1,
        'msg': '',
        'trade_no': trade_no
    }
    
    # 模拟不同支付方式的返回
    payment_type = params['type']
    device = params['device']
    
    if payment_type == 'alipay':
        if device == 'mobile':
            response_data['payurl'] = f'https://mock-epay.com/pay/alipay/{trade_no}/'
        else:
            response_data['qrcode'] = f'https://qr.alipay.com/bax08888?t={trade_no}'
    elif payment_type == 'wxpay':
        if device == 'wechat':
            response_data['urlscheme'] = f'weixin://dl/business/?ticket={trade_no}'
        else:
            response_data['qrcode'] = f'weixin://wxpay/bizpayurl?pr={trade_no}'
    elif payment_type == 'qqpay':
        response_data['qrcode'] = f'https://qpay.qq.com/qr/{trade_no}'
    elif payment_type == 'bank':
        response_data['payurl'] = f'https://mock-epay.com/pay/bank/{trade_no}/'
    elif payment_type == 'jdpay':
        response_data['qrcode'] = f'https://jdpay.com/qr/{trade_no}'
    elif payment_type == 'paypal':
        response_data['payurl'] = f'https://www.paypal.com/checkoutnow?token={trade_no}'
    elif payment_type == 'usdt':
        response_data['qrcode'] = f'bitcoin:{trade_no}?amount=1'
    else:
        # 其他支付方式默认返回支付链接
        response_data['payurl'] = f'https://mock-epay.com/pay/{payment_type}/{trade_no}/'
    
    return jsonify(response_data)

@app.route('/pay', methods=['POST'])
def pay():
    """模拟用户点击确认支付"""
    pid = request.form.get('pid')
    payment_type = request.form.get('type')
    out_trade_no = request.form.get('out_trade_no')
    money = request.form.get('money')
    name = request.form.get('name')
    notify_url = request.form.get('notify_url')
    return_url = request.form.get('return_url')
    param = request.form.get('param', '')

    # 生成易支付订单号
    trade_no = f"{int(time.time())}{out_trade_no[-6:]}"
    
    # 保存/更新订单状态
    order_data = {
        'trade_no': trade_no,
        'out_trade_no': out_trade_no,
        'api_trade_no': f'third_{trade_no}',
        'type': payment_type,
        'pid': int(pid),
        'addtime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'endtime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'name': name,
        'money': money,
        'status': 1,  # 支付成功
        'param': param,
        'buyer': 'mock_user@example.com'
    }
    ORDERS[trade_no] = order_data

    # 构造回调参数
    callback_params = {
        'pid': pid,
        'trade_no': trade_no,
        'out_trade_no': out_trade_no,
        'type': payment_type,
        'name': name,
        'money': money,
        'trade_status': 'TRADE_SUCCESS',
        'param': param,
        'sign_type': 'MD5'
    }

    # 生成签名
    merchant = MERCHANTS.get(pid)
    sign = verify_sign(callback_params, merchant['key'])
    callback_params['sign'] = sign

    # 发送异步通知
    try:
        response = requests.get(notify_url, params=callback_params, timeout=10)
        print(f"Callback sent for {out_trade_no}: {response.status_code}")
        print(f"Callback URL: {response.url}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send callback: {e}")

    # 重定向到同步返回页面
    return redirect(return_url)

@app.route('/api.php', methods=['GET'])
def api():
    """API接口集合"""
    act = request.args.get('act')
    pid = request.args.get('pid')
    key = request.args.get('key')
    
    # 验证商户
    merchant = MERCHANTS.get(pid)
    if not merchant or merchant['key'] != key:
        return jsonify({'code': 0, 'msg': '商户验证失败'})
    
    if act == 'query':
        # 查询商户信息
        return jsonify({
            'code': 1,
            'pid': int(pid),
            'key': merchant['key'],
            'active': merchant['active'],
            'money': merchant['money'],
            'type': merchant['type'],
            'account': merchant['account'],
            'username': merchant['username'],
            'orders': merchant['orders'],
            'order_today': merchant['order_today'],
            'order_lastday': merchant['order_lastday']
        })
    
    elif act == 'settle':
        # 查询结算记录
        return jsonify({
            'code': 1,
            'msg': '查询结算记录成功！',
            'data': []  # 模拟空结算记录
        })
    
    elif act == 'order':
        # 查询单个订单
        trade_no = request.args.get('trade_no')
        out_trade_no = request.args.get('out_trade_no')
        
        if not trade_no and not out_trade_no:
            return jsonify({'code': 0, 'msg': '缺少订单号参数'})
        
        # 查找订单
        order = None
        if trade_no:
            order = ORDERS.get(trade_no)
        else:
            for t_no, order_data in ORDERS.items():
                if order_data['out_trade_no'] == out_trade_no:
                    order = order_data
                    break
        
        if not order:
            return jsonify({'code': 0, 'msg': '订单不存在'})
        
        return jsonify({
            'code': 1,
            'msg': '查询订单成功！',
            **order
        })
    
    elif act == 'orders':
        # 批量查询订单
        limit = int(request.args.get('limit', 20))
        page = int(request.args.get('page', 1))
        
        # 模拟分页
        all_orders = list(ORDERS.values())
        start = (page - 1) * limit
        end = start + limit
        orders = all_orders[start:end]
        
        return jsonify({
            'code': 1,
            'msg': '查询订单列表成功！',
            'data': orders
        })
    
    elif act == 'refund':
        # 订单退款（需要POST方法）
        if request.method != 'POST':
            return jsonify({'code': 0, 'msg': '退款接口需要POST请求'})
        
        trade_no = request.form.get('trade_no')
        out_trade_no = request.form.get('out_trade_no')
        money = request.form.get('money')
        
        if not money:
            return jsonify({'code': 0, 'msg': '缺少退款金额'})
        
        if not trade_no and not out_trade_no:
            return jsonify({'code': 0, 'msg': '缺少订单号'})
        
        # 模拟退款成功
        return jsonify({'code': 1, 'msg': '退款成功'})
    
    return jsonify({'code': 0, 'msg': '未知操作类型'})

@app.route('/api.php', methods=['POST'])
def api_post():
    """处理POST类型的API请求"""
    return api()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6002, debug=True)

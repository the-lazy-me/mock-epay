#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
易支付Mock系统测试脚本
"""
import requests
import hashlib
import json

BASE_URL = "http://localhost:6002"
TEST_PID = "1001"
TEST_KEY = "89unJUB8HZ54Hj7x4nUj56HN4nUzUJ8i"

def generate_sign(params, key):
    """生成MD5签名"""
    # 排除sign和sign_type，过滤空值
    sign_params = {k: v for k, v in params.items() 
                   if k not in ['sign', 'sign_type'] and v is not None and v != ''}
    
    # 按key排序
    sorted_keys = sorted(sign_params.keys())
    sign_str = "&".join([f"{k}={sign_params[k]}" for k in sorted_keys])
    sign_str += key
    
    # MD5加密，结果小写
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()

def test_submit_payment():
    """测试页面跳转支付接口"""
    print("=== 测试页面跳转支付接口 ===")
    
    params = {
        'pid': TEST_PID,
        'type': 'alipay',
        'out_trade_no': 'TEST20240827001',
        'notify_url': 'http://localhost:8080/notify',
        'return_url': 'http://localhost:8080/return',
        'name': '测试商品',
        'money': '1.00',
        'param': 'test_param',
        'sign_type': 'MD5'
    }
    
    # 生成签名
    params['sign'] = generate_sign(params, TEST_KEY)
    
    # 发送POST请求
    response = requests.post(f"{BASE_URL}/submit.php", data=params)
    print(f"状态码: {response.status_code}")
    print(f"响应长度: {len(response.text)} 字符")
    print("✓ 页面跳转支付接口测试通过\n")

def test_mapi_payment():
    """测试API接口支付"""
    print("=== 测试API接口支付 ===")
    
    params = {
        'pid': TEST_PID,
        'type': 'wxpay',
        'out_trade_no': 'TEST20240827002',
        'notify_url': 'http://localhost:8080/notify',
        'return_url': 'http://localhost:8080/return',
        'name': '测试商品2',
        'money': '2.00',
        'clientip': '192.168.1.100',
        'device': 'pc',
        'param': 'test_param2',
        'sign_type': 'MD5'
    }
    
    # 生成签名
    params['sign'] = generate_sign(params, TEST_KEY)
    
    # 发送POST请求
    response = requests.post(f"{BASE_URL}/mapi.php", data=params)
    result = response.json()
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result['code'] == 1:
        print("✓ API接口支付测试通过\n")
    else:
        print("✗ API接口支付测试失败\n")

def test_all_payment_channels():
    """测试所有支付通道"""
    print("=== 测试所有支付通道 ===")
    
    channels = ['alipay', 'wxpay', 'qqpay', 'bank', 'jdpay', 'paypal', 'usdt']
    
    for i, channel in enumerate(channels):
        params = {
            'pid': TEST_PID,
            'type': channel,
            'out_trade_no': f'TEST2024082700{i+10}',
            'notify_url': 'http://localhost:8080/notify',
            'return_url': 'http://localhost:8080/return',
            'name': f'测试{channel}支付',
            'money': f'{i+1}.00',
            'clientip': '192.168.1.100',
            'device': 'pc',
            'sign_type': 'MD5'
        }
        
        # 生成签名
        params['sign'] = generate_sign(params, TEST_KEY)
        
        # 发送POST请求
        response = requests.post(f"{BASE_URL}/mapi.php", data=params)
        result = response.json()
        
        print(f"{channel}: {result['code']} - {result.get('msg', 'success')}")
        if result['code'] == 1:
            if 'qrcode' in result:
                print(f"  二维码: {result['qrcode'][:50]}...")
            elif 'payurl' in result:
                print(f"  支付链接: {result['payurl'][:50]}...")
            elif 'urlscheme' in result:
                print(f"  小程序链接: {result['urlscheme'][:50]}...")
    
    print("✓ 所有支付通道测试完成\n")

def test_query_merchant():
    """测试查询商户信息"""
    print("=== 测试查询商户信息 ===")
    
    url = f"{BASE_URL}/api.php?act=query&pid={TEST_PID}&key={TEST_KEY}"
    response = requests.get(url)
    result = response.json()
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result['code'] == 1:
        print("✓ 查询商户信息测试通过\n")
    else:
        print("✗ 查询商户信息测试失败\n")

def test_query_orders():
    """测试批量查询订单"""
    print("=== 测试批量查询订单 ===")
    
    url = f"{BASE_URL}/api.php?act=orders&pid={TEST_PID}&key={TEST_KEY}&limit=10&page=1"
    response = requests.get(url)
    result = response.json()
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result['code'] == 1:
        print("✓ 批量查询订单测试通过\n")
    else:
        print("✗ 批量查询订单测试失败\n")

def test_invalid_sign():
    """测试无效签名"""
    print("=== 测试签名验证 ===")
    
    params = {
        'pid': TEST_PID,
        'type': 'alipay',
        'out_trade_no': 'TEST20240827003',
        'notify_url': 'http://localhost:8080/notify',
        'return_url': 'http://localhost:8080/return',
        'name': '测试商品3',
        'money': '3.00',
        'clientip': '192.168.1.100',
        'sign': 'invalid_sign',
        'sign_type': 'MD5'
    }
    
    response = requests.post(f"{BASE_URL}/mapi.php", data=params)
    result = response.json()
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result['code'] == 0 and '签名' in result['msg']:
        print("✓ 签名验证测试通过\n")
    else:
        print("✗ 签名验证测试失败\n")

if __name__ == "__main__":
    print("开始测试易支付Mock系统...\n")
    
    try:
        test_submit_payment()
        test_mapi_payment()
        test_all_payment_channels()
        test_query_merchant()
        test_query_orders()
        test_invalid_sign()
        
        print("=== 测试完成 ===")
        print("所有主要功能已测试完毕！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到Mock系统，请确保系统正在运行在 http://localhost:6002")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")

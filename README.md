# Mock Epay 模拟易支付服务

这是一个用于测试 qh-api 充值返现功能的模拟易支付服务。

## 安装和运行

1. 进入项目目录：
```bash
cd /Volumes/Disk-1tb/qh-api/mock-epay
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 运行服务：
```bash
python app.py
```

服务将在 `http://localhost:5001` 启动。

## 配置 qh-api

在 qh-api 的后台管理中添加一个新的支付渠道：

1. 进入后台管理 → 支付设置
2. 添加新的支付渠道，配置如下：
   - **渠道名称**: Mock Epay (测试用)
   - **支付网关**: 易支付
   - **支付地址**: `http://localhost:5001/submit`
   - **商户ID**: `test_merchant`
   - **密钥**: `your_secret_key`

## 使用方法

1. 启动 mock-epay 服务
2. 在 qh-api 前端选择 "Mock Epay" 支付方式进行充值
3. 系统会跳转到模拟支付页面
4. 点击 "Confirm Payment" 按钮完成模拟支付
5. 系统会自动回调 qh-api，触发充值和返现逻辑

## 工作流程

1. **支付请求**: qh-api → `GET /submit` → 显示支付确认页面
2. **确认支付**: 用户点击确认 → `POST /pay` → 向 qh-api 发送回调通知
3. **回调处理**: qh-api 接收回调 → 处理充值 → 触发返现逻辑

## 注意事项

- 确保 `app.py` 中的 `EPAY_KEY` 与 qh-api 后台配置的密钥一致
- 服务默认运行在 5001 端口，避免与 qh-api 冲突
- 仅用于测试环境，请勿在生产环境使用

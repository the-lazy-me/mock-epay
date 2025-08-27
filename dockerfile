# 使用Python 3.11作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 设置默认环境变量
ENV EPAY_KEY=89unJUB8HZ54Hj7x4nUj56HN4nUzUJ8i
ENV MERCHANTS_ID=1001

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app.py .
COPY templates/ ./templates/

# 创建日志目录
RUN mkdir -p /app/logs

# 暴露端口
EXPOSE 6002

# 设置健康检查（使用环境变量）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f "http://localhost:6002/api.php?act=query&pid=${MERCHANTS_ID}&key=${EPAY_KEY}" || exit 1

# 启动应用
CMD ["python", "app.py"]

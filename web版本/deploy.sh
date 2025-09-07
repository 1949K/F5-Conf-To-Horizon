#!/bin/bash

# F5配置翻译工具Docker部署脚本
# 适用于Ubuntu系统

echo "🚀 开始部署F5配置翻译工具到Docker..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，正在安装Docker..."
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    sudo usermod -aG docker $USER
    echo "✅ Docker安装完成，请重新登录以应用用户组权限"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，正在安装..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose安装完成"
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p data logs
chmod 755 data logs

# 停止并删除现有容器
echo "🛑 停止现有容器..."
docker-compose down

# 构建并启动服务
echo "🔨 构建Docker镜像..."
docker-compose build --no-cache

echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 检查健康状态
echo "🏥 检查健康状态..."
docker-compose exec f5-translator-app curl -f http://localhost:5000/health || echo "⚠️  健康检查失败，服务可能还在启动中"

echo "✅ 部署完成！"
echo "🌐 访问地址: http://localhost:5000"
echo "📋 查看日志: docker-compose logs -f f5-translator"
echo "🛑 停止服务: docker-compose down" 
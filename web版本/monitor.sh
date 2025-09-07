#!/bin/bash

# F5配置翻译工具系统监控脚本

echo "🔍 F5配置翻译工具系统监控"
echo "================================"

# 检查Docker服务状态
echo "🐳 Docker服务状态:"
if systemctl is-active --quiet docker; then
    echo "✅ Docker服务运行中"
else
    echo "❌ Docker服务未运行"
    echo "尝试启动Docker服务..."
    sudo systemctl start docker
fi

# 检查容器状态
echo ""
echo "📦 容器状态:"
if command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    echo "❌ docker-compose未安装"
fi

# 检查系统资源
echo ""
echo "💻 系统资源使用情况:"
echo "CPU使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')%"
echo "内存使用: $(free -h | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
echo "磁盘使用: $(df -h / | awk 'NR==2{print $5}')"

# 检查端口占用
echo ""
echo "🌐 端口占用情况:"
if command -v netstat &> /dev/null; then
    netstat -tlnp | grep :5000 || echo "端口5000未被占用"
else
    echo "netstat未安装，无法检查端口"
fi

# 检查应用健康状态
echo ""
echo "🏥 应用健康状态:"
if curl -f http://localhost:5000/health &> /dev/null; then
    echo "✅ 应用运行正常"
    curl -s http://localhost:5000/health | python3 -m json.tool 2>/dev/null || echo "健康检查响应异常"
else
    echo "❌ 应用无响应"
fi

# 检查日志文件
echo ""
echo "📋 日志文件状态:"
if [ -d "logs" ]; then
    echo "日志目录存在"
    if [ -f "logs/app.log" ]; then
        echo "应用日志文件大小: $(du -h logs/app.log | cut -f1)"
        echo "最近错误日志:"
        tail -n 5 logs/app.log | grep -i error || echo "无错误日志"
    else
        echo "应用日志文件不存在"
    fi
else
    echo "日志目录不存在"
fi

# 检查数据目录
echo ""
echo "💾 数据目录状态:"
if [ -d "data" ]; then
    echo "数据目录存在"
    echo "数据目录大小: $(du -sh data | cut -f1)"
    echo "用户目录数量: $(find data -maxdepth 1 -type d | wc -l)"
else
    echo "数据目录不存在"
fi

# 检查Docker资源使用
echo ""
echo "🐳 Docker资源使用:"
if command -v docker &> /dev/null; then
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
else
    echo "Docker未安装"
fi

echo ""
echo "================================"
echo "监控完成！" 
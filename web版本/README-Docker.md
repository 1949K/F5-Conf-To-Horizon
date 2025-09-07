# F5配置翻译工具 - Docker部署指南

## 🐳 概述

本指南将帮助您在Ubuntu系统中使用Docker部署F5配置翻译工具。

## 📋 系统要求

- Ubuntu 18.04+ 或 CentOS 7+
- Docker 20.10+
- Docker Compose 2.0+
- 至少2GB可用内存
- 至少10GB可用磁盘空间

## 🚀 快速部署

### 方法1：使用自动部署脚本（推荐）

```bash
# 1. 克隆项目到Ubuntu服务器
git clone <your-repo-url>
cd f5-config-translator

# 2. 给部署脚本执行权限
chmod +x deploy.sh

# 3. 运行部署脚本
./deploy.sh
```

### 方法2：手动部署

```bash
# 1. 构建Docker镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps
```

## 🔧 配置说明

### 环境变量

创建 `.env` 文件（基于 `.env.example`）：

```bash
# Flask配置
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# 文件上传配置
MAX_CONTENT_LENGTH=100MB
MAX_FILES_COUNT=10
```

### 端口配置

默认端口：5000

如需修改端口，编辑 `docker-compose.yml`：

```yaml
ports:
  - "8080:5000"  # 将外部端口改为8080
```

### 数据持久化

应用数据会自动持久化到以下目录：

- `./data/` - 用户上传和处理的数据文件
- `./logs/` - 应用日志文件

## 📊 服务管理

### 查看服务状态

```bash
# 查看容器状态
docker-compose ps

# 查看服务日志
docker-compose logs -f f5-translator

# 查看特定服务的日志
docker-compose logs -f f5-translator --tail=100
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart f5-translator
```

### 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

### 更新服务

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

## 🏥 健康检查

应用提供健康检查端点：

```bash
# 检查服务健康状态
curl http://localhost:5000/health

# 预期响应
{"status": "healthy", "timestamp": "2024-01-01T12:00:00"}
```

## 🔍 故障排除

### 常见问题

#### 1. 端口被占用

```bash
# 查看端口占用
sudo netstat -tlnp | grep :5000

# 杀死占用进程
sudo kill -9 <PID>
```

#### 2. 权限问题

```bash
# 修复目录权限
sudo chown -R $USER:$USER data logs
chmod -R 755 data logs
```

#### 3. 内存不足

```bash
# 查看系统资源
docker stats

# 限制容器内存
# 在docker-compose.yml中添加：
# mem_limit: 1g
```

#### 4. 磁盘空间不足

```bash
# 清理Docker资源
docker system prune -a

# 清理日志文件
docker-compose logs --tail=1000 > recent_logs.txt
docker-compose logs --tail=0
```

### 日志分析

```bash
# 查看应用日志
tail -f logs/app.log

# 查看Docker日志
docker-compose logs -f f5-translator

# 搜索错误日志
docker-compose logs f5-translator | grep ERROR
```

## 🔒 安全配置

### 生产环境建议

1. **修改默认端口**
2. **设置强密码**
3. **启用HTTPS**
4. **配置防火墙**
5. **定期更新镜像**

### 防火墙配置

```bash
# Ubuntu UFW
sudo ufw allow 5000/tcp
sudo ufw enable

# CentOS firewalld
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

## 📈 性能优化

### 资源限制

在 `docker-compose.yml` 中添加：

```yaml
services:
  f5-translator:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### 多实例部署

```yaml
services:
  f5-translator:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
```

## 🔄 备份和恢复

### 数据备份

```bash
# 备份数据目录
tar -czf backup_$(date +%Y%m%d).tar.gz data/

# 备份数据库（如果有）
docker-compose exec f5-translator pg_dump -U username dbname > backup.sql
```

### 数据恢复

```bash
# 恢复数据目录
tar -xzf backup_20240101.tar.gz

# 恢复数据库
docker-compose exec -T f5-translator psql -U username dbname < backup.sql
```

## 📞 技术支持

如果遇到问题：

1. 查看应用日志：`docker-compose logs f5-translator`
2. 检查系统资源：`docker stats`
3. 验证网络连接：`curl http://localhost:5000/health`
4. 查看容器状态：`docker-compose ps`

## 📝 更新日志

- **v1.0.0** - 初始Docker支持
- **v1.1.0** - 添加健康检查
- **v1.2.0** - 优化资源管理
- **v2.0.0** - 生产环境就绪

---

**注意**: 在生产环境中部署前，请确保：
- 修改默认密码
- 配置适当的资源限制
- 设置监控和告警
- 制定备份策略 
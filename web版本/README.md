# F5配置翻译工具

一个统一的F5配置翻译工具，支持Web应用和桌面应用，使用相同的处理机制确保功能一致性。

## 🚀 特性

- **统一处理机制**: Web和桌面应用使用相同的核心处理逻辑
- **用户管理**: 完整的用户注册、登录、会话管理
- **文件处理**: 支持UCS和Show文件格式的处理
- **实时状态**: 文件处理状态实时跟踪
- **多格式输出**: 支持Excel、TXT、LOG等多种输出格式

## 📁 项目结构

```
F5配置翻译工具/
├── core/                          # 核心功能模块
│   ├── processors/                # 统一处理器
│   │   ├── unified_processor.py   # 统一处理管理器
│   │   ├── f5_ucs_processor.py    # UCS处理器
│   │   └── base_processor.py      # 基础处理器
│   ├── function/                  # 功能模块
│   │   ├── ucs/                   # UCS处理功能
│   │   └── show/                  # Show处理功能
│   ├── config.py                  # 配置管理
│   ├── user_manager.py            # 用户管理
│   └── auth.py                    # 认证模块
├── web/                           # Web应用
│   ├── app.py                     # Flask应用主文件
│   └── templates/                 # HTML模板
├── desktop/                       # 桌面应用
│   └── advanced_app.py            # Tkinter桌面应用
├── data/                          # 数据存储
├── requirements/                  # 依赖包配置
├── run_unified_desktop.py         # 桌面应用启动脚本
└── 统一处理机制说明.md            # 统一处理机制说明
```

## 🛠️ 安装

### 环境要求
- Python 3.8+
- 推荐使用Python11环境

### 安装依赖

```bash
# 安装基础依赖
pip install -r requirements/base.txt

# 安装Web应用依赖
pip install -r requirements/web.txt

# 安装桌面应用依赖
pip install -r requirements/desktop.txt
```

## 🚀 使用方法

### 桌面应用

```bash
# 使用Python11环境启动
/opt/anaconda3/envs/Python11/bin/python run_unified_desktop.py

# 或使用普通Python环境
python run_unified_desktop.py
```

### Web应用

```bash
# 启动Web应用
python web/app.py
```

访问 http://localhost:5000 使用Web界面。

## 📋 功能说明

### UCS文件处理流程
1. **上传UCS文件** → 用户上传.ucs文件
2. **UCS转TAR** → 将.ucs文件转换为.tar文件
3. **解压TAR文件** → 解压.tar文件到处理目录
4. **提取配置文件** → 从解压目录提取conf和base文件
5. **转换为Excel/TXT** → 使用统一模块处理conf和base文件

### Show文件处理流程
1. **上传Show文件** → 用户上传.txt或.conf文件
2. **TXT转LOG** → 将.txt文件重命名为.log文件
3. **处理配置文件** → 使用统一模块处理.conf文件

## 🔧 统一处理机制

### 核心优势
- **维护便利性**: 只需更新统一处理管理器即可同时更新Web和桌面应用
- **功能一致性**: Web和桌面应用使用完全相同的处理逻辑
- **用户体验**: 简化的操作流程，用户只需点击一个按钮
- **扩展性**: 新增功能只需在统一处理管理器中添加

### 技术实现
```python
# 统一处理管理器
class UnifiedProcessor:
    def process_ucs_files(self, files, upload_dir):
        # 完整的UCS处理流程
        pass
    
    def process_show_files(self, files, upload_dir):
        # 完整的Show处理流程
        pass
```

## 📊 处理状态

应用提供完整的文件处理状态跟踪：
- 文件上传状态
- 处理进度
- 处理结果
- 错误信息

## 🔐 用户管理

- **用户注册**: 支持新用户注册
- **用户登录**: 安全的用户认证
- **会话管理**: 用户状态保持
- **数据隔离**: 每个用户的数据独立存储

## 📁 文件管理

- **文件上传**: 支持UCS、Show等多种文件格式
- **文件下载**: 批量下载处理结果
- **文件删除**: 安全的文件删除操作
- **文件列表**: 实时文件状态显示

## 🛡️ 安全特性

- **用户认证**: 密码加密存储
- **文件安全**: 文件类型验证和大小限制
- **系统安全**: 输入验证和错误处理

## 🔄 后续更新

当需要更新处理逻辑时：
1. 修改 `core/processors/unified_processor.py`
2. 测试Web和桌面应用
3. 无需分别修改两个应用的处理逻辑

## 📝 开发说明

### 技术架构
- **Web框架**: Flask
- **桌面框架**: Tkinter
- **后端逻辑**: Python核心模块
- **数据处理**: Pandas, OpenPyXL
- **文件处理**: 自定义处理器

### 扩展开发
- 新增功能模块
- 自定义处理器
- 界面定制
- 插件系统

## 📞 支持

如果在使用过程中遇到问题，请：
1. 查看系统日志获取错误信息
2. 检查配置文件设置
3. 确认依赖包版本
4. 参考 `统一处理机制说明.md`

---

**版本**: 2.0.0  
**更新日期**: 2024年  
**技术支持**: 开发团队 
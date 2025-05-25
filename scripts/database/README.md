# Qdrant数据库工具

这个目录包含与Qdrant向量数据库相关的各种工具和脚本。

## 新的诊断系统

我们现在有了一个集中式的Qdrant诊断系统，它整合了多个测试脚本的功能：

- 核心模块: `knowledge/diagnostics.py` - 提供诊断API和实用函数
- 命令行工具: `run_diagnostics.py` - 提供命令行界面进行诊断

### 使用方法

快速诊断:

```bash
python scripts/database/run_diagnostics.py --quick
```

完整诊断:

```bash
python scripts/database/run_diagnostics.py
```

详细模式:

```bash
python scripts/database/run_diagnostics.py --verbose
```

## 配置工具

### 更新配置

更新Qdrant配置:

```bash
python scripts/database/update_qdrant_config.py --host YOUR_HOST --port YOUR_PORT --api-key YOUR_API_KEY
```

更新API密钥:

```bash
python scripts/database/update_api_key.py
```

重置API密钥:

```bash
python scripts/database/reset_qdrant_api.py
```

### 查看配置

打印当前配置:

```bash
python scripts/database/print_config.py
```

## 连接测试工具

测试客户端连接:

```bash
python scripts/database/test_client.py
```

使用curl测试连接:

```bash
./scripts/database/test_curl.sh
```

直接测试REST API:

```bash
python scripts/database/direct_test.py
```

## 数据库管理工具

初始化数据库:

```bash
python scripts/database/init_db.py
```

创建索引:

```bash
python scripts/database/create_qdrant_indexes.py
```

重置云端Qdrant:

```bash
python scripts/database/reset_cloud_qdrant.py
```

## 测试知识库

测试知识库功能:

```bash
python scripts/database/test_knowledge.py
```

## 调试和故障排除

使用诊断工具解决常见问题:

1. 检查环境变量配置是否正确
2. 确认API密钥是否有效
3. 验证端口设置 (6333或443)
4. 测试连接并获取详细错误信息

## 开发帮助

如果您需要在代码中集成诊断功能，可以导入核心模块:

```python
from knowledge.diagnostics import test_connection, run_diagnostics

# 快速测试连接
if test_connection():
    print("连接成功")

# 运行完整诊断
results = run_diagnostics()
``` 
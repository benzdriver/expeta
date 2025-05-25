# 系统工具

此目录包含主要的系统运行和管理工具。

## 工具说明

### run_expeta.py
Expeta系统的主运行脚本，支持全局推理、局部推理和完整流水线。

用法:
```bash
# 运行完整推理流水线
python tools/system/run_expeta.py full -i data/input -o data/output/architecture_full

# 仅运行全局架构推理
python tools/system/run_expeta.py global -i data/input -o data/output/architecture

# 为特定实体运行局部推理
python tools/system/run_expeta.py local -e "UserService" -i data/input -o data/output/entity
```

### rollback_manager.py
系统更改回滚管理工具，用于在系统出现问题时恢复到之前的状态。

用法:
```bash
python tools/system/rollback_manager.py
``` 
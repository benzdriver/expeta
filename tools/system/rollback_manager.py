from common import print_log
import json
import shutil
from pathlib import Path
import datetime
import os

class RollbackManager:
    """管理系统状态的备份和回滚功能"""
    
    def __init__(self, backup_dir="data/backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.current_checkpoint = None
    
    def create_checkpoint(self, tag=None):
        """创建当前状态的检查点，可以用于回滚"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_name = f"{timestamp}_{tag}" if tag else timestamp
        checkpoint_path = self.backup_dir / checkpoint_name
        
        # 确保目录存在
        checkpoint_path.mkdir(parents=True, exist_ok=True)
        
        # 备份关键文件和目录
        self._backup_file("data/validator_report.json", checkpoint_path)
        self._backup_file("data/output/dependency_graph.json", checkpoint_path)
        self._backup_file("data/output/summary_index.json", checkpoint_path)
        
        # 备份模块定义（只备份元数据，不备份完整模块内容以节省空间）
        modules_dir = Path("data/output/modules")
        if modules_dir.exists():
            modules_backup = checkpoint_path / "modules_meta"
            modules_backup.mkdir(parents=True, exist_ok=True)
            
            # 仅备份full_summary.json文件
            for module_dir in modules_dir.glob("*/"):
                if module_dir.is_dir():
                    summary_file = module_dir / "full_summary.json"
                    if summary_file.exists():
                        # 创建目标目录
                        target_dir = modules_backup / module_dir.name
                        target_dir.mkdir(parents=True, exist_ok=True)
                        # 复制summary文件
                        shutil.copy2(summary_file, target_dir / "full_summary.json")
        
        self.current_checkpoint = checkpoint_name
        print_log(f"创建检查点: {checkpoint_name}", level="info")
        return checkpoint_name
    
    def _backup_file(self, file_path, checkpoint_dir):
        """备份单个文件"""
        source = Path(file_path)
        if source.exists():
            dest = checkpoint_dir / source.name
            shutil.copy2(source, dest)
    
    def list_checkpoints(self):
        """列出所有可用的检查点"""
        return sorted([d.name for d in self.backup_dir.iterdir() if d.is_dir()])
    
    def rollback_to_checkpoint(self, checkpoint=None):
        """回滚到指定的检查点，如果未指定则回滚到最近的检查点"""
        if checkpoint is None:
            if self.current_checkpoint:
                checkpoint = self.current_checkpoint
            else:
                checkpoints = self.list_checkpoints()
                if not checkpoints:
                    print_log(f"没有可用的检查点", level="error")
                    return False
                checkpoint = checkpoints[-1]  # 获取最新的检查点
        
        checkpoint_path = self.backup_dir / checkpoint
        if not checkpoint_path.exists():
            print_log(f"检查点 {checkpoint} 不存在", level="error")
            return False
        
        # 恢复关键文件
        self._restore_file(checkpoint_path / "validator_report.json", "data/validator_report.json")
        self._restore_file(checkpoint_path / "dependency_graph.json", "data/output/dependency_graph.json")
        self._restore_file(checkpoint_path / "summary_index.json", "data/output/summary_index.json")
        
        # 恢复模块元数据
        modules_backup = checkpoint_path / "modules_meta"
        if modules_backup.exists():
            modules_dir = Path("data/output/modules")
            
            # 只恢复存在于备份中的模块的full_summary.json
            for module_dir in modules_backup.glob("*/"):
                if module_dir.is_dir():
                    summary_file = module_dir / "full_summary.json"
                    if summary_file.exists():
                        # 创建目标目录
                        target_dir = modules_dir / module_dir.name
                        target_dir.mkdir(parents=True, exist_ok=True)
                        # 复制summary文件
                        shutil.copy2(summary_file, target_dir / "full_summary.json")
        
        print_log(f"已回滚到检查点: {checkpoint}", level="info")
        return True
    
    def _restore_file(self, source_path, dest_path):
        """恢复单个文件"""
        source = Path(source_path)
        dest = Path(dest_path)
        
        if source.exists():
            # 确保目标目录存在
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
    
    def cleanup_old_checkpoints(self, keep=5):
        """清理旧的检查点，只保留最近的几个"""
        checkpoints = self.list_checkpoints()
        if len(checkpoints) <= keep:
            return
        
        # 保留最新的几个检查点
        to_delete = checkpoints[:-keep]
        
        for old_checkpoint in to_delete:
            checkpoint_path = self.backup_dir / old_checkpoint
            shutil.rmtree(checkpoint_path)
            print_log(f"🗑️ 删除旧检查点: {old_checkpoint}")

# 使用示例
def initialize_rollback_manager():
    """初始化并返回回滚管理器"""
    return RollbackManager() 
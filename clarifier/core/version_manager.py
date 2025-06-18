"""
需求版本管理器的完整实现
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
import json
import copy
from dataclasses import dataclass
from enum import Enum

from common.logger import Logger

logger = Logger.get_instance('clarifier')

class ChangeType(Enum):
    """变更类型"""
    FEATURE_ADDITION = "feature_addition"
    FEATURE_MODIFICATION = "feature_modification"
    FEATURE_REMOVAL = "feature_removal"
    BUSINESS_RULE_CHANGE = "business_rule_change"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    SECURITY_ENHANCEMENT = "security_enhancement"
    BUG_FIX = "bug_fix"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    BLIND_SPOT_CLARIFICATION = "blind_spot_clarification"

@dataclass
class Version:
    """版本数据结构"""
    id: str
    version_number: str
    created_at: str
    created_by: str
    prd_content: str
    json_summary: Dict[str, Any]
    metadata: Dict[str, Any]
    change_summary: str
    parent_version_id: Optional[str]
    checksum: str

@dataclass
class Change:
    """变更记录"""
    id: str
    timestamp: str
    type: ChangeType
    description: str
    from_version: str
    to_version: str
    affected_components: List[str]
    details: Dict[str, Any]

class RequirementVersion:
    """需求版本管理器"""
    
    def __init__(self):
        self.versions: Dict[str, Version] = {}
        self.changes: List[Change] = []
        self.current_version_id: Optional[str] = None
        self.version_tree: Dict[str, List[str]] = {}  # 版本树，记录分支
        
    def create_initial_version(
        self,
        prd_content: str,
        json_summary: Dict[str, Any],
        created_by: str = "system"
    ) -> str:
        """创建初始版本"""
        version_id = self._generate_version_id()
        version_number = "1.0.0"
        
        version = Version(
            id=version_id,
            version_number=version_number,
            created_at=datetime.now().isoformat(),
            created_by=created_by,
            prd_content=prd_content,
            json_summary=json_summary,
            metadata={
                "is_initial": True,
                "branch": "main"
            },
            change_summary="Initial version",
            parent_version_id=None,
            checksum=self._calculate_checksum(prd_content, json_summary)
        )
        
        self.versions[version_id] = version
        self.current_version_id = version_id
        self.version_tree[version_id] = []
        
        logger.log(f"✅ 创建初始版本: {version_id} (v{version_number})", level="info")
        
        return version_id
    
    def create_new_version(
        self,
        prd_content: str,
        json_summary: Dict[str, Any],
        change_type: ChangeType,
        change_description: str,
        created_by: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建新版本"""
        if not self.current_version_id:
            raise ValueError("没有当前版本，请先创建初始版本")
        
        parent_version = self.versions[self.current_version_id]
        version_id = self._generate_version_id()
        version_number = self._increment_version_number(
            parent_version.version_number,
            change_type
        )
        
        # 检测具体的变更
        change_details = self._analyze_changes(
            parent_version.json_summary,
            json_summary
        )
        
        version = Version(
            id=version_id,
            version_number=version_number,
            created_at=datetime.now().isoformat(),
            created_by=created_by,
            prd_content=prd_content,
            json_summary=json_summary,
            metadata=metadata or {},
            change_summary=change_description,
            parent_version_id=self.current_version_id,
            checksum=self._calculate_checksum(prd_content, json_summary)
        )
        
        self.versions[version_id] = version
        
        # 更新版本树
        if self.current_version_id in self.version_tree:
            self.version_tree[self.current_version_id].append(version_id)
        self.version_tree[version_id] = []
        
        # 记录变更
        change = Change(
            id=self._generate_change_id(),
            timestamp=datetime.now().isoformat(),
            type=change_type,
            description=change_description,
            from_version=self.current_version_id,
            to_version=version_id,
            affected_components=change_details["affected_components"],
            details=change_details
        )
        self.changes.append(change)
        
        # 更新当前版本
        self.current_version_id = version_id
        
        logger.log(
            f"✅ 创建新版本: {version_id} (v{version_number}) - {change_description}",
            level="info"
        )
        
        return version_id
    
    def _generate_version_id(self) -> str:
        """生成版本ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = hashlib.md5(timestamp.encode()).hexdigest()[:6]
        return f"V_{timestamp}_{random_suffix}"
    
    def _generate_change_id(self) -> str:
        """生成变更ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = hashlib.md5(timestamp.encode()).hexdigest()[:4]
        return f"C_{timestamp}_{random_suffix}"
    
    def _calculate_checksum(self, prd_content: str, json_summary: Dict[str, Any]) -> str:
        """计算内容校验和"""
        content = f"{prd_content}{json.dumps(json_summary, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _increment_version_number(self, current_version: str, change_type: ChangeType) -> str:
        """根据变更类型增加版本号"""
        major, minor, patch = map(int, current_version.split('.'))
        
        # 根据变更类型决定版本号增加策略
        if change_type in [ChangeType.FEATURE_ADDITION, ChangeType.FEATURE_REMOVAL]:
            minor += 1
            patch = 0
        elif change_type in [ChangeType.FEATURE_MODIFICATION, ChangeType.BUSINESS_RULE_CHANGE]:
            patch += 1
        elif change_type == ChangeType.REFACTORING and patch == 0:
            minor += 1
        else:
            patch += 1
        
        return f"{major}.{minor}.{patch}"
    
    def _analyze_changes(
        self,
        old_summary: Dict[str, Any],
        new_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析两个版本之间的具体变更"""
        changes = {
            "added": {},
            "modified": {},
            "removed": {},
            "affected_components": []
        }
        
        # 深度比较
        self._deep_compare(old_summary, new_summary, changes, "")
        
        # 提取受影响的组件
        affected = set()
        for change_list in [changes["added"], changes["modified"], changes["removed"]]:
            for path in change_list.keys():
                # 提取顶层组件名
                component = path.split('.')[0] if '.' in path else path
                affected.add(component)
        
        changes["affected_components"] = list(affected)
        
        return changes
    
    def _deep_compare(
        self,
        old_obj: Any,
        new_obj: Any,
        changes: Dict[str, Any],
        path: str
    ):
        """深度比较两个对象"""
        if type(old_obj) != type(new_obj):
            changes["modified"][path] = {
                "old": old_obj,
                "new": new_obj,
                "type": "type_change"
            }
            return
        
        if isinstance(old_obj, dict):
            old_keys = set(old_obj.keys())
            new_keys = set(new_obj.keys())
            
            # 添加的键
            for key in new_keys - old_keys:
                new_path = f"{path}.{key}" if path else key
                changes["added"][new_path] = new_obj[key]
            
            # 删除的键
            for key in old_keys - new_keys:
                old_path = f"{path}.{key}" if path else key
                changes["removed"][old_path] = old_obj[key]
            
            # 共同的键
            for key in old_keys & new_keys:
                new_path = f"{path}.{key}" if path else key
                self._deep_compare(old_obj[key], new_obj[key], changes, new_path)
        
        elif isinstance(old_obj, list):
            if len(old_obj) != len(new_obj):
                changes["modified"][path] = {
                    "old_length": len(old_obj),
                    "new_length": len(new_obj),
                    "type": "list_length_change"
                }
            
            # 比较列表元素
            for i in range(min(len(old_obj), len(new_obj))):
                self._deep_compare(old_obj[i], new_obj[i], changes, f"{path}[{i}]")
        
        elif old_obj != new_obj:
            changes["modified"][path] = {
                "old": old_obj,
                "new": new_obj,
                "type": "value_change"
            }
    
    def get_version(self, version_id: str) -> Optional[Version]:
        """获取特定版本"""
        return self.versions.get(version_id)
    
    def get_current_version(self) -> Optional[Version]:
        """获取当前版本"""
        if self.current_version_id:
            return self.versions.get(self.current_version_id)
        return None
    
    def get_version_history(self, limit: int = 10) -> List[Version]:
        """获取版本历史"""
        # 按创建时间倒序排序
        sorted_versions = sorted(
            self.versions.values(),
            key=lambda v: v.created_at,
            reverse=True
        )
        return sorted_versions[:limit]
    
    def get_change_history(
        self,
        from_version: Optional[str] = None,
        to_version: Optional[str] = None,
        change_type: Optional[ChangeType] = None
    ) -> List[Change]:
        """获取变更历史"""
        filtered_changes = self.changes
        
        if from_version:
            filtered_changes = [
                c for c in filtered_changes
                if c.from_version == from_version or c.to_version == from_version
            ]
        
        if to_version:
            filtered_changes = [
                c for c in filtered_changes
                if c.to_version == to_version
            ]
        
        if change_type:
            filtered_changes = [
                c for c in filtered_changes
                if c.type == change_type
            ]
        
        return sorted(filtered_changes, key=lambda c: c.timestamp, reverse=True)
    
    def get_version_diff(
        self,
        version1_id: str,
        version2_id: str
    ) -> Dict[str, Any]:
        """获取两个版本之间的差异"""
        v1 = self.versions.get(version1_id)
        v2 = self.versions.get(version2_id)
        
        if not v1 or not v2:
            raise ValueError("指定的版本不存在")
        
        # 分析差异
        diff_analysis = self._analyze_changes(v1.json_summary, v2.json_summary)
        
        # 生成差异报告
        diff_report = {
            "version1": {
                "id": v1.id,
                "number": v1.version_number,
                "created_at": v1.created_at
            },
            "version2": {
                "id": v2.id,
                "number": v2.version_number,
                "created_at": v2.created_at
            },
            "changes": diff_analysis,
            "summary": self._generate_diff_summary(diff_analysis)
        }
        
        return diff_report
    
    def _generate_diff_summary(self, diff_analysis: Dict[str, Any]) -> str:
        """生成差异摘要"""
        added_count = len(diff_analysis["added"])
        modified_count = len(diff_analysis["modified"])
        removed_count = len(diff_analysis["removed"])
        
        summary_parts = []
        
        if added_count > 0:
            summary_parts.append(f"新增 {added_count} 项")
        if modified_count > 0:
            summary_parts.append(f"修改 {modified_count} 项")
        if removed_count > 0:
            summary_parts.append(f"删除 {removed_count} 项")
        
        if not summary_parts:
            return "无变化"
        
        return "，".join(summary_parts)
    
    def checkout_version(self, version_id: str) -> bool:
        """切换到指定版本"""
        if version_id not in self.versions:
            logger.log(f"❌ 版本 {version_id} 不存在", level="error")
            return False
        
        self.current_version_id = version_id
        logger.log(f"✅ 切换到版本: {version_id}", level="info")
        return True
    
    def create_branch(self, branch_name: str) -> str:
        """从当前版本创建分支"""
        if not self.current_version_id:
            raise ValueError("没有当前版本")
        
        current_version = self.versions[self.current_version_id]
        
        # 创建分支版本
        branch_version_id = self.create_new_version(
            prd_content=current_version.prd_content,
            json_summary=current_version.json_summary,
            change_type=ChangeType.REFACTORING,
            change_description=f"Create branch: {branch_name}",
            metadata={
                "branch": branch_name,
                "branched_from": self.current_version_id
            }
        )
        
        return branch_version_id
    
    def merge_versions(
        self,
        source_version_id: str,
        target_version_id: str,
        merge_strategy: str = "theirs"  # "theirs", "ours", "manual"
    ) -> str:
        """合并两个版本"""
        source = self.versions.get(source_version_id)
        target = self.versions.get(target_version_id)
        
        if not source or not target:
            raise ValueError("源版本或目标版本不存在")
        
        # 执行合并
        if merge_strategy == "theirs":
            # 使用源版本的内容
            merged_summary = source.json_summary
            merged_prd = source.prd_content
        elif merge_strategy == "ours":
            # 使用目标版本的内容
            merged_summary = target.json_summary
            merged_prd = target.prd_content
        else:
            # 手动合并（这里简化处理）
            merged_summary = self._manual_merge(
                source.json_summary,
                target.json_summary
            )
            merged_prd = f"{target.prd_content}\n\n--- Merged from {source_version_id} ---\n\n{source.prd_content}"
        
        # 创建合并后的版本
        merge_version_id = self.create_new_version(
            prd_content=merged_prd,
            json_summary=merged_summary,
            change_type=ChangeType.REFACTORING,
            change_description=f"Merge {source_version_id} into {target_version_id}",
            metadata={
                "merge": True,
                "source_version": source_version_id,
                "target_version": target_version_id,
                "merge_strategy": merge_strategy
            }
        )
        
        return merge_version_id
    
    def _manual_merge(
        self,
        source_summary: Dict[str, Any],
        target_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """手动合并两个摘要（简化实现）"""
        # 这里应该实现更复杂的合并逻辑
        # 现在只是简单地合并顶层键
        merged = copy.deepcopy(target_summary)
        
        for key, value in source_summary.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(value, list) and isinstance(merged[key], list):
                # 合并列表
                merged[key].extend(v for v in value if v not in merged[key])
        
        return merged
    
    def rollback_to_version(self, version_id: str) -> str:
        """回滚到指定版本"""
        if version_id not in self.versions:
            raise ValueError(f"版本 {version_id} 不存在")
        
        rollback_version = self.versions[version_id]
        
        # 创建回滚版本
        rollback_id = self.create_new_version(
            prd_content=rollback_version.prd_content,
            json_summary=rollback_version.json_summary,
            change_type=ChangeType.REFACTORING,
            change_description=f"Rollback to version {version_id}",
            metadata={
                "rollback": True,
                "rollback_to": version_id
            }
        )
        
        logger.log(f"✅ 回滚到版本: {version_id}", level="info")
        
        return rollback_id
    
    def export_version_history(self, format: str = "json") -> str:
        """导出版本历史"""
        history_data = {
            "versions": [
                {
                    "id": v.id,
                    "number": v.version_number,
                    "created_at": v.created_at,
                    "created_by": v.created_by,
                    "change_summary": v.change_summary,
                    "parent_version": v.parent_version_id
                }
                for v in self.versions.values()
            ],
            "changes": [
                {
                    "id": c.id,
                    "timestamp": c.timestamp,
                    "type": c.type.value,
                    "description": c.description,
                    "from_version": c.from_version,
                    "to_version": c.to_version,
                    "affected_components": c.affected_components
                }
                for c in self.changes
            ],
            "current_version": self.current_version_id
        }
        
        if format == "json":
            return json.dumps(history_data, ensure_ascii=False, indent=2)
        elif format == "markdown":
            return self._export_history_as_markdown(history_data)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def _export_history_as_markdown(self, history_data: Dict[str, Any]) -> str:
        """导出为Markdown格式的历史"""
        md_lines = ["# 版本历史", ""]
        
        # 当前版本
        md_lines.extend([
            f"**当前版本**: {history_data['current_version']}",
            ""
        ])
        
        # 版本列表
        md_lines.extend(["## 版本列表", ""])
        
        for version in history_data["versions"]:
            md_lines.extend([
                f"### {version['number']} ({version['id']})",
                f"- 创建时间: {version['created_at']}",
                f"- 创建者: {version['created_by']}",
                f"- 变更说明: {version['change_summary']}",
                f"- 父版本: {version['parent_version'] or 'None'}",
                ""
            ])
        
        # 变更历史
        md_lines.extend(["## 变更历史", ""])
        
        for change in history_data["changes"]:
            md_lines.extend([
                f"### {change['timestamp']} - {change['type']}",
                f"- 描述: {change['description']}",
                f"- 从版本: {change['from_version']}",
                f"- 到版本: {change['to_version']}",
                f"- 影响组件: {', '.join(change['affected_components'])}",
                ""
            ])
        
        return "\n".join(md_lines)
    
    def get_version_tree_visualization(self) -> str:
        """获取版本树的可视化表示"""
        if not self.versions:
            return "No versions available"
        
        # 找到根版本
        root_versions = [
            v for v in self.versions.values()
            if v.parent_version_id is None
        ]
        
        tree_lines = ["Version Tree:", ""]
        
        for root in root_versions:
            self._add_tree_node(root.id, tree_lines, "", True)
        
        return "\n".join(tree_lines)
    
    def _add_tree_node(
        self,
        version_id: str,
        tree_lines: List[str],
        prefix: str,
        is_last: bool
    ):
        """递归添加树节点"""
        version = self.versions[version_id]
        
        # 添加连接符
        connector = "└── " if is_last else "├── "
        tree_lines.append(
            f"{prefix}{connector}{version.version_number} ({version.id[:8]}...) - {version.change_summary[:30]}..."
        )
        
        # 准备子节点的前缀
        extension = "    " if is_last else "│   "
        
        # 添加子版本
        children = self.version_tree.get(version_id, [])
        for i, child_id in enumerate(children):
            is_last_child = i == len(children) - 1
            self._add_tree_node(
                child_id,
                tree_lines,
                prefix + extension,
                is_last_child
            )

class VersionManager:
    """版本管理器门面"""
    
    def __init__(self):
        self.requirement_version = RequirementVersion()
        
    def initialize_with_prd(
        self,
        prd_content: str,
        json_summary: Dict[str, Any]
    ) -> str:
        """使用PRD初始化版本管理"""
        return self.requirement_version.create_initial_version(
            prd_content=prd_content,
            json_summary=json_summary
        )
    
    def save_blind_spot_clarification(
        self,
        updated_prd: str,
        updated_summary: Dict[str, Any],
        blind_spot_id: str,
        clarification: str
    ) -> str:
        """保存盲点澄清后的版本"""
        return self.requirement_version.create_new_version(
            prd_content=updated_prd,
            json_summary=updated_summary,
            change_type=ChangeType.BLIND_SPOT_CLARIFICATION,
            change_description=f"Clarified blind spot: {blind_spot_id}",
            metadata={
                "blind_spot_id": blind_spot_id,
                "clarification": clarification
            }
        )
    
    def save_requirement_change(
        self,
        updated_prd: str,
        updated_summary: Dict[str, Any],
        change_request: Dict[str, Any]
    ) -> str:
        """保存需求变更"""
        # 推断变更类型
        change_type = self._infer_change_type(change_request)
        
        return self.requirement_version.create_new_version(
            prd_content=updated_prd,
            json_summary=updated_summary,
            change_type=change_type,
            change_description=change_request.get("description", "Requirement change"),
            metadata={
                "change_request": change_request
            }
        )
    
    def _infer_change_type(self, change_request: Dict[str, Any]) -> ChangeType:
        """推断变更类型"""
        request_type = change_request.get("type", "").lower()
        
        type_mapping = {
            "add": ChangeType.FEATURE_ADDITION,
            "modify": ChangeType.FEATURE_MODIFICATION,
            "remove": ChangeType.FEATURE_REMOVAL,
            "optimize": ChangeType.PERFORMANCE_OPTIMIZATION,
            "fix": ChangeType.BUG_FIX,
            "security": ChangeType.SECURITY_ENHANCEMENT
        }
        
        for keyword, change_type in type_mapping.items():
            if keyword in request_type:
                return change_type
        
        return ChangeType.FEATURE_MODIFICATION
    
    def get_clarification_history(self) -> List[Dict[str, Any]]:
        """获取澄清历史"""
        clarification_changes = self.requirement_version.get_change_history(
            change_type=ChangeType.BLIND_SPOT_CLARIFICATION
        )
        
        history = []
        for change in clarification_changes:
            version = self.requirement_version.get_version(change.to_version)
            if version and "blind_spot_id" in version.metadata:
                history.append({
                    "timestamp": change.timestamp,
                    "blind_spot_id": version.metadata["blind_spot_id"],
                    "clarification": version.metadata.get("clarification", ""),
                    "version_id": change.to_version
                })
        
        return history
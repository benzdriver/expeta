"""
Qdrant诊断模块
提供Qdrant连接测试、配置验证和故障排除功能
整合了多个测试脚本的功能，使用集中式日志系统
"""

import os
import sys
import json
import traceback
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

try:
    import requests
    from qdrant_client import QdrantClient
    from qdrant_client.http.exceptions import UnexpectedResponse, ApiException
except ImportError as e:
    raise ImportError(f"缺少必要依赖: {str(e)}。请安装: pip install qdrant-client requests")

# 导入配置
from knowledge.config import (
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_API_KEY,
    QDRANT_PATH,
    ALL_COLLECTIONS,
    logger
)

class QdrantDiagnostics:
    """Qdrant诊断工具类，提供各种测试和调试功能"""
    
    def __init__(self, use_logger=True):
        """
        初始化诊断工具
        
        Args:
            use_logger: 是否使用日志系统，否则使用print
        """
        self.use_logger = use_logger
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, str]:
        """加载当前配置"""
        return {
            "host": QDRANT_HOST,
            "port": QDRANT_PORT,
            "api_key": QDRANT_API_KEY,
            "path": QDRANT_PATH
        }
    
    def log(self, message: str, level: str = "info", role: str = "diagnostics"):
        """统一日志输出"""
        if self.use_logger:
            # 使用集中式日志系统
            if level == "error":
                logger.log(message, level="error", role=role)
            elif level == "warning":
                logger.log(message, level="warning", role=role)
            elif level == "debug":
                logger.log(message, level="debug", role=role)
            else:
                logger.log(message, role=role)
        else:
            # 使用print作为备选
            prefix = ""
            if level == "error":
                prefix = "❌ "
            elif level == "warning":
                prefix = "⚠️ "
            elif level == "debug":
                prefix = "🔍 "
            print(f"{prefix}{message}")
    
    def print_config(self) -> None:
        """打印当前配置信息"""
        self.log("Qdrant配置信息:", role="config")
        
        self.log(f"主要配置:", role="config")
        self.log(f"  QDRANT_HOST: {self.config['host']}", role="config")
        self.log(f"  QDRANT_PORT: {self.config['port']}", role="config")
        
        if self.config['api_key']:
            masked_key = f"{self.config['api_key'][:8]}...{self.config['api_key'][-5:]}"
            self.log(f"  QDRANT_API_KEY: {masked_key}", role="config")
        else:
            self.log(f"  QDRANT_API_KEY: 未设置", level="warning", role="config")
        
        self.log(f"  QDRANT_PATH: {self.config['path']}", role="config")
        
        # 配置类型
        if self.config['host'] and self.config['api_key']:
            self.log("  ☁️ 使用Qdrant云服务", role="config")
            self.log(f"  连接URL: https://{self.config['host']}:{self.config['port']}", role="config")
        else:
            self.log("  💻 使用本地存储", role="config")
            self.log(f"  存储路径: {self.config['path']}", role="config")
    
    def test_system_info(self) -> Dict[str, str]:
        """收集系统信息"""
        self.log("获取系统信息...", role="diagnostics")
        
        info = {
            "os": f"{platform.system()} {platform.release()}",
            "python": platform.python_version(),
            "qdrant_client": "未安装",
            "requests": "未安装"
        }
        
        try:
            import qdrant_client
            info["qdrant_client"] = getattr(qdrant_client, "__version__", "未知版本")
        except (ImportError, AttributeError):
            pass
        
        try:
            import requests
            info["requests"] = getattr(requests, "__version__", "未知版本")
        except (ImportError, AttributeError):
            pass
        
        # 打印收集的信息
        self.log(f"操作系统: {info['os']}", role="system")
        self.log(f"Python版本: {info['python']}", role="system")
        self.log(f"Qdrant客户端版本: {info['qdrant_client']}", role="system")
        self.log(f"Requests版本: {info['requests']}", role="system")
        
        return info
    
    def test_direct_connection(self) -> bool:
        """使用requests直接测试REST API连接"""
        self.log("使用HTTP直接测试连接...", role="diagnostics")
        
        if not self.config['host'] or not self.config['api_key']:
            self.log("未配置主机或API密钥，无法测试连接", level="warning", role="diagnostics")
            return False
        
        url = f"https://{self.config['host']}:{self.config['port']}/collections"
        headers = {"api-key": self.config['api_key']}
        
        self.log(f"请求URL: {url}", level="debug", role="diagnostics")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            self.log(f"响应状态码: {response.status_code}", level="debug", role="diagnostics")
            
            if response.status_code == 200:
                data = response.json()
                collections = data.get("result", {}).get("collections", [])
                collection_names = [c.get('name') for c in collections]
                
                self.log("✅ 直接HTTP连接测试成功", role="diagnostics")
                self.log(f"发现 {len(collection_names)} 个集合: {', '.join(collection_names)}", role="diagnostics")
                return True
            else:
                self.log(f"❌ 连接失败 (HTTP {response.status_code}): {response.text}", level="error", role="diagnostics")
                
                if response.status_code == 403:
                    self.log("可能原因: API密钥无效或权限不足", level="warning", role="diagnostics")
                elif response.status_code == 401:
                    self.log("可能原因: 未提供有效的认证信息", level="warning", role="diagnostics")
                
                return False
        except Exception as e:
            self.log(f"❌ 连接错误: {str(e)}", level="error", role="diagnostics")
            self.log(f"详细错误: {traceback.format_exc()}", level="debug", role="diagnostics")
            return False
    
    def test_client_connection(self) -> Tuple[bool, Optional[QdrantClient]]:
        """使用qdrant_client测试连接"""
        self.log("使用QdrantClient测试连接...", role="diagnostics")
        
        if not self.config['host'] and not self.config['api_key']:
            self.log("使用本地存储模式", role="diagnostics")
            try:
                Path(self.config['path']).parent.mkdir(parents=True, exist_ok=True)
                client = QdrantClient(path=self.config['path'])
                self.log("✅ 本地存储连接成功", role="diagnostics")
                return True, client
            except Exception as e:
                self.log(f"❌ 本地存储连接失败: {str(e)}", level="error", role="diagnostics")
                self.log(f"详细错误: {traceback.format_exc()}", level="debug", role="diagnostics")
                return False, None
        
        if not self.config['host'] or not self.config['api_key']:
            self.log("缺少云服务配置 (主机或API密钥)", level="warning", role="diagnostics")
            return False, None
        
        try:
            # 创建客户端
            self.log(f"连接到 {self.config['host']}:{self.config['port']}...", level="debug", role="diagnostics")
            
            client = QdrantClient(
                host=self.config['host'],
                port=int(self.config['port']),
                api_key=self.config['api_key'],
                timeout=30,
                prefer_grpc=False,
                check_compatibility=False
            )
            
            # 测试获取集合
            collections = client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            self.log("✅ QdrantClient连接成功", role="diagnostics")
            self.log(f"发现 {len(collection_names)} 个集合: {', '.join(collection_names)}", role="diagnostics")
            
            return True, client
        except UnexpectedResponse as e:
            self.log(f"❌ Qdrant API响应异常: {str(e)}", level="error", role="diagnostics")
            
            # 尝试解析详细错误信息
            error_details = "未知错误"
            http_status = "未知"
            try:
                if hasattr(e, 'response'):
                    http_status = str(e.response.status_code)
                    error_data = json.loads(e.response.text)
                    error_details = error_data.get('error', 'API详细错误未知')
            except:
                pass
            
            self.log(f"HTTP状态码: {http_status}", level="debug", role="diagnostics")
            self.log(f"错误详情: {error_details}", level="debug", role="diagnostics")
            
            # 针对常见错误提供建议
            if "403" in http_status:
                self.log("可能原因: API密钥无效或权限不足", level="warning", role="diagnostics")
                self.log("建议: 在Qdrant控制台重新生成API密钥", level="warning", role="diagnostics")
            elif "401" in http_status:
                self.log("可能原因: 认证失败", level="warning", role="diagnostics")
                self.log("建议: 检查API密钥格式是否正确", level="warning", role="diagnostics")
            
            return False, None
        except Exception as e:
            self.log(f"❌ 连接异常: {str(e)}", level="error", role="diagnostics")
            self.log(f"详细错误: {traceback.format_exc()}", level="debug", role="diagnostics")
            return False, None
    
    def test_curl(self) -> bool:
        """使用curl命令测试连接"""
        self.log("使用curl命令测试连接...", role="diagnostics")
        
        if not self.config['host'] or not self.config['api_key']:
            self.log("未配置主机或API密钥，无法使用curl测试", level="warning", role="diagnostics")
            return False
        
        # 构建curl命令
        curl_cmd = [
            "curl", "-s",
            f"https://{self.config['host']}:{self.config['port']}/collections",
            "-H", f"api-key: {self.config['api_key']}"
        ]
        
        try:
            # 执行curl命令
            self.log(f"执行命令: curl -s https://{self.config['host']}:{self.config['port']}/collections -H 'api-key: ***'", 
                   level="debug", role="diagnostics")
            result = subprocess.run(curl_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log(f"❌ curl命令执行失败 (返回码: {result.returncode})", level="error", role="diagnostics")
                if result.stderr:
                    self.log(f"错误输出: {result.stderr}", level="debug", role="diagnostics")
                return False
            
            # 解析响应
            try:
                response_data = json.loads(result.stdout)
                
                # 检查是否有错误
                if "error" in response_data:
                    self.log(f"❌ API返回错误: {response_data['error']}", level="error", role="diagnostics")
                    return False
                
                # 检查集合
                collections = response_data.get("result", {}).get("collections", [])
                collection_names = [c.get('name') for c in collections]
                
                self.log("✅ curl测试成功", role="diagnostics")
                self.log(f"发现 {len(collection_names)} 个集合: {', '.join(collection_names)}", role="diagnostics")
                return True
                
            except json.JSONDecodeError:
                self.log(f"❌ 无法解析响应为JSON: {result.stdout}", level="error", role="diagnostics")
                return False
                
        except Exception as e:
            self.log(f"❌ 执行curl命令时出错: {str(e)}", level="error", role="diagnostics")
            self.log(f"详细错误: {traceback.format_exc()}", level="debug", role="diagnostics")
            return False
    
    def run_full_diagnostics(self) -> Dict[str, Any]:
        """
        运行完整的诊断流程
        
        Returns:
            Dict: 包含诊断结果的字典
        """
        results = {
            "config": self.config.copy(),
            "system_info": {},
            "tests": {
                "direct_connection": False,
                "client_connection": False,
                "curl_test": False
            },
            "collections": [],
            "issues": []
        }
        
        # 掩码API密钥
        if results["config"]["api_key"]:
            api_key = results["config"]["api_key"]
            results["config"]["api_key"] = f"{api_key[:8]}...{api_key[-5:]}"
        
        self.log("🔍 开始Qdrant诊断...", role="diagnostics")
        
        # 打印配置
        self.print_config()
        
        # 收集系统信息
        results["system_info"] = self.test_system_info()
        
        # 检查配置问题
        if not self.config['host']:
            results["issues"].append("未设置QDRANT_HOST")
        
        if not self.config['api_key']:
            results["issues"].append("未设置QDRANT_API_KEY")
        
        # 直接连接测试
        results["tests"]["direct_connection"] = self.test_direct_connection()
        
        # 客户端连接测试
        client_ok, client = self.test_client_connection()
        results["tests"]["client_connection"] = client_ok
        
        # 如果客户端连接成功，获取集合信息
        if client_ok and client:
            collections = client.get_collections().collections
            results["collections"] = [c.name for c in collections]
        
        # curl测试
        results["tests"]["curl_test"] = self.test_curl()
        
        # 总结
        self.log("\n诊断摘要:", role="diagnostics")
        
        if all(results["tests"].values()):
            self.log("✅ 所有连接测试通过", role="diagnostics")
        else:
            self.log("⚠️ 部分测试失败:", level="warning", role="diagnostics")
            for test, passed in results["tests"].items():
                status = "✅ 通过" if passed else "❌ 失败"
                self.log(f"  - {test}: {status}", level="warning" if not passed else "info", role="diagnostics")
        
        if results["issues"]:
            self.log("发现以下问题:", level="warning", role="diagnostics")
            for issue in results["issues"]:
                self.log(f"  - {issue}", level="warning", role="diagnostics")
        
        # 提供建议
        self._suggest_solutions(results)
        
        return results
    
    def _suggest_solutions(self, results: Dict[str, Any]) -> None:
        """根据诊断结果提供解决方案建议"""
        self.log("\n解决方案建议:", role="diagnostics")
        
        if not results["issues"] and all(results["tests"].values()):
            self.log("✅ 未发现问题，配置正常工作", role="diagnostics")
            return
        
        # 针对不同问题提供建议
        if "未设置QDRANT_HOST" in results["issues"]:
            self.log("1. 配置Qdrant主机:", role="diagnostics")
            self.log("   - 在.env文件中设置QDRANT_HOST变量", role="diagnostics")
            self.log("   - 使用update_qdrant_config.py脚本: python scripts/database/update_qdrant_config.py --host YOUR_HOST", role="diagnostics")
        
        if "未设置QDRANT_API_KEY" in results["issues"]:
            self.log("2. 配置API密钥:", role="diagnostics")
            self.log("   - 在Qdrant控制台生成新的API密钥", role="diagnostics")
            self.log("   - 在.env文件中设置QDRANT_API_KEY变量", role="diagnostics")
            self.log("   - 使用update_api_key.py脚本: python scripts/database/update_api_key.py", role="diagnostics")
        
        # 如果直接连接失败但curl成功
        if not results["tests"]["direct_connection"] and results["tests"]["curl_test"]:
            self.log("3. HTTP连接问题:", role="diagnostics")
            self.log("   - 检查端口设置是否正确 (通常为6333或443)", role="diagnostics")
            self.log("   - 尝试使用scripts/database/update_qdrant_config.py设置正确的端口", role="diagnostics")
        
        # 如果客户端连接失败
        if not results["tests"]["client_connection"]:
            self.log("4. Qdrant客户端连接问题:", role="diagnostics")
            self.log("   - 检查API密钥格式是否正确", role="diagnostics")
            self.log("   - 确保API密钥具有足够权限", role="diagnostics")
            self.log("   - 尝试在Qdrant控制台重新生成API密钥", role="diagnostics")
        
        # 通用建议
        self.log("\n其他建议:", role="diagnostics")
        self.log("- 使用scripts/database/print_config.py脚本查看当前配置", role="diagnostics")
        self.log("- 使用scripts/database/test_curl.sh脚本测试基本连接", role="diagnostics")
        self.log("- 如果问题持续，请联系Qdrant支持或检查网络连接", role="diagnostics")

# 直接运行诊断的便捷函数
def run_diagnostics(use_logger=True) -> Dict[str, Any]:
    """
    运行Qdrant诊断并返回结果
    
    Args:
        use_logger: 是否使用日志系统，否则使用print
    
    Returns:
        Dict: 包含诊断结果的字典
    """
    diagnostics = QdrantDiagnostics(use_logger=use_logger)
    return diagnostics.run_full_diagnostics()

# 直接测试连接的便捷函数
def test_connection(use_logger=True) -> bool:
    """
    快速测试Qdrant连接
    
    Args:
        use_logger: 是否使用日志系统，否则使用print
        
    Returns:
        bool: 连接是否成功
    """
    diagnostics = QdrantDiagnostics(use_logger=use_logger)
    client_ok, _ = diagnostics.test_client_connection()
    return client_ok

# 命令行入口点
if __name__ == "__main__":
    # 当作为脚本直接运行时，执行完整诊断
    run_diagnostics(use_logger=False) 
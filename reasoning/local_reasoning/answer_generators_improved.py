"""
改进的局部推理答案生成模块。
强制生成具体、结构化的架构决策，避免空泛表述。
"""

from typing import Dict, List, Any, Optional
from llm_services.executor import run_prompt
import json
import re

# 定义具体性模板
SPECIFICITY_TEMPLATE = """
你必须提供具体的技术实现方案，严格避免使用空泛表述。

输出要求：
1. 类名必须具体且符合命名规范（如 UserService, OrderRepository）
2. 方法名必须明确且包含参数（如 createUser(userData: UserDTO): User）
3. 技术栈必须指定具体版本（如 Spring Boot 2.7.0, React 18.2）
4. 数据模型必须包含具体字段和类型
5. API端点必须是完整的RESTful路径（如 POST /api/v1/users）

禁用词汇列表：
- 处理、管理、相关、合适的、一些、某些
- 功能、模块（除非作为具体名称的一部分）
- 可以考虑、建议使用（直接说"使用"）

示例对比：
❌ 错误："处理用户相关功能"
✅ 正确："实现 UserService 类，包含 createUser(dto: CreateUserDTO): User, updateProfile(userId: string, data: UpdateProfileDTO): User, authenticate(credentials: LoginDTO): AuthToken 方法"

❌ 错误："使用合适的数据库"
✅ 正确："使用 PostgreSQL 14.5 存储用户数据，表结构包含 id(UUID), email(VARCHAR(255)), password_hash(VARCHAR(60)), created_at(TIMESTAMP)"
"""

# 分阶段答案模板
PHASED_ANSWER_TEMPLATES = {
    "功能定义与边界划分": """
请按以下结构精确回答：

### 1. 核心功能清单
列出3-5个核心功能，每个功能必须包含：
- 功能名称（动词+名词，如"创建订单"）
- 输入参数（具体数据类型）
- 输出结果（具体返回值）
- 业务规则（1-2条关键规则）

### 2. API接口定义
为每个功能设计RESTful API：
- HTTP方法 + 路径
- 请求体结构（JSON格式）
- 响应体结构（JSON格式）
- 状态码（成功和错误情况）

### 3. 数据模型设计
定义核心实体，包含：
- 实体名称（单数形式）
- 字段列表（名称:类型）
- 主键和索引
- 关联关系

### 4. 职责边界
明确说明：
- 该模块负责什么
- 该模块不负责什么
- 与其他模块的交互点
""",

    "技术实现与模式选择": """
请按以下结构提供技术方案：

### 1. 技术栈选择
- 编程语言及版本：[具体版本号]
- 核心框架：[框架名称及版本]
- 数据库：[数据库类型及版本]
- 缓存方案：[如果需要]
- 消息队列：[如果需要]

### 2. 架构模式
- 整体架构模式：[如分层架构、六边形架构]
- 设计模式应用：
  - 模式名称：使用场景和实现类
  - 示例：Repository模式 - UserRepository接口和UserRepositoryImpl实现

### 3. 核心类设计
提供主要类的设计：
```
类名: [具体类名]
职责: [一句话描述]
主要方法:
  - 方法签名
  - 方法职责
依赖: [依赖的其他类或接口]
```

### 4. 关键算法
如果涉及复杂逻辑，描述：
- 算法名称
- 输入输出
- 时间复杂度
- 伪代码或流程
""",

    "集成设计与依赖分析": """
请详细说明集成方案：

### 1. 外部依赖
列出所有外部依赖：
- 依赖名称：[服务/库名称]
- 依赖版本：[具体版本]
- 依赖用途：[为什么需要]
- 集成方式：[HTTP/gRPC/SDK等]

### 2. 接口契约
定义与其他模块的接口：
```
接口名称: [具体名称]
协议: [HTTP/gRPC/消息队列]
数据格式: [JSON/Protobuf/Avro]
请求示例: [具体示例]
响应示例: [具体示例]
错误码: [错误码列表]
```

### 3. 数据流设计
描述数据流动：
- 入口：数据从哪里来
- 处理：经过哪些组件
- 出口：数据到哪里去
- 异常流：错误如何处理

### 4. 事务边界
明确事务管理：
- 事务范围
- 隔离级别
- 补偿机制
""",

    "质量保证与优化": """
请提供质量保证方案：

### 1. 性能指标
- 响应时间要求：[具体毫秒数]
- 吞吐量要求：[QPS/TPS]
- 并发用户数：[具体数字]
- 资源限制：[CPU/内存]

### 2. 性能优化
- 缓存策略：[具体方案]
- 数据库优化：[索引/分区/读写分离]
- 异步处理：[消息队列/线程池]
- 限流降级：[具体实现]

### 3. 安全措施
- 认证方式：[JWT/OAuth2/Session]
- 授权模型：[RBAC/ABAC]
- 数据加密：[传输/存储加密方案]
- 安全头：[具体HTTP头]

### 4. 测试策略
- 单元测试：[覆盖率目标]
- 集成测试：[测试场景]
- 性能测试：[测试工具和指标]
- 示例测试代码：[具体示例]
"""
}

async def generate_specific_answer(
    entity_name: str,
    question: str,
    context: str,
    round_goal: str,
    previous_answers: Optional[List[str]] = None
) -> str:
    """
    生成具体、结构化的架构答案。
    
    Args:
        entity_name: 实体名称
        question: 问题内容
        context: 上下文信息
        round_goal: 当前推理目标
        previous_answers: 之前的答案（用于保持一致性）
        
    Returns:
        str: 具体的架构答案
    """
    # 选择合适的答案模板
    answer_template = PHASED_ANSWER_TEMPLATES.get(
        round_goal, 
        PHASED_ANSWER_TEMPLATES["功能定义与边界划分"]
    )
    
    # 构建增强的系统提示
    system_prompt = f"""{SPECIFICITY_TEMPLATE}

你是一个专业的软件架构师，正在为 "{entity_name}" 模块设计详细的技术方案。

当前阶段：{round_goal}

{answer_template}"""
    
    # 构建用户提示，包含之前的答案以保持一致性
    previous_context = ""
    if previous_answers:
        previous_context = "\n之前的设计决策：\n" + "\n".join(
            f"- {ans[:200]}..." if len(ans) > 200 else f"- {ans}"
            for ans in previous_answers[-3:]  # 只包含最近3个答案
        )
    
    user_prompt = f"""问题：{question}

基于以下信息回答：
{context}
{previous_context}

请严格按照模板格式回答，确保所有内容都是具体的、可实施的。"""

    # 调用LLM生成回答
    answer = await run_prompt(
        system_message=system_prompt,
        user_message=user_prompt,
        temperature=0.3  # 降低温度以获得更一致的输出
    )
    
    # 验证答案质量
    quality_score, issues = validate_answer_quality(answer)
    
    # 如果质量不合格，尝试改进
    if quality_score < 70 and len(issues) > 0:
        improvement_prompt = f"""
之前的回答存在以下问题：
{chr(10).join(issues)}

请重新回答，确保：
1. 避免使用空泛词汇
2. 提供具体的类名、方法名、技术版本
3. 包含可执行的代码示例或配置

原始问题：{question}
"""
        answer = await run_prompt(
            system_message=system_prompt,
            user_message=improvement_prompt,
            temperature=0.2
        )
    
    return answer

def validate_answer_quality(answer: str) -> tuple[int, List[str]]:
    """
    验证答案质量，返回分数和问题列表。
    
    Args:
        answer: 生成的答案
        
    Returns:
        tuple: (质量分数, 问题列表)
    """
    score = 100
    issues = []
    
    # 检查空泛词汇
    vague_terms = [
        "处理", "管理", "相关", "合适的", "一些", "某些",
        "功能", "模块", "可以考虑", "建议使用"
    ]
    
    for term in vague_terms:
        # 排除作为具体名称一部分的情况
        pattern = rf'\b{term}\b(?![A-Z]|\w+Service|\w+Repository|\w+Controller)'
        occurrences = len(re.findall(pattern, answer, re.IGNORECASE))
        if occurrences > 0:
            score -= 5 * occurrences
            issues.append(f"使用了空泛词汇 '{term}' {occurrences} 次")
    
    # 检查是否包含具体类名
    class_pattern = r'[A-Z]\w+(?:Service|Repository|Controller|Factory|Builder|Manager|Handler)'
    if not re.search(class_pattern, answer):
        score -= 20
        issues.append("缺少具体的类名定义")
    
    # 检查是否包含方法签名
    method_pattern = r'\w+\([^)]*\)(?:\s*:\s*\w+)?'
    if not re.search(method_pattern, answer):
        score -= 15
        issues.append("缺少具体的方法签名")
    
    # 检查是否包含技术版本
    version_pattern = r'\d+\.\d+(?:\.\d+)?'
    if not re.search(version_pattern, answer):
        score -= 10
        issues.append("缺少具体的技术版本号")
    
    # 检查是否包含API路径
    api_pattern = r'(?:GET|POST|PUT|DELETE|PATCH)\s+/\w+'
    if "API" in answer.upper() and not re.search(api_pattern, answer):
        score -= 10
        issues.append("提到API但缺少具体的端点定义")
    
    # 确保分数不低于0
    score = max(0, score)
    
    return score, issues

async def generate_structured_json_summary(
    entity_name: str,
    qa_pairs: List[Dict[str, str]],
    entity_type: str
) -> Dict[str, Any]:
    """
    基于问答对生成结构化的JSON摘要。
    
    Args:
        entity_name: 实体名称
        qa_pairs: 问答对列表
        entity_type: 实体类型
        
    Returns:
        Dict: 结构化的JSON摘要
    """
    # 定义严格的JSON模板
    json_template = {
        "module": entity_name,
        "type": entity_type,
        "description": "",
        "core_functionality": [],
        "technical_decisions": {
            "language": "",
            "framework": "",
            "database": "",
            "patterns": []
        },
        "api_design": {
            "endpoints": [],
            "authentication": "",
            "data_format": "JSON"
        },
        "implementation": {
            "services": [],
            "repositories": [],
            "controllers": [],
            "models": []
        },
        "dependencies": {
            "internal": [],
            "external": []
        },
        "testing_strategy": {
            "unit_test_coverage": "",
            "integration_tests": [],
            "performance_benchmarks": []
        }
    }
    
    # 构建摘要提示
    qa_context = "\n\n".join([
        f"Q: {pair['question']}\nA: {pair['answer']}"
        for pair in qa_pairs
    ])
    
    system_prompt = """你是一个JSON生成专家，需要从问答内容中提取信息填充JSON模板。

规则：
1. 只提取问答中明确提到的信息
2. 类名必须以大写字母开头，符合命名规范
3. 方法名必须是驼峰命名
4. API端点必须以/开头
5. 不要创造问答中没有的信息
6. 如果某个字段没有信息，保持空值（空字符串或空数组）

输出必须是有效的JSON格式。"""
    
    user_prompt = f"""基于以下问答内容，填充JSON模板：

{qa_context}

请填充这个JSON模板（保持结构不变）：
{json.dumps(json_template, indent=2, ensure_ascii=False)}

记住：
- services数组示例：["UserService", "AuthService"]
- endpoints数组示例：[{{"method": "POST", "path": "/api/v1/users", "description": "创建用户"}}]
- 只填充问答中明确提到的内容"""
    
    # 生成JSON
    response = await run_prompt(
        system_message=system_prompt,
        user_message=user_prompt,
        temperature=0.1  # 非常低的温度以确保一致性
    )
    
    # 尝试解析JSON
    try:
        # 提取JSON部分（处理可能的markdown代码块）
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析整个响应
            json_str = response
            
        summary = json.loads(json_str)
        
        # 验证并清理空泛内容
        summary = clean_vague_content(summary)
        
        return summary
        
    except json.JSONDecodeError:
        # 如果解析失败，返回基础结构
        return {
            "module": entity_name,
            "type": entity_type,
            "description": "JSON解析失败，需要手动检查",
            "parse_error": True,
            "raw_response": response[:500]
        }

def clean_vague_content(summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    清理JSON中的空泛内容。
    
    Args:
        summary: 原始摘要
        
    Returns:
        Dict: 清理后的摘要
    """
    vague_phrases = [
        "处理.*功能", "管理.*", "相关.*", "一些.*", "某些.*"
    ]
    
    def clean_string(s: str) -> str:
        if isinstance(s, str):
            for phrase in vague_phrases:
                s = re.sub(phrase, "", s)
            return s.strip()
        return s
    
    def clean_recursive(obj):
        if isinstance(obj, dict):
            return {k: clean_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_recursive(item) for item in obj if item]
        elif isinstance(obj, str):
            cleaned = clean_string(obj)
            return cleaned if cleaned else None
        return obj
    
    # 清理整个对象
    cleaned = clean_recursive(summary)
    
    # 移除空值
    def remove_nulls(obj):
        if isinstance(obj, dict):
            return {k: remove_nulls(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [remove_nulls(item) for item in obj if item is not None]
        return obj
    
    return remove_nulls(cleaned)

# 批量生成的改进版本
async def generate_specific_answers(
    questions: List[str],
    context: str,
    entity_name: str = "当前实体",
    round_goal: str = "功能定义与边界划分"
) -> List[str]:
    """
    批量生成具体的答案。
    
    Args:
        questions: 问题列表
        context: 上下文信息
        entity_name: 实体名称
        round_goal: 当前推理目标
        
    Returns:
        List[str]: 具体的答案列表
    """
    if not questions:
        return []
    
    answers = []
    
    for i, question in enumerate(questions):
        answer = await generate_specific_answer(
            entity_name=entity_name,
            question=question,
            context=context,
            round_goal=round_goal,
            previous_answers=answers  # 传递之前的答案以保持一致性
        )
        answers.append(answer)
    
    return answers
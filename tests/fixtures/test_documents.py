"""
测试文档数据fixtures
提供各种测试场景需要的输入文档数据
"""

SAMPLE_ARCHITECTURE_DOC = """
# ThinkForward AI - 技术架构设计

## 1. 整体架构概览

ThinkForward AI采用serverless架构，专注于快速交付MVP，同时保证可扩展性。整体架构如下：

- **前端**：Next.js框架，React组件库，Tailwind CSS
- **API网关**：AWS API Gateway / Azure API Management
- **认证**：AWS Cognito / Auth0
- **Serverless函数**：AWS Lambda / Azure Functions (Node.js)
- **数据库**：MongoDB Atlas
- **存储**：AWS S3 / Azure Blob Storage
- **AI集成**：OpenAI API

### 技术架构原则

- **无服务器优先**：避免管理服务器，专注于业务逻辑
- **功能分离**：按业务域划分函数，确保职责单一
- **事件驱动**：使用事件模式进行服务间通信
- **缓存策略**：适当缓存以提高性能和降低成本
- **安全优先**：数据加密、身份验证和授权控制
"""

SAMPLE_USER_SERVICE_DOC = """
# 用户认证与资料管理服务

## 功能职责
用户服务负责处理所有与用户账户相关的操作，包括但不限于:
- 用户注册与登录
- 个人资料管理
- 认证与授权
- 用户角色管理（客户/顾问/管理员）

## 技术实现
- Serverless函数 (Node.js)
- JWT令牌实现无状态会话
- Cognito/Auth0集成
- MongoDB存储用户数据

## API设计
- POST /auth/login - 用户登录
- POST /auth/register - 新用户注册
- GET /profile - 获取用户资料
- PATCH /profile - 更新用户资料
- GET /profile/completeness - 获取资料完整度

## 数据模型
User {
  _id: ObjectId,
  email: String,
  name: String,
  role: String, // client, consultant, admin
  status: String, // active, inactive, suspended
  createdAt: Date,
  profile: {
    personalInfo: Object,
    education: Array,
    workExperience: Array,
    languageSkills: Array,
    familyInfo: Array,
    profileCompleteness: Object
  }
}

## 依赖关系
- 评估服务 - 用户完整性评估
- 通知服务 - 发送邮件通知
"""

SAMPLE_ASSESSMENT_SERVICE_DOC = """
# 评估与路径建议服务

## 功能职责
评估服务负责管理移民申请者的资格评估流程，包括:
- 初步评估问卷处理
- 移民路径分析与建议
- 资格评分计算
- 成功概率预测

## 技术实现
- Serverless函数 (Node.js)
- OpenAI API集成
- 数据分析算法
- MongoDB存储评估数据

## API设计
- POST /assessments - 创建新评估
- GET /assessments/{id} - 获取评估详情
- POST /assessments/{id}/steps/{stepId} - 提交评估步骤
- GET /assessments/{id}/result - 获取评估结果
- POST /pathways/compare - 比较移民路径

## 数据模型
Assessment {
  _id: ObjectId,
  userId: String,
  status: String, // in-progress, completed
  startedAt: Date,
  completedAt: Date,
  currentStep: Number,
  steps: Array,
  results: {
    overallEligibility: String,
    expressEntryScore: Number,
    programEligibility: Object,
    recommendedPathways: Array
  }
}

## 依赖关系
- 用户服务 - 获取用户资料
- 表格服务 - 生成推荐表格
"""

SAMPLE_FORM_SERVICE_DOC = """
# 智能表格生成服务

## 功能职责
表格服务负责自动生成和管理加拿大移民申请表格，包括:
- 用户数据映射至官方表格
- 表格验证与错误检测
- PDF生成与管理
- 表格填写指导

## 技术实现
- Serverless函数 (Node.js)
- OpenAI API用于数据映射
- PDF生成库
- S3/Blob存储生成的文档

## API设计
- GET /forms/templates - 获取表格模板列表
- POST /forms/generate - 生成表格
- GET /forms/{id} - 获取特定表格
- PATCH /forms/{id} - 更新表格字段
- GET /forms/{id}/download - 下载表格PDF

## 数据模型
GeneratedForm {
  _id: ObjectId,
  userId: String,
  templateId: String,
  createdAt: Date,
  updatedAt: Date,
  status: String, // draft, completed, submitted
  data: Object,
  validationResults: {
    isValid: Boolean,
    errors: Array,
    warnings: Array
  },
  pdfStorageKey: String
}

## 依赖关系
- 用户服务 - 获取用户资料
- 文档服务 - 存储生成的表格
"""

SAMPLE_DOCUMENT_SERVICE_DOC = """
# 文档管理与分析服务

## 功能职责
文档服务负责管理用户上传的所有文档，包括:
- 文档上传与分类
- 文档内容分析与数据提取
- 文档验证与合规检查
- 安全存储与访问控制

## 技术实现
- Serverless函数 (Node.js)
- OpenAI API进行文档分析
- S3/Blob存储文档
- MongoDB存储文档元数据

## API设计
- POST /documents - 上传新文档
- GET /documents - 获取用户文档列表
- GET /documents/{id} - 获取特定文档
- POST /documents/{id}/analyze - 分析文档
- DELETE /documents/{id} - 删除文档

## 数据模型
Document {
  _id: ObjectId,
  userId: String,
  filename: String,
  fileSize: Number,
  mimeType: String,
  storageKey: String,
  uploadedAt: Date,
  documentType: String,
  status: String, // uploaded, processed, verified
  analysis: {
    processedAt: Date,
    extractedData: Object,
    confidence: Number
  }
}

## 依赖关系
- 用户服务 - 用户验证和权限检查
- 表格服务 - 根据文档内容预填表格
"""

SAMPLE_CONSULTANT_SERVICE_DOC = """
# 顾问匹配与协作服务

## 功能职责
顾问服务负责管理客户和移民顾问之间的匹配与协作，包括:
- 顾问匹配算法
- 预约管理
- 协作工作区
- 任务分配与跟踪

## 技术实现
- Serverless函数 (Node.js)
- 实时消息传递
- MongoDB存储工作区数据
- 日历集成API

## API设计
- GET /consultants - 获取顾问列表
- POST /consultants/match - 匹配合适顾问
- POST /consultants/{id}/appointments - 创建预约
- GET /workspaces/{id} - 获取工作区详情
- POST /workspaces/{id}/messages - 发送工作区消息

## 数据模型
Workspace {
  _id: ObjectId,
  clientId: String,
  consultantId: String,
  createdAt: Date,
  status: String, // active, closed
  sharedDocuments: Array,
  tasks: Array,
  messages: Array
}

## 依赖关系
- 用户服务 - 获取用户与顾问资料
- 文档服务 - 管理共享文档
- 表格服务 - 协作表格填写
"""

SAMPLE_API_DOCS = [
    SAMPLE_ARCHITECTURE_DOC,
    SAMPLE_USER_SERVICE_DOC,
    SAMPLE_ASSESSMENT_SERVICE_DOC,
    SAMPLE_FORM_SERVICE_DOC,
    SAMPLE_DOCUMENT_SERVICE_DOC,
    SAMPLE_CONSULTANT_SERVICE_DOC
] 
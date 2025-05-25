#!/bin/bash
# 测试组件的便捷脚本

set -e

# 包含彩色输出函数
highlight() {
    echo -e "\033[1;34m$1\033[0m"
}

error() {
    echo -e "\033[1;31m$1\033[0m"
}

success() {
    echo -e "\033[1;32m$1\033[0m"
}

warn() {
    echo -e "\033[1;33m$1\033[0m"
}

# 帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  --init-db                                   测试前初始化Qdrant数据库集合"
    echo "  --test-db                                   测试Qdrant数据库连接"
    echo "  --analyzer <input_file> [output_file]      测试文档内容分析组件"
    echo "  --summarizer <input_file> <entity_name> [output_file]    测试初始摘要生成"
    echo "  --knowledge <action> <entity_name> [input_file]   测试知识存储 (actions: save, retrieve, list)"
    echo "  --reasoning <entity_name> [rounds] [constraints_file] [entity_file]    测试本地推理"
    echo "  --dependency [action]                       测试依赖管理模块 (actions: test-all, create-graph, infer-dependencies, test-real-api)"
    echo "  --help                                      显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --init-db                           # 初始化数据库集合"
    echo "  $0 --test-db                           # 测试数据库连接"
    echo "  $0 --analyzer data/sample_doc.txt"
    echo "  $0 --summarizer data/sample_doc.txt ModuleName"
    echo "  $0 --knowledge list"
    echo "  $0 --knowledge retrieve ModuleName"
    echo "  $0 --knowledge save ModuleName data/entity.json"
    echo "  $0 --reasoning ModuleName 2"
    echo "  $0 --reasoning ModuleName 2 data/constraints.json data/entity.json"
    echo "  $0 --dependency test-all               # 运行所有依赖管理测试"
    echo "  $0 --dependency create-graph           # 创建示例依赖图"
    echo "  $0 --dependency test-real-api          # 使用真实API测试依赖推断"
}

# 初始化数据库函数
init_db() {
    highlight "初始化Qdrant数据库集合..."
    python scripts/database/init_db.py
}

# 测试数据库连接函数
test_db() {
    highlight "测试Qdrant数据库连接..."
    python scripts/database/test_qdrant_connection.py --full
}

# 检查参数
if [ $# -eq 0 ] || [ "$1" == "--help" ]; then
    show_help
    exit 0
fi

# 显示测试标题
highlight "======== Expeta 组件测试 ========"
echo "当前目录: $(pwd)"

# 主命令解析
case "$1" in
    --init-db)
        init_db
        ;;
        
    --test-db)
        test_db
        ;;
        
    --analyzer)
        if [ -z "$2" ]; then
            error "错误: 需要提供输入文件"
            show_help
            exit 1
        fi
        
        highlight "运行文档内容分析器测试"
        if [ -z "$3" ]; then
            python scripts/testing/test_components.py --mode content_analyzer --input "$2"
        else
            python scripts/testing/test_components.py --mode content_analyzer --input "$2" --output "$3"
        fi
        ;;
        
    --summarizer)
        if [ -z "$2" ] || [ -z "$3" ]; then
            error "错误: 需要提供输入文件和实体名称"
            show_help
            exit 1
        fi
        
        highlight "运行初始摘要生成器测试"
        if [ -z "$4" ]; then
            python scripts/testing/test_components.py --mode initial_summarizer --input "$2" --entity "$3"
        else
            python scripts/testing/test_components.py --mode initial_summarizer --input "$2" --entity "$3" --output "$4"
        fi
        ;;
        
    --knowledge)
        if [ -z "$2" ]; then
            error "错误: 需要提供操作类型 (save, retrieve, list)"
            show_help
            exit 1
        fi
        
        highlight "运行知识存储测试"
        # 可选：初始化数据库
        if [ "$2" != "list" ]; then  # 对于非列表操作，初始化数据库可能更重要
            warn "初始化Qdrant数据库集合，确保可以存储/检索实体..."
            init_db
        fi
        
        case "$2" in
            list)
                python scripts/testing/test_components.py --mode knowledge_store --action list
                ;;
                
            retrieve)
                if [ -z "$3" ]; then
                    error "错误: 需要提供实体名称"
                    exit 1
                fi
                python scripts/testing/test_components.py --mode knowledge_store --action retrieve --entity "$3"
                ;;
                
            save)
                if [ -z "$3" ] || [ -z "$4" ]; then
                    error "错误: 保存操作需要提供实体名称和输入文件"
                    exit 1
                fi
                python scripts/testing/test_components.py --mode knowledge_store --action save --entity "$3" --input "$4"
                ;;
                
            *)
                error "错误: 不支持的操作类型 '$2'"
                show_help
                exit 1
                ;;
        esac
        ;;
        
    --reasoning)
        if [ -z "$2" ]; then
            error "错误: 需要提供实体名称"
            show_help
            exit 1
        fi
        
        highlight "运行本地推理测试"
        # 初始化数据库 - 推理需要多个集合
        warn "初始化Qdrant数据库集合，确保可以存储/检索推理结果..."
        init_db
        
        rounds="${3:-1}"
        
        if [ -z "$4" ] && [ -z "$5" ]; then
            # 无约束和实体文件
            python scripts/testing/test_components.py --mode local_reasoning --entity "$2" --rounds "$rounds"
        elif [ -n "$4" ] && [ -z "$5" ]; then
            # 有约束但无实体文件
            python scripts/testing/test_components.py --mode local_reasoning --entity "$2" --rounds "$rounds" --constraints "$4"
        elif [ -n "$4" ] && [ -n "$5" ]; then
            # 有约束和实体文件
            python scripts/testing/test_components.py --mode local_reasoning --entity "$2" --rounds "$rounds" --constraints "$4" --input "$5"
        elif [ -z "$4" ] && [ -n "$5" ]; then
            # 无约束但有实体文件
            python scripts/testing/test_components.py --mode local_reasoning --entity "$2" --rounds "$rounds" --input "$5"
        fi
        ;;
        
    --dependency)
        highlight "运行依赖管理模块测试"
        
        # 执行依赖管理测试脚本
        action="${2:-test-all}"
        
        # 检查是否是真实API测试
        if [ "$action" == "test-real-api" ]; then
            warn "执行真实API调用测试，可能需要API密钥和网络连接..."
        fi
        
        python scripts/testing/test_dependency.py "$action"
        ;;
        
    *)
        error "错误: 未知选项 '$1'"
        show_help
        exit 1
        ;;
esac

success "测试完成!" 
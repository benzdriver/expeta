#!/bin/bash

# Clarifier测试运行脚本
# 使用方法: ./clarifier/run_tests.sh [选项]

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/Users/ziyanzhou/Projects/expeta"
cd $PROJECT_ROOT

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo -e "${RED}错误: 虚拟环境不存在${NC}"
    echo "请先创建虚拟环境: python -m venv .venv"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

# 设置Python路径
export PYTHONPATH=$PROJECT_ROOT:$PYTHONPATH

# 显示帮助信息
show_help() {
    echo "Clarifier测试运行脚本"
    echo ""
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  all          运行所有测试并生成覆盖率报告（默认）"
    echo "  unit         只运行单元测试"
    echo "  integration  只运行集成测试"
    echo "  real         只运行真实数据测试"
    echo "  coverage     生成详细覆盖率报告"
    echo "  check        检查测试覆盖状态"
    echo "  blind        测试盲点检测器"
    echo "  version      测试版本管理器"
    echo "  impact       测试影响分析器"
    echo "  refactor     测试重构引擎"
    echo "  quick        快速测试（跳过慢速测试）"
    echo "  help         显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 all       # 运行所有测试"
    echo "  $0 unit      # 只运行单元测试"
    echo "  $0 coverage  # 生成覆盖率报告"
}

# 运行所有测试
run_all_tests() {
    echo -e "${GREEN}运行所有Clarifier测试...${NC}"
    python clarifier/tests/run_tests_with_coverage.py
}

# 运行单元测试
run_unit_tests() {
    echo -e "${GREEN}运行单元测试...${NC}"
    python -m pytest clarifier/tests/test_blind_spot_detector.py \
                     clarifier/tests/test_version_manager.py \
                     clarifier/tests/test_impact_analyzer.py \
                     clarifier/tests/test_refactoring_engine.py -v
}

# 运行集成测试
run_integration_tests() {
    echo -e "${GREEN}运行集成测试...${NC}"
    python -m pytest clarifier/tests/test_clarifier_integration.py \
                     clarifier/tests/test_all_components.py -v
}

# 运行真实数据测试
run_real_data_tests() {
    echo -e "${GREEN}运行真实数据测试...${NC}"
    python -m pytest clarifier/tests/test_clarifier_orchestrator_real_data.py -v
}

# 生成覆盖率报告
generate_coverage() {
    echo -e "${GREEN}生成覆盖率报告...${NC}"
    python -m coverage run -m pytest clarifier/tests
    python -m coverage report --show-missing
    python -m coverage html
    echo -e "${YELLOW}HTML报告位置: clarifier/tests/htmlcov/index.html${NC}"
}

# 检查测试状态
check_status() {
    echo -e "${GREEN}检查测试覆盖状态...${NC}"
    python clarifier/tests/check_coverage.py
}

# 测试特定组件
test_component() {
    case $1 in
        blind)
            echo -e "${GREEN}测试盲点检测器...${NC}"
            python -m pytest clarifier/tests/test_blind_spot_detector.py -v
            ;;
        version)
            echo -e "${GREEN}测试版本管理器...${NC}"
            python -m pytest clarifier/tests/test_version_manager.py -v
            ;;
        impact)
            echo -e "${GREEN}测试影响分析器...${NC}"
            python -m pytest clarifier/tests/test_impact_analyzer.py -v
            ;;
        refactor)
            echo -e "${GREEN}测试重构引擎...${NC}"
            python -m pytest clarifier/tests/test_refactoring_engine.py -v
            ;;
    esac
}

# 快速测试（跳过慢速测试）
run_quick_tests() {
    echo -e "${GREEN}运行快速测试（跳过慢速测试）...${NC}"
    python -m pytest clarifier/tests -m "not slow" -v
}

# 主程序
case "${1:-all}" in
    all)
        run_all_tests
        ;;
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    real)
        run_real_data_tests
        ;;
    coverage)
        generate_coverage
        ;;
    check)
        check_status
        ;;
    blind|version|impact|refactor)
        test_component $1
        ;;
    quick)
        run_quick_tests
        ;;
    help)
        show_help
        ;;
    *)
        echo -e "${RED}未知选项: $1${NC}"
        show_help
        exit 1
        ;;
esac

# 显示测试完成信息
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 测试完成${NC}"
else
    echo -e "${RED}✗ 测试失败${NC}"
    exit 1
fi
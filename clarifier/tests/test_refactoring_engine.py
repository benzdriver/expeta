"""
Comprehensive tests for SmartRefactoring engine
"""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from clarifier.core import SmartRefactoring
from clarifier.core.refactoring_engine import (
    RefactoringStrategy, RefactoringPlan, RefactoringStep,
    RefactoringStatus, ValidationResult
)


class TestSmartRefactoring:
    """Test SmartRefactoring functionality"""
    
    @pytest.fixture
    def refactoring_engine(self):
        """Create SmartRefactoring instance"""
        return SmartRefactoring()
    
    @pytest.fixture
    def simple_change_request(self):
        """Simple change request"""
        return {
            "type": "feature_addition",
            "description": "Add user profile picture",
            "requirements": {
                "current": {
                    "user_profile": ["name", "email", "bio"]
                },
                "target": {
                    "user_profile": ["name", "email", "bio", "profile_picture"]
                }
            }
        }
    
    @pytest.fixture
    def complex_change_request(self):
        """Complex change request from immigration system"""
        return {
            "type": "architecture_change",
            "description": "Add real-time collaboration for consultants",
            "requirements": {
                "current": {
                    "consultant_features": ["client_management", "document_review"],
                    "communication": ["email", "in_app_messaging"]
                },
                "target": {
                    "consultant_features": ["client_management", "document_review", "real_time_collaboration"],
                    "communication": ["email", "in_app_messaging", "video_calls", "screen_sharing"],
                    "infrastructure": ["websocket_server", "webrtc_integration"]
                }
            },
            "constraints": {
                "timeline": "2 months",
                "budget": "limited",
                "downtime": "minimal"
            }
        }
    
    @pytest.fixture
    def impact_analysis(self):
        """Mock impact analysis result"""
        return {
            "affected_components": ["user_service", "frontend", "database"],
            "effort_hours": 40,
            "risk_level": "medium",
            "dependencies": {
                "user_service": ["database", "auth_service"],
                "frontend": ["user_service", "api_gateway"]
            }
        }
    
    @pytest.mark.asyncio
    async def test_create_refactoring_plan_incremental(self, refactoring_engine, simple_change_request, impact_analysis):
        """Test creating incremental refactoring plan"""
        plan = await refactoring_engine.create_refactoring_plan(
            simple_change_request,
            impact_analysis,
            strategy=RefactoringStrategy.INCREMENTAL
        )
        
        assert isinstance(plan, RefactoringPlan)
        assert plan.strategy == RefactoringStrategy.INCREMENTAL
        assert len(plan.steps) > 0
        assert plan.total_effort_hours == impact_analysis["effort_hours"]
        assert plan.risk_assessment["level"] == "medium"
        
        # Check steps are properly ordered
        for i, step in enumerate(plan.steps):
            assert step.order == i + 1
            assert step.status == RefactoringStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_create_refactoring_plan_big_bang(self, refactoring_engine, complex_change_request):
        """Test creating big bang refactoring plan"""
        impact = {
            "affected_components": ["consultant_service", "communication_service", "frontend"],
            "effort_hours": 320,
            "risk_level": "high"
        }
        
        plan = await refactoring_engine.create_refactoring_plan(
            complex_change_request,
            impact,
            strategy=RefactoringStrategy.BIG_BANG
        )
        
        assert plan.strategy == RefactoringStrategy.BIG_BANG
        assert plan.risk_assessment["level"] == "high"
        
        # Big bang should have preparation and cutover phases
        phase_names = [step.name for step in plan.steps]
        assert any("preparation" in name.lower() for name in phase_names)
        assert any("cutover" in name.lower() or "migration" in name.lower() for name in phase_names)
    
    @pytest.mark.asyncio
    async def test_create_refactoring_plan_parallel(self, refactoring_engine, complex_change_request):
        """Test creating parallel refactoring plan"""
        impact = {
            "affected_components": ["service_a", "service_b", "service_c"],
            "effort_hours": 120,
            "risk_level": "medium",
            "parallel_safe": True
        }
        
        plan = await refactoring_engine.create_refactoring_plan(
            complex_change_request,
            impact,
            strategy=RefactoringStrategy.PARALLEL
        )
        
        assert plan.strategy == RefactoringStrategy.PARALLEL
        
        # Check for parallel execution groups
        parallel_groups = {}
        for step in plan.steps:
            if "parallel_group" in step.metadata:
                group = step.metadata["parallel_group"]
                if group not in parallel_groups:
                    parallel_groups[group] = []
                parallel_groups[group].append(step)
        
        assert len(parallel_groups) > 0
    
    @pytest.mark.asyncio
    async def test_create_refactoring_plan_feature_toggle(self, refactoring_engine, simple_change_request, impact_analysis):
        """Test creating feature toggle refactoring plan"""
        plan = await refactoring_engine.create_refactoring_plan(
            simple_change_request,
            impact_analysis,
            strategy=RefactoringStrategy.FEATURE_TOGGLE
        )
        
        assert plan.strategy == RefactoringStrategy.FEATURE_TOGGLE
        
        # Should include toggle setup and cleanup steps
        step_names = [step.name for step in plan.steps]
        assert any("toggle" in name.lower() or "flag" in name.lower() for name in step_names)
        assert any("cleanup" in name.lower() or "remove" in name.lower() for name in step_names)
    
    @pytest.mark.asyncio
    async def test_execute_refactoring_success(self, refactoring_engine):
        """Test successful refactoring execution"""
        # Create a simple plan
        plan = RefactoringPlan(
            id="test_plan_1",
            strategy=RefactoringStrategy.INCREMENTAL,
            steps=[
                RefactoringStep(
                    id="step_1",
                    name="Update database schema",
                    description="Add profile_picture column",
                    order=1,
                    estimated_hours=2,
                    dependencies=[],
                    validation_criteria=["Column exists", "No data loss"]
                ),
                RefactoringStep(
                    id="step_2",
                    name="Update API",
                    description="Add profile picture endpoints",
                    order=2,
                    estimated_hours=4,
                    dependencies=["step_1"],
                    validation_criteria=["API responds", "Upload works"]
                )
            ],
            total_effort_hours=6,
            risk_assessment={"level": "low"},
            rollback_plan={"strategy": "restore_backup"}
        )
        
        # Mock execution
        with patch.object(refactoring_engine, '_execute_step', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = True
            
            with patch.object(refactoring_engine, '_validate_step', new_callable=AsyncMock) as mock_validate:
                mock_validate.return_value = ValidationResult(
                    success=True,
                    checks_passed=["All checks passed"],
                    checks_failed=[]
                )
                
                result = await refactoring_engine.execute_refactoring(plan)
                
                assert result["success"] == True
                assert result["completed_steps"] == 2
                assert result["status"] == RefactoringStatus.COMPLETED
                assert mock_execute.call_count == 2
                assert mock_validate.call_count == 2
    
    @pytest.mark.asyncio
    async def test_execute_refactoring_with_failure(self, refactoring_engine):
        """Test refactoring execution with failure and rollback"""
        plan = RefactoringPlan(
            id="test_plan_2",
            strategy=RefactoringStrategy.INCREMENTAL,
            steps=[
                RefactoringStep(
                    id="step_1",
                    name="Step 1",
                    description="First step",
                    order=1,
                    estimated_hours=1,
                    dependencies=[]
                ),
                RefactoringStep(
                    id="step_2",
                    name="Step 2",
                    description="Failing step",
                    order=2,
                    estimated_hours=1,
                    dependencies=["step_1"]
                )
            ],
            total_effort_hours=2,
            risk_assessment={"level": "medium"},
            rollback_plan={"strategy": "restore_checkpoints"}
        )
        
        # Mock execution - first succeeds, second fails
        exec_results = [True, False]
        with patch.object(refactoring_engine, '_execute_step', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = exec_results
            
            with patch.object(refactoring_engine, '_rollback_step', new_callable=AsyncMock) as mock_rollback:
                mock_rollback.return_value = True
                
                result = await refactoring_engine.execute_refactoring(plan, auto_rollback=True)
                
                assert result["success"] == False
                assert result["completed_steps"] == 1
                assert result["failed_step"] == "step_2"
                assert result["status"] == RefactoringStatus.ROLLED_BACK
                assert mock_rollback.called
    
    @pytest.mark.asyncio
    async def test_validate_refactoring(self, refactoring_engine):
        """Test refactoring validation"""
        plan = RefactoringPlan(
            id="test_plan_3",
            strategy=RefactoringStrategy.INCREMENTAL,
            steps=[
                RefactoringStep(
                    id="step_1",
                    name="Database update",
                    description="Schema change",
                    order=1,
                    estimated_hours=2,
                    dependencies=[],
                    validation_criteria=[
                        "Schema version updated",
                        "All migrations successful",
                        "No data corruption"
                    ]
                )
            ],
            total_effort_hours=2,
            risk_assessment={"level": "low"},
            rollback_plan={}
        )
        
        # Mock validation checks
        with patch.object(refactoring_engine, '_run_validation_check', new_callable=AsyncMock) as mock_check:
            mock_check.side_effect = [True, True, True]  # All checks pass
            
            validation_result = await refactoring_engine.validate_refactoring(plan)
            
            assert validation_result["all_passed"] == True
            assert len(validation_result["results"]) == 1
            assert validation_result["results"][0]["success"] == True
            assert mock_check.call_count == 3
    
    @pytest.mark.asyncio
    async def test_rollback_execution(self, refactoring_engine):
        """Test rollback execution"""
        # Create plan with completed steps
        plan = RefactoringPlan(
            id="test_plan_4",
            strategy=RefactoringStrategy.INCREMENTAL,
            steps=[
                RefactoringStep(
                    id="step_1",
                    name="Step 1",
                    description="Completed step",
                    order=1,
                    estimated_hours=1,
                    dependencies=[],
                    status=RefactoringStatus.COMPLETED
                ),
                RefactoringStep(
                    id="step_2",
                    name="Step 2",
                    description="Failed step",
                    order=2,
                    estimated_hours=1,
                    dependencies=["step_1"],
                    status=RefactoringStatus.FAILED
                )
            ],
            total_effort_hours=2,
            risk_assessment={"level": "low"},
            rollback_plan={
                "strategy": "reverse_order",
                "checkpoints": ["checkpoint_1"]
            }
        )
        
        with patch.object(refactoring_engine, '_rollback_step', new_callable=AsyncMock) as mock_rollback:
            mock_rollback.return_value = True
            
            result = await refactoring_engine.rollback(plan, reason="Test failure")
            
            assert result["success"] == True
            assert result["rolled_back_steps"] == 1
            assert result["reason"] == "Test failure"
            mock_rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_estimate_refactoring_effort(self, refactoring_engine):
        """Test effort estimation for refactoring"""
        change_request = {
            "type": "feature_addition",
            "scope": "medium",
            "components": ["service_a", "service_b", "database"],
            "complexity": "medium"
        }
        
        impact_analysis = {
            "affected_components": ["service_a", "service_b", "database", "frontend"],
            "dependency_depth": 3,
            "test_coverage": 0.75
        }
        
        estimate = refactoring_engine.estimate_effort(change_request, impact_analysis)
        
        assert "total_hours" in estimate
        assert "breakdown" in estimate
        assert "confidence_level" in estimate
        assert estimate["total_hours"] > 0
        
        # Check breakdown includes key activities
        breakdown = estimate["breakdown"]
        assert "development" in breakdown
        assert "testing" in breakdown
        assert "deployment" in breakdown
    
    @pytest.mark.asyncio
    async def test_parallel_execution_coordination(self, refactoring_engine):
        """Test coordination of parallel execution"""
        # Create plan with parallel steps
        plan = RefactoringPlan(
            id="test_plan_parallel",
            strategy=RefactoringStrategy.PARALLEL,
            steps=[
                RefactoringStep(
                    id="step_1a",
                    name="Service A update",
                    description="Independent update",
                    order=1,
                    estimated_hours=2,
                    dependencies=[],
                    metadata={"parallel_group": 1}
                ),
                RefactoringStep(
                    id="step_1b",
                    name="Service B update",
                    description="Independent update",
                    order=1,
                    estimated_hours=2,
                    dependencies=[],
                    metadata={"parallel_group": 1}
                ),
                RefactoringStep(
                    id="step_2",
                    name="Integration",
                    description="Depends on both",
                    order=2,
                    estimated_hours=1,
                    dependencies=["step_1a", "step_1b"]
                )
            ],
            total_effort_hours=5,
            risk_assessment={"level": "medium"},
            rollback_plan={}
        )
        
        execution_times = []
        async def mock_execute_with_timing(step):
            start = datetime.now()
            await asyncio.sleep(0.1)  # Simulate work
            execution_times.append({
                "step": step.id,
                "start": start,
                "group": step.metadata.get("parallel_group")
            })
            return True
        
        with patch.object(refactoring_engine, '_execute_step', side_effect=mock_execute_with_timing):
            with patch.object(refactoring_engine, '_validate_step', new_callable=AsyncMock) as mock_validate:
                mock_validate.return_value = ValidationResult(True, ["OK"], [])
                
                result = await refactoring_engine.execute_refactoring(plan)
                
                assert result["success"] == True
                
                # Check that parallel steps started close together
                group_1_times = [t for t in execution_times if t.get("group") == 1]
                assert len(group_1_times) == 2
    
    @pytest.mark.asyncio
    async def test_feature_toggle_lifecycle(self, refactoring_engine):
        """Test feature toggle lifecycle management"""
        change_request = {
            "type": "feature_modification",
            "feature": "payment_processing",
            "description": "Switch from provider A to provider B"
        }
        
        impact = {
            "affected_components": ["payment_service", "order_service"],
            "effort_hours": 80,
            "risk_level": "high"
        }
        
        # Create feature toggle plan
        plan = await refactoring_engine.create_refactoring_plan(
            change_request,
            impact,
            strategy=RefactoringStrategy.FEATURE_TOGGLE
        )
        
        # Verify toggle lifecycle steps
        step_names = [step.name.lower() for step in plan.steps]
        
        # Should have toggle creation
        assert any("create" in name and "toggle" in name for name in step_names)
        
        # Should have implementation behind toggle
        assert any("implement" in name for name in step_names)
        
        # Should have testing with toggle
        assert any("test" in name for name in step_names)
        
        # Should have gradual rollout
        assert any("rollout" in name or "enable" in name for name in step_names)
        
        # Should have cleanup
        assert any("cleanup" in name or "remove" in name for name in step_names)
    
    @pytest.mark.asyncio
    async def test_dependency_aware_scheduling(self, refactoring_engine):
        """Test dependency-aware step scheduling"""
        plan = RefactoringPlan(
            id="test_plan_deps",
            strategy=RefactoringStrategy.INCREMENTAL,
            steps=[
                RefactoringStep("A", "Step A", "", 1, 1, []),
                RefactoringStep("B", "Step B", "", 2, 1, ["A"]),
                RefactoringStep("C", "Step C", "", 2, 1, ["A"]),
                RefactoringStep("D", "Step D", "", 3, 1, ["B", "C"]),
            ],
            total_effort_hours=4,
            risk_assessment={"level": "low"},
            rollback_plan={}
        )
        
        # Get execution order
        execution_order = refactoring_engine.get_execution_order(plan)
        
        # A must come before B and C
        a_index = execution_order.index("A")
        b_index = execution_order.index("B")
        c_index = execution_order.index("C")
        d_index = execution_order.index("D")
        
        assert a_index < b_index
        assert a_index < c_index
        assert b_index < d_index
        assert c_index < d_index
    
    @pytest.mark.asyncio
    async def test_risk_mitigation_strategies(self, refactoring_engine):
        """Test risk mitigation strategy generation"""
        high_risk_change = {
            "type": "architecture_change",
            "description": "Replace entire data layer",
            "scope": "system-wide",
            "criticality": "high"
        }
        
        high_risk_impact = {
            "affected_components": ["all_services"],
            "effort_hours": 500,
            "risk_level": "critical",
            "downtime_required": True
        }
        
        plan = await refactoring_engine.create_refactoring_plan(
            high_risk_change,
            high_risk_impact,
            strategy=RefactoringStrategy.INCREMENTAL
        )
        
        # Should have comprehensive risk mitigation
        assert "mitigation_strategies" in plan.risk_assessment
        strategies = plan.risk_assessment["mitigation_strategies"]
        
        assert len(strategies) > 3  # Multiple strategies for critical risk
        
        # Check for specific mitigation approaches
        strategy_types = [s.get("type", "") for s in strategies]
        assert any("backup" in t.lower() for t in strategy_types)
        assert any("rollback" in t.lower() for t in strategy_types)
        assert any("test" in t.lower() or "validation" in t.lower() for t in strategy_types)
    
    @pytest.mark.asyncio
    async def test_immigration_system_refactoring(self, refactoring_engine):
        """Test refactoring for immigration system specific changes"""
        # Real-world change from immigration PRD
        change_request = {
            "type": "feature_addition",
            "description": "Add multi-language support to AI dialogue",
            "requirements": {
                "current": {
                    "languages": ["English"],
                    "ai_dialogue": ["pathway_exploration", "form_guidance"]
                },
                "target": {
                    "languages": ["English", "French", "Chinese"],
                    "ai_dialogue": ["pathway_exploration", "form_guidance", "multilingual_processing"],
                    "translation": ["real_time_translation", "context_preservation"]
                }
            }
        }
        
        impact = {
            "affected_components": ["ai_dialogue_service", "nlp_processor", "frontend", "database"],
            "effort_hours": 240,
            "risk_level": "medium",
            "dependencies": {
                "ai_dialogue_service": ["openai_api", "translation_service"],
                "translation_service": ["google_translate_api", "custom_glossary"]
            }
        }
        
        plan = await refactoring_engine.create_refactoring_plan(
            change_request,
            impact,
            strategy=RefactoringStrategy.INCREMENTAL
        )
        
        # Verify plan addresses language-specific concerns
        step_descriptions = [step.description.lower() for step in plan.steps]
        
        assert any("translation" in desc for desc in step_descriptions)
        assert any("language" in desc or "multilingual" in desc for desc in step_descriptions)
        assert any("test" in desc for desc in step_descriptions)
        
        # Should have proper ordering for language features
        translation_steps = [i for i, step in enumerate(plan.steps) 
                           if "translation" in step.name.lower()]
        ai_update_steps = [i for i, step in enumerate(plan.steps)
                          if "ai" in step.name.lower() and "update" in step.name.lower()]
        
        if translation_steps and ai_update_steps:
            # Translation infrastructure should come before AI updates
            assert min(translation_steps) < max(ai_update_steps)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
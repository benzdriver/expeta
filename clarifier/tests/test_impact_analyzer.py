"""
Comprehensive tests for ImpactAnalyzer
"""

import pytest
import json
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from clarifier.core import ImpactAnalyzer, ChangeImpactAnalyzer
from clarifier.core.impact_analyzer import (
    ComponentType, DependencyType, Component, Dependency,
    ChangeType, ChangeImpact, ImpactLevel
)


class TestImpactAnalyzer:
    """Test ImpactAnalyzer functionality"""
    
    @pytest.fixture
    def analyzer(self):
        """Create ImpactAnalyzer instance"""
        return ImpactAnalyzer()
    
    @pytest.fixture
    def ecommerce_components(self):
        """E-commerce system components"""
        return {
            "user_service": {
                "type": ComponentType.SERVICE,
                "dependencies": ["database", "auth_service"],
                "features": ["user_registration", "user_profile"]
            },
            "product_service": {
                "type": ComponentType.SERVICE,
                "dependencies": ["database", "search_service"],
                "features": ["product_catalog", "inventory"]
            },
            "order_service": {
                "type": ComponentType.SERVICE,
                "dependencies": ["database", "user_service", "product_service", "payment_gateway"],
                "features": ["order_creation", "order_tracking"]
            },
            "payment_gateway": {
                "type": ComponentType.EXTERNAL_API,
                "dependencies": [],
                "features": ["payment_processing", "refunds"]
            },
            "database": {
                "type": ComponentType.DATABASE,
                "dependencies": [],
                "features": ["data_storage", "transactions"]
            },
            "auth_service": {
                "type": ComponentType.LIBRARY,
                "dependencies": ["database"],
                "features": ["authentication", "authorization"]
            },
            "search_service": {
                "type": ComponentType.SERVICE,
                "dependencies": ["database"],
                "features": ["full_text_search", "filtering"]
            }
        }
    
    @pytest.fixture
    def immigration_components(self):
        """Immigration system components from PRD"""
        return {
            "ai_dialogue": {
                "type": ComponentType.SERVICE,
                "dependencies": ["openai_api", "conversation_store"],
                "features": ["pathway_exploration", "requirement_gathering"]
            },
            "form_generator": {
                "type": ComponentType.SERVICE,
                "dependencies": ["template_engine", "validation_service"],
                "features": ["dynamic_forms", "pdf_generation"]
            },
            "document_processor": {
                "type": ComponentType.SERVICE,
                "dependencies": ["ocr_service", "storage_service"],
                "features": ["document_upload", "data_extraction"]
            },
            "consultant_matching": {
                "type": ComponentType.SERVICE,
                "dependencies": ["consultant_db", "matching_algorithm"],
                "features": ["consultant_search", "appointment_booking"]
            },
            "openai_api": {
                "type": ComponentType.EXTERNAL_API,
                "dependencies": [],
                "features": ["nlp_processing", "content_generation"]
            },
            "storage_service": {
                "type": ComponentType.INFRASTRUCTURE,
                "dependencies": ["s3_bucket"],
                "features": ["file_storage", "retrieval"]
            }
        }
    
    def test_build_dependency_graph(self, analyzer, ecommerce_components):
        """Test dependency graph building"""
        # Build graph from components
        for name, config in ecommerce_components.items():
            analyzer.add_component(
                name=name,
                component_type=config["type"],
                dependencies=config["dependencies"],
                metadata={"features": config["features"]}
            )
        
        # Verify graph structure
        assert analyzer.has_component("order_service")
        assert analyzer.has_component("database")
        
        # Check dependencies
        order_deps = analyzer.get_dependencies("order_service")
        assert "user_service" in order_deps
        assert "product_service" in order_deps
        assert "payment_gateway" in order_deps
        assert "database" in order_deps
    
    def test_analyze_change_impact(self, analyzer, ecommerce_components):
        """Test change impact analysis"""
        # Build dependency graph
        for name, config in ecommerce_components.items():
            analyzer.add_component(name, config["type"], config["dependencies"])
        
        # Analyze impact of database change
        change = {
            "type": ChangeType.SCHEMA_CHANGE,
            "component": "database",
            "description": "Add new index for performance"
        }
        
        impact = analyzer.analyze_change_impact(change)
        
        # All services depending on database should be affected
        affected_components = [imp.component for imp in impact.affected_components]
        assert "user_service" in affected_components
        assert "product_service" in affected_components
        assert "order_service" in affected_components
        assert "auth_service" in affected_components
        assert "search_service" in affected_components
    
    def test_transitive_impact_analysis(self, analyzer, ecommerce_components):
        """Test transitive dependency impact"""
        # Build graph
        for name, config in ecommerce_components.items():
            analyzer.add_component(name, config["type"], config["dependencies"])
        
        # Change in auth_service should affect user_service and order_service
        change = {
            "type": ChangeType.API_CHANGE,
            "component": "auth_service",
            "description": "Update authentication method"
        }
        
        impact = analyzer.analyze_change_impact(change)
        affected = [imp.component for imp in impact.affected_components]
        
        # Direct impact
        assert "user_service" in affected
        
        # Transitive impact (order_service depends on user_service)
        assert "order_service" in affected
    
    def test_effort_estimation(self, analyzer, immigration_components):
        """Test effort estimation for changes"""
        # Build immigration system graph
        for name, config in immigration_components.items():
            analyzer.add_component(
                name, 
                config["type"], 
                config["dependencies"],
                metadata={"features": config["features"]}
            )
        
        # Major change in AI dialogue
        change = {
            "type": ChangeType.FEATURE_ADDITION,
            "component": "ai_dialogue",
            "description": "Add multilingual support",
            "complexity": "high"
        }
        
        estimation = analyzer.estimate_effort(change)
        
        assert estimation["total_effort_hours"] > 0
        assert estimation["affected_components_count"] > 0
        assert "breakdown" in estimation
        assert "risk_factors" in estimation
    
    def test_find_impacted_features(self, analyzer, ecommerce_components):
        """Test finding impacted features"""
        # Build graph with feature metadata
        for name, config in ecommerce_components.items():
            analyzer.add_component(
                name,
                config["type"],
                config["dependencies"],
                metadata={"features": config["features"]}
            )
        
        # Find features impacted by payment gateway change
        change = {
            "type": ChangeType.API_CHANGE,
            "component": "payment_gateway",
            "description": "Update payment API version"
        }
        
        impacted_features = analyzer.find_impacted_features(change)
        
        # Should impact order creation and tracking
        assert "order_creation" in impacted_features
        assert "order_tracking" in impacted_features
        assert "payment_processing" in impacted_features
        assert "refunds" in impacted_features
    
    def test_suggest_refactoring_approach(self, analyzer, ecommerce_components):
        """Test refactoring approach suggestions"""
        # Build graph
        for name, config in ecommerce_components.items():
            analyzer.add_component(name, config["type"], config["dependencies"])
        
        # Complex change requiring refactoring
        change = {
            "type": ChangeType.ARCHITECTURE_CHANGE,
            "component": "database",
            "description": "Migrate from SQL to NoSQL",
            "scope": "system-wide"
        }
        
        suggestions = analyzer.suggest_refactoring_approach(change)
        
        assert "approach" in suggestions
        assert "phases" in suggestions
        assert "risks" in suggestions
        assert "mitigation_strategies" in suggestions
        assert len(suggestions["phases"]) > 0
    
    def test_circular_dependency_detection(self, analyzer):
        """Test circular dependency detection"""
        # Create circular dependency
        analyzer.add_component("service_a", ComponentType.SERVICE, ["service_b"])
        analyzer.add_component("service_b", ComponentType.SERVICE, ["service_c"])
        analyzer.add_component("service_c", ComponentType.SERVICE, ["service_a"])
        
        # Check for circular dependencies
        cycles = analyzer.detect_circular_dependencies()
        
        assert len(cycles) > 0
        cycle = cycles[0]
        assert len(cycle) == 3
        assert all(s in cycle for s in ["service_a", "service_b", "service_c"])
    
    def test_component_coupling_analysis(self, analyzer, ecommerce_components):
        """Test component coupling analysis"""
        # Build graph
        for name, config in ecommerce_components.items():
            analyzer.add_component(name, config["type"], config["dependencies"])
        
        # Analyze coupling
        coupling = analyzer.analyze_component_coupling()
        
        # Order service should have high coupling (many dependencies)
        assert coupling["order_service"]["afferent_coupling"] >= 0
        assert coupling["order_service"]["efferent_coupling"] > 3
        
        # Database should have high afferent coupling (many depend on it)
        assert coupling["database"]["afferent_coupling"] > 4
        assert coupling["database"]["efferent_coupling"] == 0
    
    def test_critical_path_identification(self, analyzer, immigration_components):
        """Test critical path identification"""
        # Build graph
        for name, config in immigration_components.items():
            analyzer.add_component(name, config["type"], config["dependencies"])
        
        # Find critical paths
        critical_paths = analyzer.find_critical_paths()
        
        assert len(critical_paths) > 0
        
        # OpenAI API should be in critical path (many depend on it)
        ai_critical = any("openai_api" in path for path in critical_paths)
        assert ai_critical
    
    def test_impact_visualization(self, analyzer, ecommerce_components):
        """Test impact visualization generation"""
        # Build graph
        for name, config in ecommerce_components.items():
            analyzer.add_component(name, config["type"], config["dependencies"])
        
        # Generate visualization data
        change = {
            "type": ChangeType.API_CHANGE,
            "component": "payment_gateway",
            "description": "Update payment API"
        }
        
        viz_data = analyzer.visualize_impact(change)
        
        assert "nodes" in viz_data
        assert "edges" in viz_data
        assert "impacted_nodes" in viz_data
        
        # Payment gateway and order service should be marked as impacted
        impacted_ids = [n["id"] for n in viz_data["impacted_nodes"]]
        assert "payment_gateway" in impacted_ids
        assert "order_service" in impacted_ids
    
    def test_parallel_change_analysis(self, analyzer, ecommerce_components):
        """Test analyzing multiple parallel changes"""
        # Build graph
        for name, config in ecommerce_components.items():
            analyzer.add_component(name, config["type"], config["dependencies"])
        
        # Multiple parallel changes
        changes = [
            {
                "type": ChangeType.FEATURE_ADDITION,
                "component": "user_service",
                "description": "Add social login"
            },
            {
                "type": ChangeType.API_CHANGE,
                "component": "product_service",
                "description": "Update product API"
            }
        ]
        
        # Analyze combined impact
        combined_impact = analyzer.analyze_parallel_changes(changes)
        
        assert combined_impact["total_affected_components"] > 2
        assert "conflict_analysis" in combined_impact
        assert "recommended_sequence" in combined_impact
    
    def test_rollback_impact_analysis(self, analyzer, ecommerce_components):
        """Test rollback impact analysis"""
        # Build graph
        for name, config in ecommerce_components.items():
            analyzer.add_component(name, config["type"], config["dependencies"])
        
        # Analyze rollback impact
        change_to_rollback = {
            "type": ChangeType.FEATURE_REMOVAL,
            "component": "search_service",
            "description": "Remove advanced search features"
        }
        
        rollback_impact = analyzer.analyze_rollback_impact(change_to_rollback)
        
        assert "safe_to_rollback" in rollback_impact
        assert "affected_by_rollback" in rollback_impact
        assert "rollback_steps" in rollback_impact
        assert len(rollback_impact["rollback_steps"]) > 0
    
    def test_component_health_assessment(self, analyzer, ecommerce_components):
        """Test component health assessment"""
        # Build graph with additional metadata
        for name, config in ecommerce_components.items():
            analyzer.add_component(
                name,
                config["type"],
                config["dependencies"],
                metadata={
                    "features": config["features"],
                    "last_modified": "2024-01-01",
                    "test_coverage": 0.8 if name != "payment_gateway" else 0.3,
                    "bug_count": 2 if name == "order_service" else 0
                }
            )
        
        # Assess health
        health_report = analyzer.assess_component_health()
        
        # Payment gateway should have low health (low test coverage)
        assert health_report["payment_gateway"]["health_score"] < 0.5
        assert "low test coverage" in str(health_report["payment_gateway"]["issues"])
        
        # Database should have good health (no bugs, good coverage)
        assert health_report["database"]["health_score"] > 0.7
    
    def test_migration_planning(self, analyzer):
        """Test migration planning for architecture changes"""
        # Build microservices architecture
        services = [
            ("api_gateway", ["auth", "user", "product", "order"]),
            ("auth", ["user_db"]),
            ("user", ["user_db", "cache"]),
            ("product", ["product_db", "cache", "search"]),
            ("order", ["order_db", "user", "product", "payment"]),
            ("payment", ["payment_provider"]),
            ("cache", []),
            ("search", ["elasticsearch"]),
        ]
        
        for service, deps in services:
            analyzer.add_component(service, ComponentType.SERVICE, deps)
        
        # Plan migration from monolith to microservices
        migration_plan = analyzer.plan_migration({
            "from": "monolith",
            "to": "microservices",
            "components_to_extract": ["user", "product", "order"],
            "timeline": "6 months"
        })
        
        assert "phases" in migration_plan
        assert len(migration_plan["phases"]) > 0
        assert "dependencies_to_break" in migration_plan
        assert "risk_assessment" in migration_plan
        assert "rollback_plan" in migration_plan
    
    def test_performance_impact_analysis(self, analyzer, immigration_components):
        """Test performance impact analysis"""
        # Build graph with performance metadata
        for name, config in immigration_components.items():
            analyzer.add_component(
                name,
                config["type"],
                config["dependencies"],
                metadata={
                    "features": config["features"],
                    "response_time_ms": 100 if "api" not in name else 500,
                    "throughput_rps": 1000 if name != "ocr_service" else 10
                }
            )
        
        # Analyze performance impact of change
        change = {
            "type": ChangeType.PERFORMANCE_OPTIMIZATION,
            "component": "openai_api",
            "description": "Add caching layer",
            "expected_improvement": "50% reduction in response time"
        }
        
        perf_impact = analyzer.analyze_performance_impact(change)
        
        assert "current_bottlenecks" in perf_impact
        assert "expected_improvements" in perf_impact
        assert "downstream_benefits" in perf_impact
        assert len(perf_impact["downstream_benefits"]) > 0


class TestChangeImpactAnalyzer:
    """Test ChangeImpactAnalyzer functionality"""
    
    @pytest.fixture
    def change_analyzer(self):
        """Create ChangeImpactAnalyzer instance"""
        return ChangeImpactAnalyzer()
    
    def test_analyze_requirement_change(self, change_analyzer):
        """Test requirement change analysis"""
        current_requirements = {
            "functional": {
                "user_management": ["login", "register", "profile"],
                "payment": ["credit_card", "paypal"],
                "notifications": ["email"]
            },
            "non_functional": {
                "performance": "response_time < 2s",
                "security": "OAuth2",
                "scalability": "1000 concurrent users"
            }
        }
        
        proposed_change = {
            "type": "feature_addition",
            "category": "functional",
            "component": "notifications",
            "change": "Add SMS and push notifications"
        }
        
        impact = change_analyzer.analyze_requirement_change(
            current_requirements,
            proposed_change
        )
        
        assert impact.level in [ImpactLevel.MEDIUM, ImpactLevel.HIGH]
        assert len(impact.affected_areas) > 0
        assert "notifications" in impact.affected_areas
        assert impact.effort_estimate > 0
        assert len(impact.risks) > 0
    
    def test_dependency_chain_analysis(self, change_analyzer):
        """Test dependency chain analysis"""
        dependencies = {
            "frontend": ["api_gateway"],
            "api_gateway": ["auth_service", "business_logic"],
            "auth_service": ["user_database"],
            "business_logic": ["main_database", "cache"],
            "main_database": [],
            "cache": [],
            "user_database": []
        }
        
        # Change in auth service
        chains = change_analyzer.analyze_dependency_chains(
            "auth_service",
            dependencies
        )
        
        # Should find chains through auth_service
        assert len(chains) > 0
        
        # Verify chain from frontend to auth_service exists
        frontend_chain = next(
            (c for c in chains if c[0] == "frontend" and "auth_service" in c),
            None
        )
        assert frontend_chain is not None
    
    def test_risk_assessment(self, change_analyzer):
        """Test risk assessment for changes"""
        change = {
            "type": ChangeType.ARCHITECTURE_CHANGE,
            "description": "Migrate from REST to GraphQL",
            "scope": "all APIs",
            "timeline": "3 months"
        }
        
        risks = change_analyzer.assess_risks(change)
        
        assert len(risks) > 0
        
        # Should identify migration risks
        risk_categories = [r["category"] for r in risks]
        assert "technical" in risk_categories
        assert "timeline" in risk_categories
        assert "compatibility" in risk_categories
        
        # Each risk should have mitigation strategies
        for risk in risks:
            assert "mitigation" in risk
            assert len(risk["mitigation"]) > 0
    
    def test_multi_version_impact(self, change_analyzer):
        """Test impact across multiple versions"""
        version_features = {
            "v1.0": ["basic_auth", "simple_ui"],
            "v1.5": ["oauth", "responsive_ui", "api_v1"],
            "v2.0": ["oauth", "modern_ui", "api_v2", "websockets"]
        }
        
        change = {
            "component": "authentication",
            "change": "Replace OAuth with SAML",
            "affects": ["oauth"]
        }
        
        version_impacts = change_analyzer.analyze_version_impacts(
            change,
            version_features
        )
        
        # v1.0 should not be affected
        assert version_impacts["v1.0"]["affected"] == False
        
        # v1.5 and v2.0 should be affected
        assert version_impacts["v1.5"]["affected"] == True
        assert version_impacts["v2.0"]["affected"] == True
        assert "oauth" in version_impacts["v1.5"]["impacted_features"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
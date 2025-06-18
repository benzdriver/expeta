"""
Comprehensive test suite for all Clarifier components
"""

import pytest
import asyncio
from pathlib import Path
import json
from typing import Dict, Any, List

from clarifier.core import (
    BlindSpotDetector,
    VersionManager,
    ImpactAnalyzer,
    SmartRefactoring,
    ClarifierOrchestrator,
    BlindSpotType
)


class TestClarifierIntegrationComplete:
    """Complete integration tests for Clarifier system"""
    
    @pytest.fixture
    def all_components(self):
        """Initialize all components"""
        return {
            "detector": BlindSpotDetector(),
            "version_manager": VersionManager(),
            "impact_analyzer": ImpactAnalyzer(),
            "refactoring": SmartRefactoring(),
            "orchestrator": ClarifierOrchestrator()
        }
    
    @pytest.fixture 
    def load_real_prds(self):
        """Load all real PRD files"""
        prds = {}
        input_dir = Path("/Users/ziyanzhou/Projects/expeta/data/input")
        
        # Load immigration PRD
        immigration_path = input_dir / "requirement-md.md"
        if immigration_path.exists():
            prds["immigration"] = immigration_path.read_text(encoding='utf-8')
        
        # Load technical architecture
        tech_path = input_dir / "technical-architecture.md" 
        if tech_path.exists():
            prds["technical"] = tech_path.read_text(encoding='utf-8')
            
        return prds
    
    @pytest.mark.asyncio
    async def test_full_workflow_with_real_data(self, all_components, load_real_prds):
        """Test complete workflow with real PRD data"""
        if "immigration" not in load_real_prds:
            pytest.skip("Real PRD files not found")
            
        orchestrator = all_components["orchestrator"]
        prd = load_real_prds["immigration"]
        
        # Step 1: Start session and detect blind spots
        session_id, initial_result = await orchestrator.start_clarification_session(
            prd_content=prd,
            mode=ClarifierMode.INTERACTIVE,
            context={
                "project_type": "saas",
                "domain": "immigration", 
                "market": "Canada"
            }
        )
        
        assert session_id is not None
        assert initial_result['total_blind_spots'] > 0
        
        # Step 2: Process multiple clarifications
        clarifications_processed = 0
        max_clarifications = 5
        quality_improvements = []
        
        while (clarifications_processed < max_clarifications and
               initial_result.get('next_action', {}).get('type') == 'clarification_needed'):
            
            blind_spot = initial_result['next_action']['blind_spot']
            
            # Create detailed clarification based on blind spot type
            clarification_text = self._generate_clarification_response(blind_spot)
            
            clarification = ClarificationRequest(
                blind_spot_id=blind_spot['id'],
                user_response=clarification_text
            )
            
            result = await orchestrator.process_clarification(session_id, clarification)
            
            quality_improvements.append(result.get('quality_improvement', 0))
            clarifications_processed += 1
            
            # Get next action
            if result.get('next_action'):
                initial_result = result
            else:
                break
        
        # Step 3: Generate final structured summary
        final_summary = await orchestrator.generate_structured_summary(prd)
        
        # Verify quality improvements
        assert sum(quality_improvements) > 0
        assert final_summary['quality_score'] >= 70
        
        # Step 4: Simulate requirement change
        change_request = {
            "type": "feature_addition",
            "description": "Add AI-powered document verification",
            "details": {
                "feature": "Document Verification AI",
                "requirements": [
                    "Automatic document authenticity check",
                    "AI-based information extraction",
                    "Cross-reference with government databases",
                    "Fraud detection algorithms"
                ]
            }
        }
        
        impact_result = await orchestrator.handle_requirement_change(
            change_request,
            auto_execute=False
        )
        
        assert impact_result['status'] == 'pending_confirmation'
        assert impact_result['estimated_effort'] > 0
        
        # Step 5: Verify version history
        history = orchestrator.get_version_history(limit=10)
        assert len(history) >= clarifications_processed + 1  # Initial + clarifications
        
        # Step 6: Export and verify reports
        json_report = orchestrator.export_session_report(session_id, format="json")
        report_data = json.loads(json_report)
        
        assert report_data['session_id'] == session_id
        assert report_data['total_clarifications'] == clarifications_processed
        assert 'quality_progression' in report_data
    
    def _generate_clarification_response(self, blind_spot: Dict[str, Any]) -> str:
        """Generate appropriate clarification response based on blind spot type"""
        responses = {
            "security": """
            Security Implementation:
            1. End-to-end encryption using AES-256 for data at rest
            2. TLS 1.3 for all data in transit
            3. Multi-factor authentication with TOTP/SMS/Biometric options
            4. Role-based access control with fine-grained permissions
            5. Regular security audits and penetration testing
            6. SIEM integration for real-time threat detection
            7. Compliance with GDPR, PIPEDA, and SOC2 standards
            """,
            
            "performance": """
            Performance Specifications:
            1. Response time: p50 < 100ms, p95 < 200ms, p99 < 500ms
            2. Throughput: 10,000 requests/second sustained
            3. Concurrent users: 50,000 active sessions
            4. Database queries: Optimized with proper indexing, < 50ms
            5. Caching: Redis with 90% cache hit rate
            6. CDN: Global distribution for static assets
            7. Auto-scaling: Horizontal scaling based on CPU/memory metrics
            """,
            
            "error_handling": """
            Error Handling Strategy:
            1. Graceful degradation for non-critical features
            2. Automatic retry with exponential backoff (3 attempts max)
            3. Circuit breaker pattern for external services
            4. Comprehensive error logging with correlation IDs
            5. User-friendly error messages in multiple languages
            6. Fallback mechanisms for critical paths
            7. Error recovery procedures with data consistency checks
            """,
            
            "scalability": """
            Scalability Architecture:
            1. Microservices architecture with container orchestration
            2. Database sharding by user geography
            3. Event-driven architecture with message queues
            4. Stateless services for horizontal scaling
            5. Read replicas for database load distribution
            6. Caching at multiple layers (CDN, API, Database)
            7. Load testing for 10x current capacity
            """
        }
        
        # Find matching response type
        blind_spot_type = blind_spot.get('type', '').lower()
        for key, response in responses.items():
            if key in blind_spot_type:
                return response
        
        # Default response
        return """
        Comprehensive Implementation Details:
        1. Detailed technical specifications following industry best practices
        2. Phased implementation approach with clear milestones
        3. Comprehensive testing strategy including unit, integration, and E2E tests
        4. Monitoring and alerting for all critical components
        5. Documentation for developers, operators, and end users
        6. Training materials and knowledge transfer sessions
        7. Post-deployment support and maintenance procedures
        """
    
    @pytest.mark.asyncio
    async def test_blind_spot_detection_coverage(self, all_components):
        """Test blind spot detection covers all types"""
        detector = all_components["detector"]
        
        # Test with various PRD types
        test_prds = {
            "minimal": "Build a web application",
            "ecommerce": """
                E-commerce Platform:
                - Product catalog
                - Shopping cart
                - Payment processing
                - Order management
            """,
            "saas": """
                SaaS Analytics Platform:
                - Data ingestion from multiple sources
                - Real-time analytics dashboard
                - User management and billing
                - API for third-party integrations
            """,
            "mobile": """
                Mobile Banking App:
                - Account management
                - Fund transfers
                - Bill payments
                - Biometric authentication
            """
        }
        
        all_blind_spot_types = set()
        
        for prd_type, prd_content in test_prds.items():
            blind_spots = await detector.detect_blind_spots(
                prd_content,
                context={"project_type": prd_type}
            )
            
            # Collect all blind spot types found
            for bs in blind_spots:
                all_blind_spot_types.add(bs.type)
        
        # Verify coverage of blind spot types
        expected_types = {
            BlindSpotType.EDGE_CASE,
            BlindSpotType.SECURITY,
            BlindSpotType.PERFORMANCE,
            BlindSpotType.ERROR_HANDLING,
            BlindSpotType.SCALABILITY
        }
        
        assert len(all_blind_spot_types.intersection(expected_types)) >= 4
    
    @pytest.mark.asyncio
    async def test_version_management_completeness(self, all_components):
        """Test version management features"""
        vm = all_components["version_manager"]
        
        # Create version tree
        v1 = vm.initialize_with_prd("Initial PRD", {"version": 1})
        
        # Create branches
        feature_branch = vm.requirement_version.create_branch(v1, "feature/new-ui")
        bugfix_branch = vm.requirement_version.create_branch(v1, "bugfix/security-patch")
        
        # Make changes on branches
        v2_feature = vm.save_blind_spot_clarification(
            "Updated UI PRD",
            {"version": 1, "ui": "new"},
            "BS_UI",
            "Redesigned UI"
        )
        
        v2_bugfix = vm.save_blind_spot_clarification(
            "Security patches PRD",
            {"version": 1, "security": "patched"},
            "BS_SEC",
            "Security fixes"
        )
        
        # Test merge
        merged = vm.requirement_version.merge_versions(v2_feature, v2_bugfix)
        
        # Verify merge
        merged_version = vm.requirement_version.get_version(merged)
        assert "ui" in merged_version.json_summary
        assert "security" in merged_version.json_summary
        
        # Test version search
        results = vm.requirement_version.search_versions("security")
        assert len(results) > 0
        
        # Test statistics
        stats = vm.requirement_version.get_version_statistics()
        assert stats["total_versions"] >= 5
        assert stats["total_branches"] >= 2
    
    @pytest.mark.asyncio
    async def test_impact_analysis_accuracy(self, all_components):
        """Test impact analysis accuracy"""
        impact = all_components["impact_analyzer"]
        
        # Build realistic system
        components = {
            "web_frontend": ["api_gateway"],
            "mobile_frontend": ["api_gateway"],
            "api_gateway": ["auth_service", "user_service", "payment_service"],
            "auth_service": ["user_db", "redis_cache"],
            "user_service": ["user_db", "notification_service"],
            "payment_service": ["payment_gateway", "order_db"],
            "notification_service": ["email_provider", "sms_provider"],
            "user_db": [],
            "order_db": [],
            "redis_cache": []
        }
        
        # Add components
        for comp, deps in components.items():
            impact.add_component(comp, ComponentType.SERVICE, deps)
        
        # Test various changes
        test_changes = [
            {
                "change": {"component": "user_db", "type": ChangeType.SCHEMA_CHANGE},
                "expected_affected": ["auth_service", "user_service", "api_gateway", "web_frontend", "mobile_frontend"]
            },
            {
                "change": {"component": "payment_gateway", "type": ChangeType.API_CHANGE},
                "expected_affected": ["payment_service", "api_gateway", "web_frontend", "mobile_frontend"]
            }
        ]
        
        for test in test_changes:
            result = impact.analyze_change_impact(test["change"])
            affected = [c.component for c in result.affected_components]
            
            for expected in test["expected_affected"]:
                assert expected in affected
    
    @pytest.mark.asyncio
    async def test_refactoring_strategies(self, all_components):
        """Test all refactoring strategies"""
        refactoring = all_components["refactoring"]
        
        strategies = [
            RefactoringStrategy.INCREMENTAL,
            RefactoringStrategy.BIG_BANG,
            RefactoringStrategy.PARALLEL,
            RefactoringStrategy.FEATURE_TOGGLE
        ]
        
        change_request = {
            "type": "architecture_change",
            "description": "Migrate to microservices"
        }
        
        impact_analysis = {
            "affected_components": ["all"],
            "effort_hours": 1000,
            "risk_level": "high"
        }
        
        plans = {}
        for strategy in strategies:
            plan = await refactoring.create_refactoring_plan(
                change_request,
                impact_analysis,
                strategy=strategy
            )
            plans[strategy] = plan
            
            assert plan.strategy == strategy
            assert len(plan.steps) > 0
            assert plan.risk_assessment is not None
        
        # Verify different strategies have different approaches
        assert plans[RefactoringStrategy.INCREMENTAL].steps[0].name != \
               plans[RefactoringStrategy.BIG_BANG].steps[0].name


class TestClarifierPerformance:
    """Performance tests for Clarifier system"""
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_prd_processing(self):
        """Test processing of large PRDs"""
        orchestrator = ClarifierOrchestrator()
        
        # Generate large PRD
        large_prd = "# Large System Specification\n\n"
        for i in range(100):
            large_prd += f"""
            ## Module {i}
            
            ### Features
            - Feature A{i}: Complex functionality with multiple components
            - Feature B{i}: Integration with external systems
            - Feature C{i}: Real-time processing requirements
            
            ### Requirements  
            - Performance: Must handle {1000 * (i+1)} requests per second
            - Security: Implement authentication and authorization
            - Scalability: Support horizontal scaling
            
            """
        
        import time
        start_time = time.time()
        
        session_id, result = await orchestrator.start_clarification_session(
            prd_content=large_prd,
            mode=ClarifierMode.QUICK_CHECK
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time
        assert processing_time < 30  # 30 seconds for large PRD
        assert result['total_blind_spots'] > 0
    
    @pytest.mark.slow
    @pytest.mark.asyncio  
    async def test_concurrent_sessions(self):
        """Test handling multiple concurrent sessions"""
        orchestrator = ClarifierOrchestrator()
        
        async def create_session(index):
            prd = f"System {index}: Basic requirements for testing"
            session_id, result = await orchestrator.start_clarification_session(
                prd_content=prd,
                mode=ClarifierMode.QUICK_CHECK
            )
            return session_id
        
        # Create 10 concurrent sessions
        tasks = [create_session(i) for i in range(10)]
        session_ids = await asyncio.gather(*tasks)
        
        # All sessions should be created successfully
        assert len(session_ids) == 10
        assert len(set(session_ids)) == 10  # All unique
        
        # Each session should be accessible
        for session_id in session_ids:
            status = orchestrator.get_session_status(session_id)
            assert status is not None
            assert status['session_id'] == session_id


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
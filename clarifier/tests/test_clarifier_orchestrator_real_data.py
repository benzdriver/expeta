"""
Tests for ClarifierOrchestrator using real PRD data
"""

import pytest
import asyncio
import json
from pathlib import Path
from typing import Dict, Any

from clarifier.core import ClarifierOrchestrator
from clarifier.core.clarifier_orchestrator import ClarifierMode, ClarificationRequest


class TestClarifierOrchestratorWithRealData:
    """Test ClarifierOrchestrator with real PRD data"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return ClarifierOrchestrator()
    
    @pytest.fixture
    def immigration_prd(self):
        """Load real immigration PRD"""
        prd_path = Path("/Users/ziyanzhou/Projects/expeta/data/input/requirement-md.md")
        if prd_path.exists():
            return prd_path.read_text(encoding='utf-8')
        else:
            # Fallback content if file not found
            return """
            # ThinkForward AI - Immigration Platform
            
            ## System Overview
            ThinkForward AI is a SaaS platform for Canadian immigration applications.
            
            ## Features
            1. AI-Guided Form Filling
            2. Document Management
            3. Consultant Matching
            4. Multi-language Support (English, French, Chinese)
            """
    
    @pytest.fixture
    def technical_architecture(self):
        """Load technical architecture document"""
        arch_path = Path("/Users/ziyanzhou/Projects/expeta/data/input/technical-architecture.md")
        if arch_path.exists():
            return arch_path.read_text(encoding='utf-8')
        else:
            return """
            # Technical Architecture
            
            ## Technology Stack
            - Frontend: Next.js + React
            - Backend: Node.js Serverless
            - Database: MongoDB Atlas
            - AI: OpenAI API
            """
    
    @pytest.mark.asyncio
    async def test_immigration_prd_blind_spot_detection(self, orchestrator, immigration_prd):
        """Test blind spot detection on real immigration PRD"""
        session_id, result = await orchestrator.start_clarification_session(
            prd_content=immigration_prd,
            mode=ClarifierMode.INTERACTIVE,
            context={
                "project_type": "saas",
                "domain": "immigration",
                "target_market": "Canada"
            }
        )
        
        assert session_id is not None
        assert result['total_blind_spots'] > 0
        
        # Should detect immigration-specific blind spots
        blind_spots_summary = result['blind_spots_summary']
        
        # Check for critical blind spots
        critical_types = ['security', 'compliance', 'data_management']
        found_critical = False
        for bs_type, blind_spots in blind_spots_summary.items():
            if bs_type in critical_types and len(blind_spots) > 0:
                found_critical = True
                break
        assert found_critical, "Should detect critical blind spots for immigration system"
        
        # Should detect multi-language challenges
        all_blind_spots = []
        for bs_list in blind_spots_summary.values():
            all_blind_spots.extend(bs_list)
        
        language_related = [bs for bs in all_blind_spots 
                          if any(term in bs.lower() 
                                for term in ['language', 'translation', 'localization', 'multilingual'])]
        assert len(language_related) > 0, "Should detect language-related blind spots"
    
    @pytest.mark.asyncio
    async def test_immigration_prd_auto_enhancement(self, orchestrator, immigration_prd):
        """Test PRD auto-enhancement for immigration system"""
        session_id, result = await orchestrator.start_clarification_session(
            prd_content=immigration_prd,
            mode=ClarifierMode.PRD_ANALYSIS
        )
        
        assert result['next_action']['type'] == 'auto_enhanced'
        assert result['next_action']['blind_spots_addressed'] > 0
        
        # Get enhanced version
        enhanced_version_id = result['next_action']['enhanced_version']
        enhanced_version = orchestrator.version_manager.requirement_version.get_version(enhanced_version_id)
        
        # Check enhancements
        enhanced_prd = enhanced_version.prd_content
        enhanced_summary = enhanced_version.json_summary
        
        # Should add security considerations
        assert any(term in enhanced_prd.lower() 
                  for term in ['encryption', 'security', 'privacy', 'gdpr', 'pipeda'])
        
        # Should add performance specifications
        assert any(term in enhanced_prd.lower()
                  for term in ['performance', 'scalability', 'load', 'concurrent'])
        
        # Should enhance error handling
        assert any(term in enhanced_prd.lower()
                  for term in ['error', 'exception', 'failure', 'retry'])
    
    @pytest.mark.asyncio
    async def test_structured_summary_generation_quality(self, orchestrator, immigration_prd):
        """Test quality of structured summary generation"""
        # Initialize with PRD
        version_id = orchestrator.version_manager.initialize_with_prd(
            immigration_prd,
            {"project": "ThinkForward AI"}
        )
        
        # Generate structured summary
        result = await orchestrator.generate_structured_summary(immigration_prd)
        
        assert result['quality_score'] >= 70
        summary = result['summary']
        
        # Check for required sections
        assert 'technical_architecture' in summary
        assert 'functional_modules' in summary
        assert 'non_functional_requirements' in summary
        assert 'data_models' in summary
        assert 'integration_points' in summary
        
        # Check technical architecture details
        tech_arch = summary['technical_architecture']
        assert 'frontend' in tech_arch
        assert 'backend' in tech_arch
        assert 'database' in tech_arch
        assert 'infrastructure' in tech_arch
        
        # Check functional modules are specific
        modules = summary['functional_modules']
        assert len(modules) > 0
        
        # Each module should have concrete details
        for module in modules:
            assert 'name' in module
            assert 'features' in module
            assert 'apis' in module or 'endpoints' in module
            assert len(module.get('features', [])) > 0
        
        # Check for immigration-specific features
        module_names = [m['name'].lower() for m in modules]
        assert any('form' in name or 'document' in name for name in module_names)
        assert any('ai' in name or 'dialogue' in name for name in module_names)
    
    @pytest.mark.asyncio
    async def test_consultant_feature_clarification(self, orchestrator, immigration_prd):
        """Test clarification specific to consultant features"""
        session_id, result = await orchestrator.start_clarification_session(
            prd_content=immigration_prd,
            mode=ClarifierMode.INTERACTIVE,
            context={
                "focus_area": "consultant_features",
                "user_type": "immigration_consultant"
            }
        )
        
        # Find consultant-related blind spots
        blind_spots = []
        for bs_type, bs_list in result['blind_spots_summary'].items():
            blind_spots.extend([(bs_type, bs) for bs in bs_list])
        
        consultant_blind_spots = [
            (t, bs) for t, bs in blind_spots
            if any(term in bs.lower() 
                  for term in ['consultant', 'client management', 'portfolio', 'collaboration'])
        ]
        
        assert len(consultant_blind_spots) > 0
        
        # Simulate clarification for first consultant blind spot
        if result['next_action']['type'] == 'clarification_needed':
            blind_spot = result['next_action']['blind_spot']
            
            # Provide detailed clarification
            clarification = ClarificationRequest(
                blind_spot_id=blind_spot['id'],
                user_response="""
                For consultant collaboration:
                1. Real-time document co-editing with version control
                2. Secure video conferencing with screen sharing
                3. Task assignment with deadlines and notifications
                4. Client progress dashboard with milestone tracking
                5. Automated report generation for consultant performance
                6. White-label options for consultant branding
                """
            )
            
            clarification_result = await orchestrator.process_clarification(
                session_id, clarification
            )
            
            assert clarification_result['status'] == 'processed'
            assert clarification_result['quality_improvement'] > 0
    
    @pytest.mark.asyncio
    async def test_immigration_requirement_change_impact(self, orchestrator, immigration_prd):
        """Test requirement change impact for immigration system"""
        # Initialize system
        initial_summary = {
            "project_name": "ThinkForward AI",
            "features": [
                "ai_dialogue",
                "form_generation",
                "document_management",
                "consultant_matching"
            ],
            "languages": ["English", "French", "Chinese"]
        }
        
        version_id = orchestrator.version_manager.initialize_with_prd(
            immigration_prd, initial_summary
        )
        
        # Simulate major change: Add Express Entry optimization
        change_request = {
            "type": "feature_addition",
            "description": "Add Express Entry CRS score optimization",
            "details": {
                "feature_name": "CRS Score Optimizer",
                "requirements": [
                    "Real-time CRS score calculation",
                    "Score improvement recommendations",
                    "What-if scenario analysis",
                    "Historical score trends",
                    "Competition analysis"
                ],
                "integration_points": [
                    "AI dialogue system",
                    "User profile data",
                    "Immigration pathway recommendations"
                ]
            }
        }
        
        # Analyze impact
        impact_result = await orchestrator.handle_requirement_change(
            change_request, auto_execute=False
        )
        
        assert impact_result['status'] == 'pending_confirmation'
        assert 'impact_analysis' in impact_result
        assert 'refactoring_plan' in impact_result
        
        # Check impact on existing components
        impact = impact_result['impact_analysis']
        assert impact['affected_components_count'] > 2
        assert impact['estimated_effort'] > 0
        
        # Should affect AI dialogue and form generation
        affected = impact['affected_components']
        affected_names = [c['name'] for c in affected]
        assert any('ai' in name.lower() or 'dialogue' in name.lower() for name in affected_names)
        assert any('form' in name.lower() for name in affected_names)
    
    @pytest.mark.asyncio
    async def test_multi_language_blind_spot_handling(self, orchestrator, immigration_prd):
        """Test handling of multi-language specific blind spots"""
        session_id, result = await orchestrator.start_clarification_session(
            prd_content=immigration_prd,
            mode=ClarifierMode.INTERACTIVE,
            context={
                "focus_area": "multi_language",
                "languages": ["English", "French", "Chinese"]
            }
        )
        
        # Process language-specific clarifications
        clarifications_made = 0
        max_clarifications = 3
        
        while (result['next_action']['type'] == 'clarification_needed' and 
               clarifications_made < max_clarifications):
            
            blind_spot = result['next_action']['blind_spot']
            
            # Check if it's language-related
            if any(term in blind_spot['description'].lower() 
                  for term in ['language', 'translation', 'localization']):
                
                # Provide comprehensive language clarification
                response = """
                Language support implementation:
                1. UI/UX localization: All interface elements translated by professional translators
                2. Content translation: Legal documents use certified translation services
                3. Cultural adaptation: Date formats, currency, address formats per locale
                4. AI dialogue: Supports natural conversation in all three languages
                5. Form generation: Creates language-specific government forms
                6. Error messages: Culturally appropriate error handling
                7. Search: Language-specific search with transliteration support
                8. Fallback: Graceful degradation to English when translation unavailable
                """
                
                clarification = ClarificationRequest(
                    blind_spot_id=blind_spot['id'],
                    user_response=response
                )
                
                result = await orchestrator.process_clarification(
                    session_id, clarification
                )
                clarifications_made += 1
        
        # Check final session status
        final_status = orchestrator.get_session_status(session_id)
        assert final_status['progress']['addressed'] >= clarifications_made
    
    @pytest.mark.asyncio
    async def test_performance_requirement_enhancement(self, orchestrator, immigration_prd):
        """Test enhancement of performance requirements"""
        # Start with performance-focused analysis
        session_id, result = await orchestrator.start_clarification_session(
            prd_content=immigration_prd,
            mode=ClarifierMode.QUICK_CHECK,
            context={
                "focus_area": "performance",
                "expected_users": 100000,
                "peak_concurrent": 10000
            }
        )
        
        # Generate enhanced summary focusing on performance
        enhanced_summary = await orchestrator.generate_structured_summary(
            immigration_prd,
            version_id=result.get('current_version')
        )
        
        # Check performance specifications
        assert 'non_functional_requirements' in enhanced_summary['summary']
        nfr = enhanced_summary['summary']['non_functional_requirements']
        
        assert 'performance' in nfr
        perf = nfr['performance']
        
        # Should have specific metrics
        assert any(key in perf for key in ['response_time', 'throughput', 'latency'])
        assert any(key in perf for key in ['concurrent_users', 'scalability'])
        
        # Should have caching strategy
        assert 'technical_architecture' in enhanced_summary['summary']
        tech = enhanced_summary['summary']['technical_architecture']
        assert any('cache' in str(v).lower() or 'caching' in str(v).lower() 
                  for v in tech.values())
    
    @pytest.mark.asyncio
    async def test_security_compliance_enhancement(self, orchestrator, immigration_prd):
        """Test security and compliance enhancement for immigration data"""
        session_id, result = await orchestrator.start_clarification_session(
            prd_content=immigration_prd,
            mode=ClarifierMode.FULL_ANALYSIS,
            context={
                "regulations": ["GDPR", "PIPEDA", "IRCC_Privacy"],
                "data_sensitivity": "high",
                "audit_requirements": True
            }
        )
        
        # Should detect multiple security/compliance blind spots
        security_blind_spots = result['blind_spots_summary'].get('security', [])
        compliance_blind_spots = result['blind_spots_summary'].get('compliance', [])
        data_blind_spots = result['blind_spots_summary'].get('data_management', [])
        
        total_critical = len(security_blind_spots) + len(compliance_blind_spots) + len(data_blind_spots)
        assert total_critical > 3, "Should detect multiple security/compliance issues"
        
        # Generate final summary after analysis
        final_summary = await orchestrator.generate_structured_summary(immigration_prd)
        
        # Check security measures in summary
        summary = final_summary['summary']
        
        # Should have security section
        assert 'security' in summary or 'security_measures' in summary
        
        # Should mention encryption
        summary_str = json.dumps(summary).lower()
        assert 'encrypt' in summary_str
        
        # Should mention authentication
        assert 'authenticat' in summary_str or 'auth' in summary_str
        
        # Should mention compliance
        assert any(reg.lower() in summary_str for reg in ['gdpr', 'pipeda', 'privacy'])
    
    @pytest.mark.asyncio 
    async def test_iterative_improvement_cycle(self, orchestrator, immigration_prd):
        """Test iterative improvement through multiple clarification cycles"""
        session_id, initial_result = await orchestrator.start_clarification_session(
            prd_content=immigration_prd,
            mode=ClarifierMode.INTERACTIVE
        )
        
        initial_blind_spots = initial_result['total_blind_spots']
        improvements = []
        
        # Run 5 clarification cycles
        for i in range(5):
            if initial_result['next_action']['type'] != 'clarification_needed':
                break
                
            blind_spot = initial_result['next_action']['blind_spot']
            
            # Provide detailed clarification
            clarification = ClarificationRequest(
                blind_spot_id=blind_spot['id'],
                user_response=f"Clarification {i+1}: Detailed implementation covering all aspects mentioned in the questions with specific technical details, timelines, and success metrics."
            )
            
            result = await orchestrator.process_clarification(session_id, clarification)
            improvements.append(result.get('quality_improvement', 0))
            
            # Get next blind spot
            status = orchestrator.get_session_status(session_id)
            if status['progress']['addressed'] < initial_blind_spots:
                # Continue with next blind spot
                initial_result = result
        
        # Check improvements
        assert len(improvements) > 0
        assert sum(improvements) > 0  # Overall quality should improve
        
        # Final quality should be good
        final_summary = await orchestrator.generate_structured_summary(immigration_prd)
        assert final_summary['quality_score'] >= 70


class TestEdgeCasesWithRealData:
    """Test edge cases using real data"""
    
    @pytest.fixture
    def orchestrator(self):
        return ClarifierOrchestrator()
    
    @pytest.mark.asyncio
    async def test_empty_prd_handling(self, orchestrator):
        """Test handling of empty or minimal PRD"""
        minimal_prd = "Build a system"
        
        session_id, result = await orchestrator.start_clarification_session(
            prd_content=minimal_prd,
            mode=ClarifierMode.INTERACTIVE
        )
        
        # Should detect many blind spots for vague PRD
        assert result['total_blind_spots'] > 5
        
        # Should flag as very low quality
        summary_result = await orchestrator.generate_structured_summary(minimal_prd)
        assert summary_result['quality_score'] < 50
    
    @pytest.mark.asyncio
    async def test_conflicting_requirements(self, orchestrator):
        """Test handling of conflicting requirements"""
        conflicting_prd = """
        ## System Requirements
        
        1. Performance: Must handle 1 million concurrent users
        2. Infrastructure: Run on a single server
        3. Cost: Less than $100/month
        4. Availability: 99.99% uptime
        5. Data: Store 1PB of user data
        """
        
        session_id, result = await orchestrator.start_clarification_session(
            prd_content=conflicting_prd,
            mode=ClarifierMode.FULL_ANALYSIS
        )
        
        # Should detect conflicts
        all_blind_spots = []
        for bs_list in result['blind_spots_summary'].values():
            all_blind_spots.extend(bs_list)
        
        conflict_related = [bs for bs in all_blind_spots
                          if any(term in bs.lower()
                                for term in ['conflict', 'inconsistent', 'impossible', 'unrealistic'])]
        
        assert len(conflict_related) > 0 or result['total_blind_spots'] > 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
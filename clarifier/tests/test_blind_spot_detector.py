"""
Comprehensive tests for BlindSpotDetector
"""

import pytest
import asyncio
from typing import List, Dict, Any
from unittest.mock import Mock, patch, AsyncMock

from clarifier.core import BlindSpotDetector, BlindSpotType
from clarifier.core.blind_spot_detector import BlindSpot


class TestBlindSpotDetector:
    """Test BlindSpotDetector functionality"""
    
    @pytest.fixture
    def detector(self):
        """Create detector instance"""
        return BlindSpotDetector()
    
    @pytest.fixture
    def immigration_prd(self):
        """Real PRD from ThinkForward AI"""
        return """
        ## ThinkForward AI - Immigration Platform
        
        ### Core Features
        1. AI-Guided Form Filling
           - Conversational AI for pathway exploration
           - Dynamic form generation
           - Real-time validation
        
        2. Document Management
           - Upload various document formats
           - OCR and data extraction
           - Document analysis
        
        3. Multi-language Support
           - English, French, Chinese
           - Cultural adaptation
        
        ### Performance Requirements
        - Page load < 2 seconds
        - AI response < 3 seconds
        - 99.9% availability
        """
    
    @pytest.fixture
    def ecommerce_prd(self):
        """E-commerce PRD with multiple blind spots"""
        return """
        ## E-commerce Platform
        
        ### Features
        1. Product catalog with search
        2. Shopping cart and checkout
        3. User registration and login
        4. Payment processing
        5. Order tracking
        """
    
    @pytest.mark.asyncio
    async def test_detect_edge_cases(self, detector, immigration_prd):
        """Test edge case detection"""
        blind_spots = await detector.detect_blind_spots(immigration_prd)
        
        # Should detect edge cases for file upload
        edge_cases = [bs for bs in blind_spots if bs.type == BlindSpotType.EDGE_CASE]
        assert len(edge_cases) > 0
        
        # Check for file size limits
        file_size_issues = [bs for bs in blind_spots if "file size" in bs.description.lower()]
        assert len(file_size_issues) > 0
    
    @pytest.mark.asyncio
    async def test_detect_security_issues(self, detector, ecommerce_prd):
        """Test security blind spot detection"""
        blind_spots = await detector.detect_blind_spots(ecommerce_prd)
        
        security_issues = [bs for bs in blind_spots if bs.type == BlindSpotType.SECURITY]
        assert len(security_issues) > 0
        
        # Should detect payment security issues
        payment_security = [bs for bs in security_issues if "payment" in bs.description.lower()]
        assert len(payment_security) > 0
    
    @pytest.mark.asyncio
    async def test_detect_performance_issues(self, detector, immigration_prd):
        """Test performance blind spot detection"""
        blind_spots = await detector.detect_blind_spots(immigration_prd)
        
        performance_issues = [bs for bs in blind_spots if bs.type == BlindSpotType.PERFORMANCE]
        assert len(performance_issues) > 0
        
        # Should detect caching strategies
        caching_issues = [bs for bs in blind_spots if "cach" in bs.description.lower()]
        assert len(caching_issues) > 0
    
    @pytest.mark.asyncio
    async def test_detect_error_handling(self, detector, ecommerce_prd):
        """Test error handling detection"""
        blind_spots = await detector.detect_blind_spots(ecommerce_prd)
        
        error_handling = [bs for bs in blind_spots if bs.type == BlindSpotType.ERROR_HANDLING]
        assert len(error_handling) > 0
        
        # Should detect payment failure handling
        payment_errors = [bs for bs in error_handling if "payment" in bs.description.lower()]
        assert len(payment_errors) > 0
    
    @pytest.mark.asyncio
    async def test_domain_specific_detection(self, detector):
        """Test domain-specific blind spot detection"""
        # Test e-commerce specific
        ecommerce_prd = "Build an online store with products and checkout"
        blind_spots = await detector.detect_blind_spots(
            ecommerce_prd, 
            context={"project_type": "e-commerce"}
        )
        
        # Should detect inventory management issues
        inventory_issues = [bs for bs in blind_spots if "inventory" in bs.description.lower()]
        assert len(inventory_issues) > 0
        
        # Test SaaS specific
        saas_prd = "Create a subscription-based analytics platform"
        blind_spots = await detector.detect_blind_spots(
            saas_prd,
            context={"project_type": "saas"}
        )
        
        # Should detect billing and subscription issues
        billing_issues = [bs for bs in blind_spots if "billing" in bs.description.lower() or "subscription" in bs.description.lower()]
        assert len(billing_issues) > 0
    
    @pytest.mark.asyncio
    async def test_severity_scoring(self, detector, ecommerce_prd):
        """Test severity scoring accuracy"""
        blind_spots = await detector.detect_blind_spots(ecommerce_prd)
        
        # Security issues should have high severity
        security_issues = [bs for bs in blind_spots if bs.type == BlindSpotType.SECURITY]
        for issue in security_issues:
            assert issue.severity in ["high", "critical"]
        
        # UX issues should have lower severity
        ux_issues = [bs for bs in blind_spots if bs.type == BlindSpotType.USER_EXPERIENCE]
        for issue in ux_issues:
            assert issue.severity in ["low", "medium"]
    
    @pytest.mark.asyncio
    async def test_ai_analysis_integration(self, detector):
        """Test AI analysis integration"""
        with patch.object(detector, '_ai_deep_analysis', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = [
                BlindSpot(
                    id="AI_001",
                    type=BlindSpotType.SCALABILITY,
                    title="Database Scaling Strategy",
                    description="No mention of database scaling strategy",
                    severity="high",
                    questions=["How will the database scale?"],
                    suggestions=["Consider sharding or replication"]
                )
            ]
            
            prd = "Build a social media platform"
            blind_spots = await detector.detect_blind_spots(prd, use_ai=True)
            
            # Should include AI-detected blind spots
            ai_spots = [bs for bs in blind_spots if bs.id.startswith("AI_")]
            assert len(ai_spots) > 0
            mock_ai.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_blind_spot_filtering(self, detector):
        """Test blind spot filtering by type"""
        prd = "Create a payment processing system"
        all_blind_spots = await detector.detect_blind_spots(prd)
        
        # Filter by single type
        security_only = detector.filter_blind_spots(
            all_blind_spots,
            types=[BlindSpotType.SECURITY]
        )
        assert all(bs.type == BlindSpotType.SECURITY for bs in security_only)
        
        # Filter by multiple types
        critical_types = detector.filter_blind_spots(
            all_blind_spots,
            types=[BlindSpotType.SECURITY, BlindSpotType.ERROR_HANDLING]
        )
        assert all(bs.type in [BlindSpotType.SECURITY, BlindSpotType.ERROR_HANDLING] 
                  for bs in critical_types)
    
    @pytest.mark.asyncio
    async def test_blind_spot_prioritization(self, detector, immigration_prd):
        """Test blind spot prioritization"""
        blind_spots = await detector.detect_blind_spots(immigration_prd)
        prioritized = detector.prioritize_blind_spots(blind_spots)
        
        # Should be sorted by severity (critical > high > medium > low)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        for i in range(len(prioritized) - 1):
            current_severity = severity_order[prioritized[i].severity]
            next_severity = severity_order[prioritized[i + 1].severity]
            assert current_severity <= next_severity
    
    @pytest.mark.asyncio
    async def test_comprehensive_immigration_analysis(self, detector):
        """Test comprehensive analysis using real immigration PRD"""
        with open("/Users/ziyanzhou/Projects/expeta/data/input/requirement-md.md", "r") as f:
            full_immigration_prd = f.read()
        
        blind_spots = await detector.detect_blind_spots(
            full_immigration_prd,
            context={"project_type": "saas", "domain": "immigration"}
        )
        
        # Should detect various categories
        types_found = set(bs.type for bs in blind_spots)
        assert BlindSpotType.SECURITY in types_found  # Data protection
        assert BlindSpotType.SCALABILITY in types_found  # Multi-tenant
        assert BlindSpotType.ERROR_HANDLING in types_found  # Form errors
        assert BlindSpotType.USER_EXPERIENCE in types_found  # Multi-language
        
        # Should have specific immigration-related blind spots
        immigration_specific = [
            bs for bs in blind_spots 
            if any(term in bs.description.lower() 
                  for term in ["visa", "immigration", "applicant", "consultant"])
        ]
        assert len(immigration_specific) > 0
    
    @pytest.mark.asyncio
    async def test_pattern_matching_accuracy(self, detector):
        """Test pattern matching accuracy"""
        test_cases = [
            {
                "prd": "User uploads files to the system",
                "expected_patterns": ["file_upload", "edge_case"]
            },
            {
                "prd": "Process payments using credit cards",
                "expected_patterns": ["payment", "security"]
            },
            {
                "prd": "System sends email notifications",
                "expected_patterns": ["notification", "error_handling"]
            }
        ]
        
        for case in test_cases:
            blind_spots = await detector.detect_blind_spots(case["prd"])
            found_patterns = set()
            
            for bs in blind_spots:
                if "upload" in bs.description.lower():
                    found_patterns.add("file_upload")
                if "payment" in bs.description.lower():
                    found_patterns.add("payment")
                if "security" in bs.description.lower():
                    found_patterns.add("security")
                if "notification" in bs.description.lower():
                    found_patterns.add("notification")
                if bs.type == BlindSpotType.EDGE_CASE:
                    found_patterns.add("edge_case")
                if bs.type == BlindSpotType.ERROR_HANDLING:
                    found_patterns.add("error_handling")
            
            for expected in case["expected_patterns"]:
                assert expected in found_patterns, f"Expected pattern '{expected}' not found"
    
    @pytest.mark.asyncio
    async def test_question_generation_quality(self, detector, ecommerce_prd):
        """Test quality of generated questions"""
        blind_spots = await detector.detect_blind_spots(ecommerce_prd)
        
        for bs in blind_spots:
            # Each blind spot should have questions
            assert len(bs.questions) > 0
            
            # Questions should be specific and actionable
            for question in bs.questions:
                assert len(question) > 10  # Not too short
                assert question.endswith("?")  # Proper question format
                assert not question.isupper()  # Not shouting
    
    @pytest.mark.asyncio
    async def test_suggestion_generation_quality(self, detector, immigration_prd):
        """Test quality of generated suggestions"""
        blind_spots = await detector.detect_blind_spots(immigration_prd)
        
        for bs in blind_spots:
            # Each blind spot should have suggestions
            assert len(bs.suggestions) > 0
            
            # Suggestions should be actionable
            for suggestion in bs.suggestions:
                assert len(suggestion) > 10  # Not too short
                # Should contain action words
                action_words = ["implement", "add", "create", "define", "consider", "use", "ensure"]
                assert any(word in suggestion.lower() for word in action_words)
    
    @pytest.mark.asyncio
    async def test_empty_prd_handling(self, detector):
        """Test handling of empty or minimal PRDs"""
        # Empty PRD
        blind_spots = await detector.detect_blind_spots("")
        assert len(blind_spots) == 0
        
        # Very minimal PRD
        blind_spots = await detector.detect_blind_spots("Build a website")
        assert len(blind_spots) > 0  # Should still detect generic issues
    
    @pytest.mark.asyncio
    async def test_large_prd_performance(self, detector):
        """Test performance with large PRDs"""
        # Generate a large PRD
        large_prd = """
        ## Large System Specification
        """ + "\n".join([f"Feature {i}: Description of feature {i}" for i in range(100)])
        
        import time
        start_time = time.time()
        blind_spots = await detector.detect_blind_spots(large_prd)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 5.0  # 5 seconds max
        assert len(blind_spots) > 0
    
    def test_blind_spot_type_coverage(self, detector):
        """Test that all blind spot types are covered"""
        # Check that all enum values have patterns
        for blind_spot_type in BlindSpotType:
            type_patterns = [
                pattern for pattern in detector.pattern_matchers
                if pattern['type'] == blind_spot_type
            ]
            assert len(type_patterns) > 0, f"No patterns for {blind_spot_type}"
    
    @pytest.mark.asyncio
    async def test_context_aware_detection(self, detector):
        """Test context-aware blind spot detection"""
        base_prd = "Create a user management system"
        
        # Without context
        blind_spots_no_context = await detector.detect_blind_spots(base_prd)
        
        # With B2B context
        blind_spots_b2b = await detector.detect_blind_spots(
            base_prd,
            context={"business_model": "b2b", "industry": "enterprise"}
        )
        
        # With B2C context
        blind_spots_b2c = await detector.detect_blind_spots(
            base_prd,
            context={"business_model": "b2c", "industry": "consumer"}
        )
        
        # Should have different blind spots based on context
        b2b_specific = [bs for bs in blind_spots_b2b if "sso" in bs.description.lower() or "enterprise" in bs.description.lower()]
        b2c_specific = [bs for bs in blind_spots_b2c if "social" in bs.description.lower() or "consumer" in bs.description.lower()]
        
        assert len(b2b_specific) > 0 or len(b2c_specific) > 0


class TestBlindSpotPatterns:
    """Test specific blind spot patterns"""
    
    @pytest.fixture
    def detector(self):
        return BlindSpotDetector()
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("prd,expected_type", [
        ("System allows file uploads", BlindSpotType.EDGE_CASE),
        ("Users can make payments", BlindSpotType.SECURITY),
        ("Platform supports 1 million users", BlindSpotType.SCALABILITY),
        ("Mobile app for iOS and Android", BlindSpotType.USER_EXPERIENCE),
        ("Real-time chat functionality", BlindSpotType.PERFORMANCE),
        ("API for third-party integrations", BlindSpotType.INTEGRATION),
        ("User data is stored securely", BlindSpotType.DATA_MANAGEMENT),
        ("System is always available", BlindSpotType.MONITORING),
    ])
    async def test_specific_pattern_detection(self, detector, prd, expected_type):
        """Test detection of specific patterns"""
        blind_spots = await detector.detect_blind_spots(prd)
        types_found = [bs.type for bs in blind_spots]
        assert expected_type in types_found


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
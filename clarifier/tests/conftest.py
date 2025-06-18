"""
Pytest configuration for Clarifier tests
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing without API calls"""
    def _mock_response(prompt):
        if "blind spot" in prompt.lower():
            return """
            Based on the PRD analysis, here are additional blind spots:
            
            1. **Data Retention Policy**: No mention of how long user data is retained
               - Question: What is the data retention policy for user information?
               - Suggestion: Define clear data retention periods for different data types
            
            2. **API Rate Limiting**: No specification for API rate limits
               - Question: What are the rate limiting requirements for APIs?
               - Suggestion: Implement rate limiting to prevent abuse
            
            3. **Disaster Recovery**: No disaster recovery plan mentioned
               - Question: What is the RTO/RPO for disaster recovery?
               - Suggestion: Create comprehensive disaster recovery procedures
            """
        
        elif "structured summary" in prompt.lower():
            return """
            {
                "technical_architecture": {
                    "frontend": {
                        "framework": "Next.js 14",
                        "styling": "Tailwind CSS",
                        "state_management": "Redux Toolkit",
                        "components": ["Dashboard", "Forms", "Documents", "Chat"]
                    },
                    "backend": {
                        "runtime": "Node.js",
                        "framework": "Express",
                        "architecture": "Serverless",
                        "api_style": "RESTful + GraphQL"
                    },
                    "database": {
                        "primary": "MongoDB Atlas",
                        "cache": "Redis",
                        "search": "Elasticsearch"
                    }
                },
                "functional_modules": [
                    {
                        "name": "AI Dialogue Module",
                        "features": ["Natural language processing", "Context management", "Multi-turn conversation"],
                        "apis": ["/api/dialogue/start", "/api/dialogue/continue", "/api/dialogue/end"]
                    },
                    {
                        "name": "Form Generation Module", 
                        "features": ["Dynamic form creation", "Validation", "PDF generation"],
                        "apis": ["/api/forms/generate", "/api/forms/validate", "/api/forms/export"]
                    }
                ],
                "non_functional_requirements": {
                    "performance": {
                        "response_time": "< 200ms p95",
                        "throughput": "10000 requests/second",
                        "concurrent_users": 50000
                    },
                    "security": {
                        "authentication": "JWT + OAuth2",
                        "encryption": "AES-256 at rest, TLS 1.3 in transit",
                        "compliance": ["GDPR", "PIPEDA", "SOC2"]
                    }
                }
            }
            """
        
        elif "clarification" in prompt.lower():
            return """
            Thank you for the clarification. Based on your response, here's the enhanced understanding:
            
            1. The system will implement comprehensive error handling with retry logic
            2. All edge cases will be covered with specific validation rules
            3. Performance monitoring will track key metrics in real-time
            
            This clarification significantly improves the requirement specificity.
            """
        
        else:
            return "Generic test response for LLM prompt"
    
    return _mock_response


@pytest.fixture
def sample_components():
    """Sample component structure for testing"""
    return {
        "frontend": {
            "type": "ui",
            "dependencies": ["api_gateway"],
            "features": ["dashboard", "forms", "reports"]
        },
        "api_gateway": {
            "type": "service",
            "dependencies": ["auth_service", "business_logic"],
            "features": ["routing", "rate_limiting", "caching"]
        },
        "auth_service": {
            "type": "service", 
            "dependencies": ["user_database"],
            "features": ["authentication", "authorization", "session_management"]
        },
        "business_logic": {
            "type": "service",
            "dependencies": ["main_database", "external_apis"],
            "features": ["core_processing", "validation", "calculations"]
        },
        "main_database": {
            "type": "database",
            "dependencies": [],
            "features": ["data_storage", "transactions", "replication"]
        }
    }


@pytest.fixture
def sample_change_request():
    """Sample change request for testing"""
    return {
        "type": "feature_addition",
        "description": "Add real-time notifications",
        "requirements": {
            "current": {
                "notifications": ["email"],
                "delivery": ["async"]
            },
            "target": {
                "notifications": ["email", "sms", "push", "in-app"],
                "delivery": ["async", "real-time"],
                "infrastructure": ["websockets", "notification_service"]
            }
        },
        "constraints": {
            "timeline": "6 weeks",
            "budget": "medium",
            "team_size": 3
        }
    }


# Test markers
pytest.mark.slow = pytest.mark.slow
pytest.mark.integration = pytest.mark.integration
pytest.mark.unit = pytest.mark.unit
"""
Comprehensive tests for VersionManager
"""

import pytest
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any

from clarifier.core import VersionManager, RequirementVersion
from clarifier.core.version_manager import Version, VersionStatus, Change, ChangeType


class TestVersionManager:
    """Test VersionManager functionality"""
    
    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary storage directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def version_manager(self, temp_storage_dir):
        """Create VersionManager instance with temp storage"""
        return VersionManager(storage_path=temp_storage_dir)
    
    @pytest.fixture
    def sample_prd(self):
        """Sample PRD content"""
        return """
        ## Project: Task Management System
        
        ### Features
        1. Create and manage tasks
        2. Assign tasks to users
        3. Track task progress
        4. Generate reports
        """
    
    @pytest.fixture
    def sample_summary(self):
        """Sample JSON summary"""
        return {
            "project_name": "Task Management System",
            "features": [
                "Task creation and management",
                "User assignment",
                "Progress tracking",
                "Reporting"
            ],
            "technical_requirements": {
                "database": "PostgreSQL",
                "framework": "Django"
            }
        }
    
    def test_initialize_with_prd(self, version_manager, sample_prd, sample_summary):
        """Test initializing with PRD"""
        version_id = version_manager.initialize_with_prd(sample_prd, sample_summary)
        
        assert version_id is not None
        assert version_id.startswith("v_")
        
        # Check version was created
        version = version_manager.requirement_version.get_version(version_id)
        assert version is not None
        assert version.prd_content == sample_prd
        assert version.json_summary == sample_summary
        assert version.parent_id is None
        assert version.status == VersionStatus.ACTIVE
    
    def test_save_blind_spot_clarification(self, version_manager, sample_prd, sample_summary):
        """Test saving blind spot clarification"""
        # Initialize first
        initial_id = version_manager.initialize_with_prd(sample_prd, sample_summary)
        
        # Add clarification
        updated_prd = sample_prd + "\n\n### Security Requirements\n- User authentication\n- Data encryption"
        updated_summary = {**sample_summary, "security": ["authentication", "encryption"]}
        
        new_version_id = version_manager.save_blind_spot_clarification(
            updated_prd,
            updated_summary,
            "BS_001",
            "Added security requirements"
        )
        
        assert new_version_id != initial_id
        
        # Check new version
        new_version = version_manager.requirement_version.get_version(new_version_id)
        assert new_version.parent_id == initial_id
        assert "BS_001" in new_version.metadata["blind_spot_addressed"]
        assert new_version.change_summary == "Added security requirements"
    
    def test_apply_requirement_change(self, version_manager, sample_prd, sample_summary):
        """Test applying requirement changes"""
        initial_id = version_manager.initialize_with_prd(sample_prd, sample_summary)
        
        # Create change
        change = Change(
            type=ChangeType.FEATURE_ADDITION,
            description="Add notification system",
            details={
                "component": "notifications",
                "requirements": ["email", "push", "in-app"]
            }
        )
        
        new_version_id = version_manager.apply_requirement_change(
            change,
            updated_prd=sample_prd + "\n\n### Notifications\n- Email notifications\n- Push notifications",
            updated_summary={**sample_summary, "notifications": ["email", "push"]}
        )
        
        # Verify change was applied
        new_version = version_manager.requirement_version.get_version(new_version_id)
        assert new_version.metadata["change_type"] == "feature_addition"
        assert "notification" in new_version.change_summary.lower()
    
    def test_create_branch(self, version_manager, sample_prd, sample_summary):
        """Test branch creation"""
        main_id = version_manager.initialize_with_prd(sample_prd, sample_summary)
        
        # Create branch
        branch_id = version_manager.requirement_version.create_branch(
            main_id,
            "feature/mobile-app"
        )
        
        assert branch_id != main_id
        
        # Check branch
        branch_version = version_manager.requirement_version.get_version(branch_id)
        assert branch_version.parent_id == main_id
        assert branch_version.branch == "feature/mobile-app"
        assert branch_version.metadata["branched_from"] == main_id
    
    def test_merge_versions(self, version_manager, sample_prd, sample_summary):
        """Test version merging"""
        # Create main and branch
        main_id = version_manager.initialize_with_prd(sample_prd, sample_summary)
        branch_id = version_manager.requirement_version.create_branch(main_id, "feature/api")
        
        # Update branch
        branch_prd = sample_prd + "\n\n### API\n- RESTful API\n- GraphQL support"
        branch_summary = {**sample_summary, "api": ["rest", "graphql"]}
        
        updated_branch_id = version_manager.save_blind_spot_clarification(
            branch_prd,
            branch_summary,
            "BS_API",
            "Added API specifications"
        )
        
        # Merge back to main
        merged_id = version_manager.requirement_version.merge_versions(
            updated_branch_id,
            main_id,
            merge_strategy="recursive"
        )
        
        # Check merged version
        merged_version = version_manager.requirement_version.get_version(merged_id)
        assert "api" in merged_version.json_summary
        assert "API" in merged_version.prd_content
    
    def test_rollback_to_version(self, version_manager, sample_prd, sample_summary):
        """Test version rollback"""
        # Create version history
        v1 = version_manager.initialize_with_prd(sample_prd, sample_summary)
        
        v2_prd = sample_prd + "\n\n### Feature X"
        v2_summary = {**sample_summary, "feature_x": True}
        v2 = version_manager.save_blind_spot_clarification(v2_prd, v2_summary, "BS_002", "Added Feature X")
        
        v3_prd = v2_prd + "\n\n### Feature Y"
        v3_summary = {**v2_summary, "feature_y": True}
        v3 = version_manager.save_blind_spot_clarification(v3_prd, v3_summary, "BS_003", "Added Feature Y")
        
        # Rollback to v1
        version_manager.rollback_to_version(v1, "Feature X and Y caused issues")
        
        # Check current version
        current = version_manager.requirement_version.get_current_version()
        assert current.prd_content == sample_prd
        assert current.json_summary == sample_summary
        assert current.metadata.get("rollback_from") == v3
    
    def test_get_version_history(self, version_manager, sample_prd, sample_summary):
        """Test retrieving version history"""
        # Create multiple versions
        v1 = version_manager.initialize_with_prd(sample_prd, sample_summary)
        
        for i in range(5):
            updated_prd = sample_prd + f"\n\n### Update {i}"
            updated_summary = {**sample_summary, f"update_{i}": True}
            version_manager.save_blind_spot_clarification(
                updated_prd,
                updated_summary,
                f"BS_{i}",
                f"Update {i}"
            )
        
        # Get history
        history = version_manager.get_version_history(limit=3)
        assert len(history) == 3
        
        # Should be in reverse chronological order
        for i in range(len(history) - 1):
            assert history[i]['timestamp'] >= history[i + 1]['timestamp']
    
    def test_get_blind_spot_history(self, version_manager, sample_prd, sample_summary):
        """Test retrieving blind spot history"""
        version_manager.initialize_with_prd(sample_prd, sample_summary)
        
        # Address multiple blind spots
        blind_spots = [
            ("BS_001", "Security", "Added authentication"),
            ("BS_002", "Performance", "Added caching"),
            ("BS_003", "Scalability", "Added load balancing")
        ]
        
        for bs_id, topic, summary in blind_spots:
            updated_prd = sample_prd + f"\n\n### {topic}"
            updated_summary = {**sample_summary, topic.lower(): True}
            version_manager.save_blind_spot_clarification(
                updated_prd,
                updated_summary,
                bs_id,
                summary
            )
        
        # Get blind spot history
        bs_history = version_manager.get_blind_spot_history()
        assert len(bs_history) == 3
        
        # Check all blind spots are recorded
        bs_ids = [h['blind_spot_id'] for h in bs_history]
        assert "BS_001" in bs_ids
        assert "BS_002" in bs_ids
        assert "BS_003" in bs_ids
    
    def test_compare_versions(self, version_manager, sample_prd, sample_summary):
        """Test version comparison"""
        v1 = version_manager.initialize_with_prd(sample_prd, sample_summary)
        
        # Create modified version
        v2_prd = sample_prd.replace("Task Management", "Project Management")
        v2_prd += "\n\n### Additional Features\n- Gantt charts\n- Resource allocation"
        v2_summary = {
            **sample_summary,
            "project_name": "Project Management System",
            "additional_features": ["gantt_charts", "resource_allocation"]
        }
        v2 = version_manager.save_blind_spot_clarification(v2_prd, v2_summary, "BS_004", "Upgraded to project management")
        
        # Compare versions
        comparison = version_manager.compare_versions(v1, v2)
        
        assert comparison is not None
        assert "prd_diff" in comparison
        assert "summary_diff" in comparison
        assert comparison["from_version"] == v1
        assert comparison["to_version"] == v2
    
    def test_export_version_history(self, version_manager, sample_prd, sample_summary):
        """Test exporting version history"""
        # Create some versions
        version_manager.initialize_with_prd(sample_prd, sample_summary)
        for i in range(3):
            version_manager.save_blind_spot_clarification(
                sample_prd + f"\n\nUpdate {i}",
                {**sample_summary, f"update_{i}": True},
                f"BS_{i}",
                f"Update {i}"
            )
        
        # Test JSON export
        json_export = version_manager.requirement_version.export_version_history("json")
        exported_data = json.loads(json_export)
        assert "versions" in exported_data
        assert len(exported_data["versions"]) >= 4
        
        # Test Markdown export
        md_export = version_manager.requirement_version.export_version_history("markdown")
        assert "# 版本历史" in md_export
        assert "Update 0" in md_export
        assert "Update 1" in md_export
        assert "Update 2" in md_export
    
    def test_search_versions(self, version_manager, sample_prd, sample_summary):
        """Test version search functionality"""
        version_manager.initialize_with_prd(sample_prd, sample_summary)
        
        # Create versions with specific content
        search_terms = ["authentication", "performance", "mobile app"]
        for term in search_terms:
            updated_prd = sample_prd + f"\n\n### {term.title()}\nImplementation of {term}"
            version_manager.save_blind_spot_clarification(
                updated_prd,
                {**sample_summary, term.replace(" ", "_"): True},
                f"BS_{term}",
                f"Added {term}"
            )
        
        # Search for specific term
        results = version_manager.requirement_version.search_versions("performance")
        assert len(results) > 0
        assert any("performance" in v.prd_content.lower() for v in results)
    
    def test_version_tagging(self, version_manager, sample_prd, sample_summary):
        """Test version tagging functionality"""
        v1 = version_manager.initialize_with_prd(sample_prd, sample_summary)
        
        # Tag version
        version_manager.requirement_version.tag_version(v1, "v1.0.0", "Initial release")
        
        # Get version by tag
        tagged_version = version_manager.requirement_version.get_version_by_tag("v1.0.0")
        assert tagged_version is not None
        assert tagged_version.id == v1
    
    def test_concurrent_version_creation(self, version_manager, sample_prd, sample_summary):
        """Test concurrent version creation"""
        import threading
        import time
        
        version_manager.initialize_with_prd(sample_prd, sample_summary)
        
        created_versions = []
        lock = threading.Lock()
        
        def create_version(index):
            time.sleep(0.01)  # Small delay to increase chance of collision
            version_id = version_manager.save_blind_spot_clarification(
                sample_prd + f"\n\nConcurrent update {index}",
                {**sample_summary, f"concurrent_{index}": True},
                f"BS_CONCURRENT_{index}",
                f"Concurrent update {index}"
            )
            with lock:
                created_versions.append(version_id)
        
        # Create multiple versions concurrently
        threads = []
        for i in range(5):
            t = threading.Thread(target=create_version, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # All versions should be unique
        assert len(created_versions) == 5
        assert len(set(created_versions)) == 5
    
    def test_version_metadata_management(self, version_manager, sample_prd, sample_summary):
        """Test version metadata management"""
        v1 = version_manager.initialize_with_prd(sample_prd, sample_summary)
        
        # Add custom metadata
        version = version_manager.requirement_version.get_version(v1)
        version.metadata["reviewed_by"] = "john.doe"
        version.metadata["review_status"] = "approved"
        version.metadata["deployment_target"] = "production"
        
        # Update version with metadata
        version_manager.requirement_version.update_version_metadata(
            v1,
            version.metadata
        )
        
        # Retrieve and verify
        updated_version = version_manager.requirement_version.get_version(v1)
        assert updated_version.metadata["reviewed_by"] == "john.doe"
        assert updated_version.metadata["review_status"] == "approved"
        assert updated_version.metadata["deployment_target"] == "production"
    
    def test_version_statistics(self, version_manager, sample_prd, sample_summary):
        """Test version statistics generation"""
        version_manager.initialize_with_prd(sample_prd, sample_summary)
        
        # Create versions over time
        for i in range(10):
            version_manager.save_blind_spot_clarification(
                sample_prd + f"\n\nUpdate {i}",
                {**sample_summary, f"update_{i}": True},
                f"BS_{i}",
                f"Update {i}"
            )
        
        # Get statistics
        stats = version_manager.requirement_version.get_version_statistics()
        
        assert stats["total_versions"] == 11  # Initial + 10 updates
        assert stats["total_blind_spots_addressed"] == 10
        assert "most_recent_version" in stats
        assert "version_frequency" in stats
    
    def test_prd_evolution_tracking(self, version_manager):
        """Test tracking PRD evolution over time"""
        # Start with minimal PRD
        initial_prd = "## Project: Simple App\n\n### Features\n- Basic functionality"
        initial_summary = {"project": "Simple App", "features": ["basic"]}
        
        v1 = version_manager.initialize_with_prd(initial_prd, initial_summary)
        
        # Evolve PRD over multiple versions
        evolution_steps = [
            ("Added user management", "- User registration\n- User login"),
            ("Added data persistence", "- Database integration\n- Data backup"),
            ("Added API", "- RESTful endpoints\n- API documentation"),
            ("Added monitoring", "- Performance metrics\n- Error tracking")
        ]
        
        for i, (summary, addition) in enumerate(evolution_steps):
            current_version = version_manager.requirement_version.get_current_version()
            evolved_prd = current_version.prd_content + f"\n\n### Evolution {i+1}\n{addition}"
            evolved_summary = {**current_version.json_summary, f"evolution_{i+1}": summary}
            
            version_manager.save_blind_spot_clarification(
                evolved_prd,
                evolved_summary,
                f"BS_EVOLUTION_{i+1}",
                summary
            )
        
        # Track evolution
        evolution = version_manager.requirement_version.get_prd_evolution()
        
        assert len(evolution) == 5  # Initial + 4 evolution steps
        assert evolution[-1]["features_added"] >= 4
        assert "User registration" in evolution[-1]["prd_content"]
        assert "API documentation" in evolution[-1]["prd_content"]


class TestRequirementVersion:
    """Test RequirementVersion class functionality"""
    
    @pytest.fixture
    def requirement_version(self, temp_storage_dir):
        """Create RequirementVersion instance"""
        return RequirementVersion(storage_path=temp_storage_dir)
    
    def test_version_status_transitions(self, requirement_version):
        """Test version status transitions"""
        # Create active version
        version = requirement_version.create_version(
            "Test PRD",
            {"test": True},
            change_summary="Initial"
        )
        
        assert version.status == VersionStatus.ACTIVE
        
        # Archive version
        requirement_version.archive_version(version.id)
        archived = requirement_version.get_version(version.id)
        assert archived.status == VersionStatus.ARCHIVED
        
        # Try to modify archived version (should fail)
        with pytest.raises(ValueError):
            requirement_version.update_version_metadata(
                version.id,
                {"new_field": "value"}
            )
    
    def test_version_tree_visualization(self, requirement_version):
        """Test version tree visualization"""
        # Create branching structure
        main = requirement_version.create_version("Main", {}, change_summary="Initial")
        
        # Create two branches
        branch1 = requirement_version.create_version(
            "Branch 1", {}, 
            parent_id=main.id, 
            branch="feature/branch1",
            change_summary="Branch 1"
        )
        
        branch2 = requirement_version.create_version(
            "Branch 2", {},
            parent_id=main.id,
            branch="feature/branch2", 
            change_summary="Branch 2"
        )
        
        # Add commits to branches
        requirement_version.create_version(
            "Branch 1 Update", {},
            parent_id=branch1.id,
            branch="feature/branch1",
            change_summary="Update on branch 1"
        )
        
        # Visualize tree
        tree_viz = requirement_version.visualize_version_tree()
        
        assert main.id in tree_viz
        assert "feature/branch1" in tree_viz
        assert "feature/branch2" in tree_viz
    
    def test_conflict_detection(self, requirement_version):
        """Test conflict detection between versions"""
        # Create base version
        base = requirement_version.create_version(
            "Base PRD", 
            {"features": ["A", "B"]},
            change_summary="Base"
        )
        
        # Create two conflicting branches
        branch1 = requirement_version.create_version(
            "Modified feature A differently",
            {"features": ["A_modified_v1", "B"]},
            parent_id=base.id,
            branch="branch1",
            change_summary="Modified A v1"
        )
        
        branch2 = requirement_version.create_version(
            "Modified feature A differently", 
            {"features": ["A_modified_v2", "B"]},
            parent_id=base.id,
            branch="branch2",
            change_summary="Modified A v2"
        )
        
        # Detect conflicts
        conflicts = requirement_version.detect_conflicts(branch1.id, branch2.id)
        
        assert len(conflicts) > 0
        assert any("features" in str(c) for c in conflicts)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
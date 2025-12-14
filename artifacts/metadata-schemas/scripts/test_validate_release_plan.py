#!/usr/bin/env python3
"""
Unit tests for MetadataValidator.validate() method

Tests the complete validation workflow including:
- File loading and YAML parsing
- Schema type detection
- Schema validation
- Semantic rule checking
- File existence checking
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import yaml
from jsonschema import ValidationError
import sys
import importlib.util

# Import the module under test (validate-release-plan.py has hyphens, so we need special handling)
script_dir = Path(__file__).parent
spec = importlib.util.spec_from_file_location("validate_release_plan", script_dir / "validate-release-plan.py")
validate_module = importlib.util.module_from_spec(spec)
sys.modules["validate_release_plan"] = validate_module
spec.loader.exec_module(validate_module)
MetadataValidator = validate_module.MetadataValidator


# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent / "test_fixtures"
VALID_DIR = FIXTURES_DIR / "valid"
INVALID_DIR = FIXTURES_DIR / "invalid"
SCHEMAS_DIR = FIXTURES_DIR / "schemas"


# Pytest fixtures
@pytest.fixture
def release_plan_schema():
    """Load release-plan schema for tests"""
    schema_file = SCHEMAS_DIR / "release-plan-schema.yaml"
    with open(schema_file, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def release_metadata_schema():
    """Load release-metadata schema for tests"""
    schema_file = SCHEMAS_DIR / "release-metadata-schema.yaml"
    with open(schema_file, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def temp_metadata_dir(tmp_path):
    """Create temporary directory with code/API_definitions structure for file checks"""
    api_dir = tmp_path / "code" / "API_definitions"
    api_dir.mkdir(parents=True)
    return tmp_path


class TestMetadataValidatorValidate:
    """Tests for MetadataValidator.validate() method"""

    class TestHappyPath:
        """Successful validation scenarios"""

        def test_validate_release_plan_success(self):
            """Valid release-plan.yaml with auto-detected schema"""
            metadata_file = VALID_DIR / "release-plan-valid.yaml"
            validator = MetadataValidator(metadata_file)

            result = validator.validate()

            assert result is True
            assert len(validator.errors) == 0
            assert len(validator.warnings) == 0

        def test_validate_release_metadata_success(self):
            """Valid release-metadata.yaml with auto-detected schema"""
            metadata_file = VALID_DIR / "release-metadata-valid.yaml"
            validator = MetadataValidator(metadata_file)

            result = validator.validate()

            assert result is True
            assert len(validator.errors) == 0
            assert len(validator.warnings) == 0

        def test_validate_with_explicit_schema_success(self):
            """Validation with explicitly provided schema file"""
            metadata_file = VALID_DIR / "release-plan-valid.yaml"
            schema_file = SCHEMAS_DIR / "release-plan-schema.yaml"
            validator = MetadataValidator(metadata_file, schema_file=schema_file)

            result = validator.validate()

            assert result is True
            assert len(validator.errors) == 0

        def test_validate_with_file_checks_success(self, temp_metadata_dir):
            """Validation with file existence checks when files present"""
            # Create metadata file in temp directory
            metadata_file = temp_metadata_dir / "release-plan.yaml"
            metadata_content = """
repository:
  release_track: independent
  target_release_tag: r1.1
  target_release_type: public-release

apis:
  - api_name: test-api
    target_api_version: 1.0.0
    target_api_status: public
    main_contacts:
      - testuser
"""
            metadata_file.write_text(metadata_content)

            # Create the API definition file
            api_file = temp_metadata_dir / "code" / "API_definitions" / "test-api.yaml"
            api_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\n")

            validator = MetadataValidator(metadata_file, check_files=True)
            result = validator.validate()

            assert result is True
            assert len(validator.warnings) == 0

        def test_validate_strict_phase1_success(self):
            """Strict Phase 1 validation with null date and sha"""
            metadata_file = VALID_DIR / "release-metadata-phase1.yaml"
            validator = MetadataValidator(metadata_file, strict_phase1=True)

            result = validator.validate()

            assert result is True
            assert len(validator.errors) == 0

        def test_validate_release_type_none_allows_any_status(self):
            """Release type 'none' allows any API status"""
            metadata_file = VALID_DIR / "release-type-none.yaml"
            validator = MetadataValidator(metadata_file)

            result = validator.validate()

            assert result is True
            assert len(validator.errors) == 0

        def test_validate_warnings_still_succeeds(self, tmp_path):
            """Validation with warnings present but still succeeds"""
            # Create metadata with independent track but meta_release field present
            metadata_file = tmp_path / "test.yaml"
            metadata_content = """
repository:
  release_track: independent
  meta_release: Fall26
  target_release_tag: r1.1
  target_release_type: public-release

apis:
  - api_name: test-api
    target_api_version: 1.0.0
    target_api_status: public
    main_contacts:
      - testuser
"""
            metadata_file.write_text(metadata_content)
            validator = MetadataValidator(metadata_file)

            result = validator.validate()

            assert result is True
            assert len(validator.errors) == 0
            assert len(validator.warnings) > 0
            assert "independent" in validator.warnings[0]

    class TestFileErrors:
        """File I/O and YAML parsing errors"""

        def test_validate_metadata_file_not_found(self):
            """Metadata file doesn't exist"""
            metadata_file = Path("/nonexistent/file.yaml")
            validator = MetadataValidator(metadata_file)

            result = validator.validate()

            assert result is False
            assert len(validator.errors) > 0
            assert "not found" in validator.errors[0].lower()

        def test_validate_metadata_yaml_parse_error(self):
            """Metadata file has invalid YAML syntax"""
            metadata_file = INVALID_DIR / "invalid-yaml.yaml"
            validator = MetadataValidator(metadata_file)

            result = validator.validate()

            assert result is False
            assert len(validator.errors) > 0
            assert "yaml" in validator.errors[0].lower() or "parsing" in validator.errors[0].lower()

        def test_validate_schema_file_not_found(self):
            """Explicitly provided schema file doesn't exist"""
            metadata_file = VALID_DIR / "release-plan-valid.yaml"
            schema_file = Path("/nonexistent/schema.yaml")
            validator = MetadataValidator(metadata_file, schema_file=schema_file)

            result = validator.validate()

            assert result is False
            assert len(validator.errors) > 0
            assert "not found" in validator.errors[0].lower()

        def test_validate_schema_yaml_parse_error(self, tmp_path):
            """Schema file has invalid YAML"""
            metadata_file = VALID_DIR / "release-plan-valid.yaml"
            schema_file = tmp_path / "bad-schema.yaml"
            schema_file.write_text("invalid: yaml: content: [")
            validator = MetadataValidator(metadata_file, schema_file=schema_file)

            result = validator.validate()

            assert result is False
            assert len(validator.errors) > 0

    class TestSchemaDetection:
        """Schema type detection and finding"""

        def test_validate_unknown_schema_type_missing_repository(self):
            """Cannot detect type - missing 'repository' field"""
            metadata_file = INVALID_DIR / "missing-repository.yaml"
            validator = MetadataValidator(metadata_file)

            result = validator.validate()

            assert result is False
            assert len(validator.errors) > 0
            assert "cannot determine" in validator.errors[0].lower() or "unknown" in validator.errors[0].lower()

        def test_validate_unknown_schema_type_ambiguous(self, tmp_path):
            """Cannot detect type - ambiguous metadata structure"""
            metadata_file = tmp_path / "ambiguous.yaml"
            metadata_content = """
repository:
  some_field: value
apis:
  - api_name: test
"""
            metadata_file.write_text(metadata_content)
            validator = MetadataValidator(metadata_file)

            result = validator.validate()

            assert result is False
            assert len(validator.errors) > 0

        def test_validate_cannot_find_schema_file(self, tmp_path, monkeypatch):
            """Schema type detected but schema file doesn't exist"""
            # Create valid metadata in a location where schema files won't be found
            metadata_file = tmp_path / "test.yaml"
            metadata_content = """
repository:
  release_track: independent
  target_release_tag: r1.1
  target_release_type: public-release
apis:
  - api_name: test
    target_api_version: 1.0.0
    target_api_status: public
    main_contacts:
      - testuser
"""
            metadata_file.write_text(metadata_content)

            # Mock find_schema_file to return None
            validator = MetadataValidator(metadata_file)
            with patch.object(validator, 'find_schema_file', return_value=None):
                result = validator.validate()

            assert result is False
            assert len(validator.errors) > 0
            assert "cannot find schema" in validator.errors[0].lower()

    class TestSchemaValidation:
        """JSON schema validation failures"""

        def test_validate_schema_validation_failure(self, tmp_path):
            """Metadata doesn't match schema"""
            # Create metadata that violates schema
            metadata_file = tmp_path / "invalid-schema.yaml"
            metadata_content = """
repository:
  release_track: invalid-value
  target_release_tag: r1.1
  target_release_type: public-release
apis:
  - api_name: test
    target_api_version: 1.0.0
    target_api_status: public
    main_contacts:
      - testuser
"""
            metadata_file.write_text(metadata_content)
            validator = MetadataValidator(metadata_file)

            result = validator.validate()

            assert result is False
            assert len(validator.errors) > 0
            assert "schema validation" in validator.errors[0].lower() or "not one of" in validator.errors[0].lower()

        def test_validate_schema_validation_failure_with_path(self, tmp_path):
            """Schema validation error with specific path"""
            # Create metadata with missing required field
            metadata_file = tmp_path / "missing-field.yaml"
            metadata_content = """
repository:
  release_track: independent
  target_release_tag: r1.1

apis:
  - api_name: test
    target_api_version: 1.0.0
    target_api_status: public
"""
            metadata_file.write_text(metadata_content)
            validator = MetadataValidator(metadata_file)

            result = validator.validate()

            assert result is False
            assert len(validator.errors) > 0

    class TestSemanticValidation:
        """Semantic rule checking errors"""

        def test_validate_semantic_track_consistency_error(self):
            """release_track='meta-release' but no meta_release field"""
            metadata_file = INVALID_DIR / "meta-release-without-field.yaml"
            validator = MetadataValidator(metadata_file)

            result = validator.validate()

            assert result is False
            assert len(validator.errors) > 0
            assert "meta_release" in validator.errors[0] or "meta-release" in validator.errors[0]

        def test_validate_semantic_release_type_pre_alpha_with_draft(self):
            """target_release_type='pre-release-alpha' with draft APIs"""
            metadata_file = INVALID_DIR / "pre-alpha-with-draft.yaml"
            validator = MetadataValidator(metadata_file)

            result = validator.validate()

            assert result is False
            assert len(validator.errors) > 0
            assert "draft" in validator.errors[0]

        def test_validate_semantic_release_type_pre_rc_with_alpha(self):
            """target_release_type='pre-release-rc' with alpha APIs"""
            metadata_file = INVALID_DIR / "pre-rc-with-alpha.yaml"
            validator = MetadataValidator(metadata_file)

            result = validator.validate()

            assert result is False
            assert len(validator.errors) > 0
            assert ("alpha" in validator.errors[0] or "not rc/public" in validator.errors[0])

        def test_validate_semantic_release_type_public_with_non_public(self):
            """target_release_type='public-release' with non-public APIs"""
            metadata_file = INVALID_DIR / "public-release-with-rc.yaml"
            validator = MetadataValidator(metadata_file)

            result = validator.validate()

            assert result is False
            assert len(validator.errors) > 0
            assert "public" in validator.errors[0]

        def test_validate_semantic_release_type_maintenance_with_non_public(self, tmp_path):
            """target_release_type='maintenance-release' with non-public APIs"""
            metadata_file = tmp_path / "maintenance-invalid.yaml"
            metadata_content = """
repository:
  release_track: independent
  target_release_tag: r1.1
  target_release_type: maintenance-release

apis:
  - api_name: test-api
    target_api_version: 1.0.1
    target_api_status: rc
    main_contacts:
      - testuser
"""
            metadata_file.write_text(metadata_content)
            validator = MetadataValidator(metadata_file)

            result = validator.validate()

            assert result is False
            assert len(validator.errors) > 0
            assert "public" in validator.errors[0]

        def test_validate_strict_phase1_release_date_not_null(self):
            """strict_phase1=True but release_date is not null"""
            metadata_file = INVALID_DIR / "phase1-with-date.yaml"
            validator = MetadataValidator(metadata_file, strict_phase1=True)

            result = validator.validate()

            assert result is False
            assert len(validator.errors) > 0
            assert "release_date" in validator.errors[0] and "null" in validator.errors[0]

        def test_validate_strict_phase1_src_commit_sha_not_null(self, tmp_path):
            """strict_phase1=True but src_commit_sha is not null"""
            metadata_file = tmp_path / "phase1-with-sha.yaml"
            metadata_content = """
repository:
  repository_name: TestRepo
  release_tag: r4.1
  release_date: null
  release_type: public-release
  src_commit_sha: 7f3a9b2c8e1d4f6a0b5c7e9d3f8a1c4e6b9d2f5a

dependencies:
  commonalities_release: r4.2 (1.0.0)

apis:
  - api_name: test-api
    api_version: 1.0.0
    api_title: "Test API"
"""
            metadata_file.write_text(metadata_content)
            validator = MetadataValidator(metadata_file, strict_phase1=True)

            result = validator.validate()

            assert result is False
            assert len(validator.errors) > 0
            assert "src_commit_sha" in validator.errors[0] and "null" in validator.errors[0]

    class TestFileChecks:
        """Optional file existence checking"""

        def test_validate_file_checks_missing_api_file(self, temp_metadata_dir):
            """check_files=True, non-draft API file missing (warning)"""
            metadata_file = temp_metadata_dir / "release-plan.yaml"
            metadata_content = """
repository:
  release_track: independent
  target_release_tag: r1.1
  target_release_type: public-release

apis:
  - api_name: missing-api
    target_api_version: 1.0.0
    target_api_status: public
    main_contacts:
      - testuser
"""
            metadata_file.write_text(metadata_content)
            validator = MetadataValidator(metadata_file, check_files=True)

            result = validator.validate()

            assert result is True
            assert len(validator.warnings) > 0
            assert "missing-api" in validator.warnings[0]

        def test_validate_file_checks_skips_draft_apis(self, temp_metadata_dir):
            """check_files=True, draft API has no file (no warning)"""
            metadata_file = temp_metadata_dir / "release-plan.yaml"
            metadata_content = """
repository:
  release_track: independent
  target_release_tag: null
  target_release_type: none

apis:
  - api_name: draft-api
    target_api_version: 0.1.0
    target_api_status: draft
    main_contacts:
      - testuser
"""
            metadata_file.write_text(metadata_content)
            validator = MetadataValidator(metadata_file, check_files=True)

            result = validator.validate()

            assert result is True
            assert len(validator.warnings) == 0

    class TestEdgeCases:
        """Edge cases and boundary conditions"""

        def test_validate_print_output_format(self, capsys):
            """Verify print statements for detected type and schema path"""
            metadata_file = VALID_DIR / "release-plan-valid.yaml"
            validator = MetadataValidator(metadata_file)

            validator.validate()

            captured = capsys.readouterr()
            assert "Detected metadata type:" in captured.out
            assert "release-plan" in captured.out
            assert "Using schema:" in captured.out

        def test_validate_multiple_calls_accumulate_errors(self):
            """Multiple validate() calls accumulate errors"""
            metadata_file = INVALID_DIR / "pre-alpha-with-draft.yaml"
            validator = MetadataValidator(metadata_file)

            # First validation
            result1 = validator.validate()
            error_count1 = len(validator.errors)

            # Second validation on same instance
            result2 = validator.validate()
            error_count2 = len(validator.errors)

            assert result1 is False
            assert result2 is False
            assert error_count2 >= error_count1

        def test_validate_empty_errors_list_returns_true(self):
            """Empty errors list returns True"""
            metadata_file = VALID_DIR / "release-plan-valid.yaml"
            validator = MetadataValidator(metadata_file)

            result = validator.validate()

            assert len(validator.errors) == 0
            assert result is True


class TestParameterizedReleaseTypeConsistency:
    """Parameterized tests for release type consistency rules"""

    @pytest.mark.parametrize("release_type,api_status,should_fail", [
        ("pre-release-alpha", "draft", True),
        ("pre-release-alpha", "alpha", False),
        ("pre-release-alpha", "rc", False),
        ("pre-release-alpha", "public", False),
        ("pre-release-rc", "draft", True),
        ("pre-release-rc", "alpha", True),
        ("pre-release-rc", "rc", False),
        ("pre-release-rc", "public", False),
        ("public-release", "draft", True),
        ("public-release", "alpha", True),
        ("public-release", "rc", True),
        ("public-release", "public", False),
        ("maintenance-release", "public", False),
        ("none", "draft", False),
        ("none", "alpha", False),
        ("none", "public", False),
    ])
    def test_release_type_consistency(self, tmp_path, release_type, api_status, should_fail):
        """Test different combinations of release types and API statuses"""
        metadata_file = tmp_path / f"test-{release_type}-{api_status}.yaml"
        metadata_content = f"""
repository:
  release_track: independent
  target_release_tag: {'null' if release_type == 'none' else 'r1.1'}
  target_release_type: {release_type}

apis:
  - api_name: test-api
    target_api_version: 1.0.0
    target_api_status: {api_status}
    main_contacts:
      - testuser
"""
        metadata_file.write_text(metadata_content)
        validator = MetadataValidator(metadata_file)

        result = validator.validate()

        if should_fail:
            assert result is False
            assert len(validator.errors) > 0
        else:
            assert result is True
            assert len(validator.errors) == 0

#!/usr/bin/env python3
"""
CAMARA API Review Validator - Enhanced Version with Subscription Type Detection v0.6
Automated validation of CAMARA API definitions with proper subscription API classification

Enhanced features:
- Differentiated validation for explicit vs implicit subscription APIs
- Proper classification of subscription API types
- Targeted validation checks based on API type
- All previous validation features maintained
"""

import os
import sys
import yaml
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import datetime
import traceback

class Severity(Enum):
    CRITICAL = "🔴 Critical"
    MEDIUM = "🟡 Medium"
    LOW = "🔵 Low"
    INFO = "ℹ️ Info"

class APIType(Enum):
    REGULAR = "Regular API"
    IMPLICIT_SUBSCRIPTION = "Implicit Subscription API"
    EXPLICIT_SUBSCRIPTION = "Explicit Subscription API"

@dataclass
class ValidationIssue:
    severity: Severity
    category: str
    description: str
    location: str = ""
    fix_suggestion: str = ""
    
@dataclass
class ValidationResult:
    api_name: str = ""
    version: str = ""
    file_path: str = ""
    api_type: APIType = APIType.REGULAR
    issues: List[ValidationIssue] = field(default_factory=list)
    checks_performed: List[str] = field(default_factory=list)
    manual_checks_needed: List[str] = field(default_factory=list)
    
    @property
    def critical_count(self) -> int:
        return len([i for i in self.issues if i.severity == Severity.CRITICAL])
    
    @property
    def medium_count(self) -> int:
        return len([i for i in self.issues if i.severity == Severity.MEDIUM])
    
    @property
    def low_count(self) -> int:
        return len([i for i in self.issues if i.severity == Severity.LOW])

@dataclass
class ConsistencyResult:
    issues: List[ValidationIssue] = field(default_factory=list)
    checks_performed: List[str] = field(default_factory=list)

@dataclass
class TestAlignmentResult:
    api_file: str = ""
    test_files: List[str] = field(default_factory=list)
    issues: List[ValidationIssue] = field(default_factory=list)
    checks_performed: List[str] = field(default_factory=list)

class CAMARAAPIValidator:
    def __init__(self, expected_commonalities_version: str = "0.6"):
        self.expected_commonalities_version = expected_commonalities_version
        self.reserved_words = self._load_reserved_words()
        
    def _load_reserved_words(self) -> set:
        """Load reserved words from common OpenAPI generators"""
        return {
            # Python Flask reserved words
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del', 'elif', 'else',
            'except', 'exec', 'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
            'lambda', 'not', 'or', 'pass', 'print', 'raise', 'return', 'try', 'while', 'with', 'yield',
            # Java reserved words
            'abstract', 'boolean', 'byte', 'catch', 'char', 'double', 'final', 'float', 'int', 'interface',
            'long', 'native', 'new', 'package', 'private', 'protected', 'public', 'short', 'static', 'super',
            'synchronized', 'this', 'throw', 'throws', 'transient', 'void', 'volatile',
            # Common reserved words
            'default', 'switch', 'case', 'const', 'var', 'let', 'function', 'null', 'undefined'
        }

    def _determine_api_type(self, spec: dict) -> APIType:
        """Determine the type of API: Regular, Implicit Subscription, or Explicit Subscription"""
        
        title = spec.get('info', {}).get('title', '').lower()
        paths = spec.get('paths', {})
        schemas = spec.get('components', {}).get('schemas', {})
        
        # 1. Check for Explicit Subscription APIs
        # These have dedicated subscription management endpoints
        if 'subscription' in title:
            return APIType.EXPLICIT_SUBSCRIPTION
            
        # Check for subscription endpoints
        for path in paths.keys():
            if path.endswith('/subscriptions') or '/subscriptions/' in path:
                return APIType.EXPLICIT_SUBSCRIPTION
        
        # 2. Check for Implicit Subscription APIs
        # These support notifications via resource creation (sink parameter)
        
        # Check for CloudEvent schemas (indicates notification capability)
        if 'CloudEvent' in schemas:
            return APIType.IMPLICIT_SUBSCRIPTION
            
        # Check for SinkCredential schemas (indicates sink support)
        if 'SinkCredential' in schemas or any('SinkCredential' in name for name in schemas.keys()):
            return APIType.IMPLICIT_SUBSCRIPTION
            
        # Check for callback operations in any path
        for path_obj in paths.values():
            for operation in path_obj.values():
                if isinstance(operation, dict) and 'callbacks' in operation:
                    return APIType.IMPLICIT_SUBSCRIPTION
        
        # Check for sink-related properties in schemas
        for schema_name, schema in schemas.items():
            if isinstance(schema, dict):
                properties = schema.get('properties', {})
                if 'sink' in properties or 'sinkCredential' in properties:
                    return APIType.IMPLICIT_SUBSCRIPTION
        
        # 3. Default to Regular API
        return APIType.REGULAR

    def validate_api_file(self, file_path: str) -> ValidationResult:
        """Validate a single API YAML file"""
        result = ValidationResult(file_path=file_path)
        
        try:
            # Load and parse YAML
            with open(file_path, 'r', encoding='utf-8') as f:
                api_spec = yaml.safe_load(f)
            
            if not api_spec:
                result.issues.append(ValidationIssue(
                    Severity.CRITICAL, "File Structure", "Empty or invalid YAML file"
                ))
                return result
            
            # Extract basic info and determine API type
            result.api_name = api_spec.get('info', {}).get('title', 'Unknown')
            result.version = api_spec.get('info', {}).get('version', 'Unknown')
            result.api_type = self._determine_api_type(api_spec)
            
            # Run all validation checks
            self._check_openapi_version(api_spec, result)
            self._check_info_object(api_spec, result)
            self._check_servers_object(api_spec, result)
            self._check_external_docs(api_spec, result)
            self._check_security_schemes(api_spec, result)
            self._check_error_responses(api_spec, result)
            self._check_x_correlator(api_spec, result)
            self._check_date_time_fields(api_spec, result)
            self._check_reserved_words(api_spec, result)
            self._check_device_schema(api_spec, result)
            self._check_file_naming(file_path, api_spec, result)
            
            # Enhanced checks for Commonalities 0.6
            self._check_work_in_progress_version(api_spec, result)
            self._check_updated_generic401(api_spec, result)
            
            # Enhanced consistency checks
            self._check_scope_naming_patterns(api_spec, result)
            self._check_deep_filename_consistency(file_path, api_spec, result)
            
            # Apply type-specific validation checks
            if result.api_type == APIType.EXPLICIT_SUBSCRIPTION:
                self._check_explicit_subscription_compliance(api_spec, result)
            elif result.api_type == APIType.IMPLICIT_SUBSCRIPTION:
                self._check_implicit_subscription_compliance(api_spec, result)
            
            # Add manual checks needed based on API type
            result.manual_checks_needed = self._get_manual_checks_for_type(result.api_type)
            
        except yaml.YAMLError as e:
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "YAML Syntax", f"YAML parsing error: {str(e)}"
            ))
        except Exception as e:
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Validation Error", f"Unexpected error: {str(e)}"
            ))
        
        return result

    def _get_manual_checks_for_type(self, api_type: APIType) -> List[str]:
        """Get manual checks needed based on API type"""
        common_checks = [
            "Business logic appropriateness review",
            "Documentation quality assessment", 
            "API design patterns validation",
            "Use case coverage evaluation",
            "Security considerations beyond structure",
            "Performance and scalability considerations"
        ]
        
        if api_type == APIType.EXPLICIT_SUBSCRIPTION:
            return common_checks + [
                "Cross-file reference validation (if multi-API)",
                "Event subscription flow testing", 
                "Subscription lifecycle management testing",
                "Event notification delivery testing"
            ]
        elif api_type == APIType.IMPLICIT_SUBSCRIPTION:
            return common_checks + [
                "Notification callback testing",
                "Sink credential validation testing",
                "Resource-bound notification flow testing"
            ]
        else:
            return common_checks + [
                "Cross-file reference validation (if multi-API)"
            ]

    def _check_explicit_subscription_compliance(self, spec: dict, result: ValidationResult):
        """Check compliance for explicit subscription APIs"""
        result.checks_performed.append("Explicit subscription API compliance validation")
        
        # Check for subscription endpoint
        paths = spec.get('paths', {})
        has_subscriptions_path = False
        
        for path in paths.keys():
            if path.endswith('/subscriptions') or '/subscriptions/' in path:
                has_subscriptions_path = True
                break
        
        if not has_subscriptions_path:
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Explicit Subscriptions",
                "Explicit subscription API must have /subscriptions endpoint",
                "paths",
                "Add /subscriptions endpoint for subscription management"
            ))
        
        # Apply all subscription-specific checks
        self._check_cloudevents_compliance(spec, result)
        self._check_event_type_naming(spec, result)
        self._check_subscription_lifecycle_events(spec, result)
        self._check_sink_validation(spec, result)
        self._check_subscription_error_codes(spec, result)

    def _check_implicit_subscription_compliance(self, spec: dict, result: ValidationResult):
        """Check compliance for implicit subscription APIs"""
        result.checks_performed.append("Implicit subscription API compliance validation")
        
        # Check for CloudEvents compliance if CloudEvent schemas exist
        schemas = spec.get('components', {}).get('schemas', {})
        if 'CloudEvent' in schemas:
            self._check_cloudevents_compliance(spec, result)
        
        # Check for callback operations
        paths = spec.get('paths', {})
        has_callbacks = False
        
        for path_obj in paths.values():
            for operation in path_obj.values():
                if isinstance(operation, dict) and 'callbacks' in operation:
                    has_callbacks = True
                    break
            if has_callbacks:
                break
        
        if not has_callbacks and 'CloudEvent' in schemas:
            result.issues.append(ValidationIssue(
                Severity.MEDIUM, "Implicit Subscriptions",
                "API has CloudEvent schemas but no callback operations defined",
                "paths",
                "Add callback operations for notification delivery"
            ))
        
        # Check sink credential implementation
        if 'SinkCredential' in schemas or any('sink' in name.lower() for name in schemas.keys()):
            self._check_sink_credential_compliance(spec, result)
        
        # Should NOT have subscription endpoints (that's for explicit APIs)
        for path in paths.keys():
            if path.endswith('/subscriptions') or '/subscriptions/' in path:
                result.issues.append(ValidationIssue(
                    Severity.MEDIUM, "Implicit Subscriptions",
                    "Implicit subscription API should not have /subscriptions endpoint",
                    f"paths.{path}",
                    "Remove /subscriptions endpoint or reclassify as explicit subscription API"
                ))

    def _check_sink_credential_compliance(self, spec: dict, result: ValidationResult):
        """Check sink credential implementation for implicit subscriptions"""
        result.checks_performed.append("Sink credential compliance validation")
        
        schemas = spec.get('components', {}).get('schemas', {})
        sink_credential = schemas.get('SinkCredential')
        
        if sink_credential:
            # Check for discriminator
            discriminator = sink_credential.get('discriminator')
            if not discriminator:
                result.issues.append(ValidationIssue(
                    Severity.MEDIUM, "Sink Credentials",
                    "SinkCredential schema should use discriminator pattern",
                    "components.schemas.SinkCredential.discriminator"
                ))
            
            # Check for AccessTokenCredential support
            if 'AccessTokenCredential' not in schemas:
                result.issues.append(ValidationIssue(
                    Severity.MEDIUM, "Sink Credentials", 
                    "Missing AccessTokenCredential schema for sink authentication",
                    "components.schemas.AccessTokenCredential"
                ))

    # ===========================================
    # Event Subscription Validation Functions (for explicit subscriptions)
    # ===========================================

    def _check_cloudevents_compliance(self, spec: dict, result: ValidationResult):
        """Check CloudEvents compliance for notification callbacks"""
        result.checks_performed.append("CloudEvents compliance validation")
        
        schemas = spec.get('components', {}).get('schemas', {})
        cloud_event = schemas.get('CloudEvent', {})
        
        if cloud_event:
            # Check required CloudEvent fields
            required_fields = cloud_event.get('required', [])
            expected_fields = ['id', 'source', 'specversion', 'type', 'time']
            
            for field in expected_fields:
                if field not in required_fields:
                    result.issues.append(ValidationIssue(
                        Severity.CRITICAL, "CloudEvents",
                        f"CloudEvent missing required field: {field}",
                        "components.schemas.CloudEvent.required"
                    ))
            
            # Check specversion enum
            properties = cloud_event.get('properties', {})
            specversion = properties.get('specversion', {})
            enum_values = specversion.get('enum', [])
            
            if '1.0' not in enum_values:
                result.issues.append(ValidationIssue(
                    Severity.CRITICAL, "CloudEvents",
                    "CloudEvent specversion must include '1.0'",
                    "components.schemas.CloudEvent.properties.specversion.enum"
                ))
            
            # Check datacontenttype enum
            datacontenttype = properties.get('datacontenttype', {})
            enum_values = datacontenttype.get('enum', [])
            
            if 'application/json' not in enum_values:
                result.issues.append(ValidationIssue(
                    Severity.CRITICAL, "CloudEvents",
                    "CloudEvent datacontenttype must include 'application/json'",
                    "components.schemas.CloudEvent.properties.datacontenttype.enum"
                ))

    def _check_event_type_naming(self, spec: dict, result: ValidationResult):
        """Check event type naming follows CAMARA pattern"""
        result.checks_performed.append("Event type naming validation")
        
        schemas = spec.get('components', {}).get('schemas', {})
        
        # Check event type enums
        for schema_name, schema in schemas.items():
            if 'EventType' in schema_name and schema.get('type') == 'string':
                enum_values = schema.get('enum', [])
                
                for event_type in enum_values:
                    if not re.match(r'^org\.camaraproject\.[a-z0-9-]+\.v\d+\.[a-z0-9-]+$', event_type):
                        result.issues.append(ValidationIssue(
                            Severity.MEDIUM, "Event Type Naming",
                            f"Event type doesn't follow CAMARA pattern: {event_type}",
                            f"components.schemas.{schema_name}.enum",
                            "Use pattern: org.camaraproject.<api-name>.v<version>.<event-name>"
                        ))

    def _check_subscription_lifecycle_events(self, spec: dict, result: ValidationResult):
        """Check for standard subscription lifecycle events"""
        result.checks_performed.append("Subscription lifecycle events validation")
        
        schemas = spec.get('components', {}).get('schemas', {})
        
        # Check for lifecycle event schemas
        lifecycle_events = [
            'subscription-started',
            'subscription-updated', 
            'subscription-ended'
        ]
        
        found_events = []
        for schema_name, schema in schemas.items():
            if 'EventType' in schema_name and schema.get('type') == 'string':
                enum_values = schema.get('enum', [])
                for event_type in enum_values:
                    for lifecycle_event in lifecycle_events:
                        if lifecycle_event in event_type:
                            found_events.append(lifecycle_event)
        
        # Check termination reasons if subscription-ended exists
        if 'subscription-ended' in found_events:
            termination_schema = schemas.get('TerminationReason', {})
            if termination_schema:
                enum_values = termination_schema.get('enum', [])
                required_reasons = [
                    'NETWORK_TERMINATED',
                    'SUBSCRIPTION_EXPIRED',
                    'MAX_EVENTS_REACHED',
                    'ACCESS_TOKEN_EXPIRED',
                    'SUBSCRIPTION_DELETED'
                ]
                
                for reason in required_reasons:
                    if reason not in enum_values:
                        result.issues.append(ValidationIssue(
                            Severity.MEDIUM, "Subscription Events",
                            f"Missing termination reason: {reason}",
                            "components.schemas.TerminationReason.enum"
                        ))

    def _check_sink_validation(self, spec: dict, result: ValidationResult):
        """Check sink property validation for subscriptions"""
        result.checks_performed.append("Sink validation")
        
        # Check for INVALID_SINK error response
        responses = spec.get('components', {}).get('responses', {})
        found_invalid_sink = False
        
        for response_name, response in responses.items():
            content = response.get('content', {})
            app_json = content.get('application/json', {})
            schema = app_json.get('schema', {})
            
            # Check in allOf structure
            all_of = schema.get('allOf', [])
            for item in all_of:
                properties = item.get('properties', {})
                code_prop = properties.get('code', {})
                enum_values = code_prop.get('enum', [])
                
                if 'INVALID_SINK' in enum_values:
                    found_invalid_sink = True
                    break
        
        if not found_invalid_sink:
            result.issues.append(ValidationIssue(
                Severity.MEDIUM, "Sink Validation",
                "Missing INVALID_SINK error response",
                "components.responses",
                "Add 400 INVALID_SINK error response for sink validation"
            ))

    def _check_subscription_error_codes(self, spec: dict, result: ValidationResult):
        """Check subscription-specific error codes"""
        result.checks_performed.append("Subscription error codes validation")
        
        # Check for device-related error codes
        required_device_errors = [
            'MISSING_IDENTIFIER',
            'UNNECESSARY_IDENTIFIER',
            'UNSUPPORTED_IDENTIFIER',
            'SERVICE_NOT_APPLICABLE'
        ]
        
        responses = spec.get('components', {}).get('responses', {})
        found_errors = set()
        
        for response_name, response in responses.items():
            content = response.get('content', {})
            app_json = content.get('application/json', {})
            schema = app_json.get('schema', {})
            
            all_of = schema.get('allOf', [])
            for item in all_of:
                properties = item.get('properties', {})
                code_prop = properties.get('code', {})
                enum_values = code_prop.get('enum', [])
                
                for error in required_device_errors:
                    if error in enum_values:
                        found_errors.add(error)
        
        for error in required_device_errors:
            if error not in found_errors:
                result.issues.append(ValidationIssue(
                    Severity.LOW, "Error Responses",
                    f"Missing device error code: {error}",
                    "components.responses",
                    f"Add 422 {error} error response for device validation"
                ))

    # ===========================================
    # Updated Scope Naming Pattern Check
    # ===========================================

    def _check_scope_naming_patterns(self, spec: dict, result: ValidationResult):
        """Check scope naming follows CAMARA patterns"""
        result.checks_performed.append("Scope naming pattern validation")
        
        # Extract api-name from server URL
        servers = spec.get('servers', [])
        if not servers:
            return
            
        server_url = servers[0].get('url', '')
        api_name_match = re.search(r'/([a-z0-9-]+)/v[\d\w\.]+', server_url)
        if not api_name_match:
            return
            
        api_name = api_name_match.group(1)
        
        # Check security scopes in operations
        paths = spec.get('paths', {})
        for path, path_obj in paths.items():
            for method, operation in path_obj.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    security = operation.get('security', [])
                    for sec_req in security:
                        for scheme_name, scopes in sec_req.items():
                            if scheme_name == 'openId':
                                for scope in scopes:
                                    self._validate_scope_pattern(scope, api_name, 
                                                               result.api_type, 
                                                               operation, result)

    def _validate_scope_pattern(self, scope: str, api_name: str, api_type: APIType, 
                               operation: dict, result: ValidationResult):
        """Validate individual scope against CAMARA naming patterns"""
        
        if api_type == APIType.EXPLICIT_SUBSCRIPTION:
            # For explicit subscription APIs: {api-name}:{event-type}:{action} or {api-name}:{resource}:{action}
            if scope.startswith(f'{api_name}:org.camaraproject.'):
                # Event-specific scope
                pattern = rf'^{re.escape(api_name)}:org\.camaraproject\.[a-z0-9-]+\.v\d+\.[a-z0-9-]+:(create|read|write|delete)$'
                if not re.match(pattern, scope):
                    result.issues.append(ValidationIssue(
                        Severity.MEDIUM, "Scope Naming",
                        f"Event-specific scope doesn't follow pattern: {scope}",
                        f"Expected: {api_name}:org.camaraproject.<api-name>.v<version>.<event-name>:<action>",
                        "Use correct event-specific scope pattern"
                    ))
            elif ':' in scope:
                # Resource-based scope: subscriptions:read
                parts = scope.split(':')
                if len(parts) != 2:
                    result.issues.append(ValidationIssue(
                        Severity.MEDIUM, "Scope Naming",
                        f"Explicit subscription scope should have 2 parts: {scope}",
                        f"Expected: {api_name}:<action>"
                    ))
                elif parts[0] != api_name:
                    result.issues.append(ValidationIssue(
                        Severity.MEDIUM, "Scope Naming",
                        f"Scope API name mismatch: expected '{api_name}', got '{parts[0]}'",
                        f"Use: {api_name}:{parts[1]}"
                    ))
        else:
            # For regular and implicit subscription APIs: {api-name}:{resource}:{action} or {api-name}:{action}
            parts = scope.split(':')
            if len(parts) == 2:
                # Simple scope: api-name:action
                if parts[0] != api_name:
                    result.issues.append(ValidationIssue(
                        Severity.MEDIUM, "Scope Naming",
                        f"Scope API name mismatch: expected '{api_name}', got '{parts[0]}'",
                        f"Use: {api_name}:{parts[1]}"
                    ))
            elif len(parts) == 3:
                # Resource-based scope: api-name:resource:action  
                if parts[0] != api_name:
                    result.issues.append(ValidationIssue(
                        Severity.MEDIUM, "Scope Naming",
                        f"Scope API name mismatch: expected '{api_name}', got '{parts[0]}'",
                        f"Use: {api_name}:{parts[1]}:{parts[2]}"
                    ))
            else:
                result.issues.append(ValidationIssue(
                    Severity.MEDIUM, "Scope Naming",
                    f"Scope doesn't follow CAMARA pattern: {scope}",
                    f"Expected: {api_name}:<action> or {api_name}:<resource>:<action>"
                ))

    # ===========================================
    # Existing Validation Functions (unchanged from original)
    # ===========================================

    def _check_deep_filename_consistency(self, file_path: str, spec: dict, result: ValidationResult):
        """Extract api-name from server URL and compare with filename"""
        result.checks_performed.append("Deep filename consistency validation")
        
        filename = Path(file_path).stem
        
        # Extract api-name from server URL
        servers = spec.get('servers', [])
        if not servers:
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Filename Consistency",
                "No servers object found for filename validation",
                "servers"
            ))
            return
            
        server_url = servers[0].get('url', '')
        
        # Parse server URL to extract api-name
        url_pattern = r'\{[^}]+\}/([a-z0-9-]+)/v[\d\w\.]+'
        match = re.search(url_pattern, server_url)
        
        if not match:
            result.issues.append(ValidationIssue(
                Severity.MEDIUM, "Filename Consistency",
                f"Cannot extract api-name from server URL: {server_url}",
                "servers[0].url",
                "Use format: {apiRoot}/api-name/version"
            ))
            return
            
        url_api_name = match.group(1)
        
        # Check exact match
        if filename != url_api_name:
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Filename Consistency",
                f"Filename '{filename}' doesn't match server URL api-name '{url_api_name}'",
                file_path,
                f"Rename file to '{url_api_name}.yaml' or update server URL"
            ))
        
        # Check title consistency with extracted api-name
        title = spec.get('info', {}).get('title', '')
        expected_title_words = url_api_name.replace('-', ' ').title()
        
        # Convert title to comparable format
        title_normalized = re.sub(r'\s+', ' ', title.lower().strip())
        expected_normalized = expected_title_words.lower()
        
        if not self._titles_match(title_normalized, expected_normalized):
            result.issues.append(ValidationIssue(
                Severity.MEDIUM, "Filename Consistency",
                f"Title '{title}' doesn't align with api-name '{url_api_name}'",
                "info.title",
                f"Consider title that relates to '{expected_title_words}'"
            ))

    def _titles_match(self, title_normalized: str, expected_normalized: str) -> bool:
        """Check if titles are reasonably consistent"""
        # Remove common words and check if main words match
        common_words = {'api', 'service', 'the', 'a', 'an', 'for', 'and', 'or', 'of', 'on', 'in'}
        
        title_words = set(title_normalized.split()) - common_words
        expected_words = set(expected_normalized.split()) - common_words
        
        # Check if there's significant overlap
        if len(expected_words) == 0:
            return True
            
        overlap = len(title_words & expected_words)
        return overlap / len(expected_words) >= 0.5

    def _check_openapi_version(self, spec: dict, result: ValidationResult):
        """Check OpenAPI version compliance"""
        result.checks_performed.append("OpenAPI version validation")
        
        openapi_version = spec.get('openapi')
        if openapi_version != '3.0.3':
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "OpenAPI Version",
                f"Must use OpenAPI 3.0.3, found: {openapi_version}",
                "Root level",
                "Set 'openapi: 3.0.3'"
            ))

    def _check_info_object(self, spec: dict, result: ValidationResult):
        """Check info object compliance"""
        result.checks_performed.append("Info object validation")
        
        info = spec.get('info', {})
        
        # Title check
        title = info.get('title', '')
        if 'API' in title:
            result.issues.append(ValidationIssue(
                Severity.MEDIUM, "Info Object",
                f"Title should not include 'API': {title}",
                "info.title",
                "Remove 'API' from title"
            ))
        
        # Version check (enhanced for wip detection)
        version = info.get('version', '')
        if version != 'wip' and not re.match(r'^\d+\.\d+\.\d+(-rc\.\d+|-alpha\.\d+)?$', version):
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Info Object",
                f"Invalid version format: {version}",
                "info.version",
                "Use semantic versioning (x.y.z or x.y.z-rc.n)"
            ))
        
        # License check
        license_info = info.get('license', {})
        if license_info.get('name') != 'Apache 2.0':
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Info Object",
                "License must be 'Apache 2.0'",
                "info.license.name"
            ))
        
        if license_info.get('url') != 'https://www.apache.org/licenses/LICENSE-2.0.html':
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Info Object",
                "Incorrect license URL",
                "info.license.url"
            ))
        
        # Commonalities version
        commonalities = info.get('x-camara-commonalities')
        if str(commonalities) != self.expected_commonalities_version:
            result.issues.append(ValidationIssue(
                Severity.MEDIUM, "Info Object",
                f"Expected commonalities {self.expected_commonalities_version}, found: {commonalities}",
                "info.x-camara-commonalities"
            ))
        
        # Forbidden fields
        if 'termsOfService' in info:
            result.issues.append(ValidationIssue(
                Severity.MEDIUM, "Info Object",
                "termsOfService field is forbidden",
                "info.termsOfService",
                "Remove termsOfService field"
            ))
        
        if 'contact' in info:
            result.issues.append(ValidationIssue(
                Severity.MEDIUM, "Info Object",
                "contact field is forbidden",
                "info.contact",
                "Remove contact field"
            ))
        
        # Check mandatory description templates
        description = info.get('description', '')
        if 'Authorization and authentication' not in description:
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Info Object",
                "Missing mandatory 'Authorization and authentication' section",
                "info.description"
            ))
        
        if 'Additional CAMARA error responses' not in description:
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Info Object",
                "Missing mandatory 'Additional CAMARA error responses' section",
                "info.description"
            ))

    def _check_servers_object(self, spec: dict, result: ValidationResult):
        """Check servers object compliance"""
        result.checks_performed.append("Servers object validation")
        
        servers = spec.get('servers', [])
        if not servers:
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Servers Object",
                "Missing servers object",
                "servers"
            ))
            return
        
        server = servers[0]
        url = server.get('url', '')
        
        # Extract version from info for validation
        version = spec.get('info', {}).get('version', '')
        
        # Enhanced check for wip versions
        if version == 'wip' and 'vwip' not in url:
            result.issues.append(ValidationIssue(
                Severity.MEDIUM, "Servers Object",
                "WIP version should use 'vwip' in URL or be updated to proper version",
                "servers[0].url"
            ))
        
        # Check URL format for RC versions
        if '-rc.' in version and version != 'wip':
            match = re.match(r'^(\d+)\.(\d+)\.(\d+)-rc\.(\d+)$', version)
            if match:
                major, minor, patch, rc_num = match.groups()
                if major == '0':
                    expected_url_pattern = f"v{major}.{minor}rc{rc_num}"
                else:
                    expected_url_pattern = f"v{major}rc{rc_num}"
                
                if expected_url_pattern not in url:
                    result.issues.append(ValidationIssue(
                        Severity.CRITICAL, "Servers Object",
                        f"Incorrect URL version format. Expected pattern: {expected_url_pattern}",
                        "servers[0].url"
                    ))
        
        # Check apiRoot variable
        variables = server.get('variables', {})
        api_root = variables.get('apiRoot', {})
        if api_root.get('default') != 'http://localhost:9091':
            result.issues.append(ValidationIssue(
                Severity.MEDIUM, "Servers Object",
                "apiRoot default should be 'http://localhost:9091'",
                "servers[0].variables.apiRoot.default"
            ))

    def _check_external_docs(self, spec: dict, result: ValidationResult):
        """Check externalDocs object"""
        result.checks_performed.append("ExternalDocs validation")
        
        external_docs = spec.get('externalDocs')
        if not external_docs:
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "ExternalDocs",
                "Missing externalDocs object",
                "externalDocs",
                "Add externalDocs with GitHub repository URL"
            ))
        else:
            description = external_docs.get('description', '')
            if 'Product documentation at CAMARA' not in description:
                # Truncate description for display
                truncated_desc = description[:60] + "..." if len(description) > 60 else description
                result.issues.append(ValidationIssue(
                    Severity.MEDIUM, "ExternalDocs",
                    f"Should use standard description: 'Product documentation at CAMARA'. Found: '{truncated_desc}'",
                    "externalDocs.description",
                    "Change description to: 'Product documentation at CAMARA'"
                ))
            
            url = external_docs.get('url', '')
            if not url.startswith('https://github.com/camaraproject/'):
                result.issues.append(ValidationIssue(
                    Severity.MEDIUM, "ExternalDocs",
                    "URL should point to camaraproject GitHub repository",
                    "externalDocs.url"
                ))

    def _check_security_schemes(self, spec: dict, result: ValidationResult):
        """Check security schemes compliance"""
        result.checks_performed.append("Security schemes validation")
        
        components = spec.get('components', {})
        security_schemes = components.get('securitySchemes', {})
        
        # Check for openId scheme
        open_id = security_schemes.get('openId')
        if not open_id:
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Security Schemes",
                "Missing 'openId' security scheme",
                "components.securitySchemes.openId"
            ))
        elif open_id.get('type') != 'openIdConnect':
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Security Schemes",
                "openId scheme must have type 'openIdConnect'",
                "components.securitySchemes.openId.type"
            ))
        
        # Check for undefined security scheme references
        paths = spec.get('paths', {})
        for path, path_obj in paths.items():
            for method, operation in path_obj.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    security = operation.get('security', [])
                    for sec_req in security:
                        for scheme_name in sec_req.keys():
                            if scheme_name not in security_schemes:
                                result.issues.append(ValidationIssue(
                                    Severity.CRITICAL, "Security Schemes",
                                    f"Undefined security scheme '{scheme_name}' referenced",
                                    f"paths.{path}.{method}.security"
                                ))

    def _check_error_responses(self, spec: dict, result: ValidationResult):
        """Check error response compliance"""
        result.checks_performed.append("Error responses validation")
        
        components = spec.get('components', {})
        responses = components.get('responses', {})
        
        # Check for forbidden error codes
        forbidden_codes = ['AUTHENTICATION_REQUIRED', 'IDENTIFIER_MISMATCH']
        
        for response_name, response_obj in responses.items():
            content = response_obj.get('content', {})
            app_json = content.get('application/json', {})
            schema = app_json.get('schema', {})
            
            # Check allOf structure
            all_of = schema.get('allOf', [])
            if all_of:
                for item in all_of:
                    properties = item.get('properties', {})
                    code_prop = properties.get('code', {})
                    enum_values = code_prop.get('enum', [])
                    
                    for forbidden_code in forbidden_codes:
                        if forbidden_code in enum_values:
                            result.issues.append(ValidationIssue(
                                Severity.CRITICAL, "Error Responses",
                                f"Forbidden error code '{forbidden_code}' found",
                                f"components.responses.{response_name}",
                                f"Remove '{forbidden_code}' from error codes"
                            ))
            
            # Check examples for forbidden codes
            examples = app_json.get('examples', {})
            for example_name, example_obj in examples.items():
                example_value = example_obj.get('value', {})
                if example_value.get('code') in forbidden_codes:
                    result.issues.append(ValidationIssue(
                        Severity.CRITICAL, "Error Responses",
                        f"Forbidden error code in example '{example_name}'",
                        f"components.responses.{response_name}.examples.{example_name}"
                    ))

    def _check_x_correlator(self, spec: dict, result: ValidationResult):
        """Check x-correlator implementation"""
        result.checks_performed.append("X-Correlator validation")
        
        components = spec.get('components', {})
        schemas = components.get('schemas', {})
        
        # Check XCorrelator schema
        x_correlator = schemas.get('XCorrelator')
        if not x_correlator:
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "X-Correlator",
                "Missing XCorrelator schema",
                "components.schemas.XCorrelator"
            ))
        else:
            pattern = x_correlator.get('pattern')
            expected_pattern = r'^[a-zA-Z0-9-_:;.\/<>{}]{0,256}$'
            if pattern != expected_pattern:
                result.issues.append(ValidationIssue(
                    Severity.CRITICAL, "X-Correlator",
                    f"Incorrect XCorrelator pattern. Expected: {expected_pattern}",
                    "components.schemas.XCorrelator.pattern"
                ))

    def _check_date_time_fields(self, spec: dict, result: ValidationResult):
        """Check date-time field descriptions"""
        result.checks_performed.append("Date-time fields validation")
        
        def check_datetime_in_schema(schema_obj: dict, path: str = ""):
            if isinstance(schema_obj, dict):
                if schema_obj.get('format') == 'date-time':
                    description = schema_obj.get('description', '')
                    if 'RFC 3339' not in description:
                        result.issues.append(ValidationIssue(
                            Severity.MEDIUM, "Date-Time Fields",
                            "Missing RFC 3339 description for date-time field",
                            path,
                            "Add RFC 3339 format description"
                        ))
                
                for key, value in schema_obj.items():
                    check_datetime_in_schema(value, f"{path}.{key}" if path else key)
            elif isinstance(schema_obj, list):
                for i, item in enumerate(schema_obj):
                    check_datetime_in_schema(item, f"{path}[{i}]")
        
        components = spec.get('components', {})
        schemas = components.get('schemas', {})
        
        for schema_name, schema_obj in schemas.items():
            check_datetime_in_schema(schema_obj, f"components.schemas.{schema_name}")

    def _check_reserved_words(self, spec: dict, result: ValidationResult):
        """Check for reserved words usage"""
        result.checks_performed.append("Reserved words validation")
        
        def check_name(name: str, location: str):
            if name.lower() in self.reserved_words:
                result.issues.append(ValidationIssue(
                    Severity.MEDIUM, "Reserved Words",
                    f"Reserved word '{name}' used",
                    location,
                    f"Rename '{name}' to avoid conflicts"
                ))
        
        # Check paths
        paths = spec.get('paths', {})
        for path in paths.keys():
            path_parts = path.strip('/').split('/')
            for part in path_parts:
                if not part.startswith('{'):  # Skip path parameters
                    check_name(part, f"paths.{path}")
        
        # Check operation IDs
        for path, path_obj in paths.items():
            for method, operation in path_obj.items():
                if isinstance(operation, dict):
                    operation_id = operation.get('operationId')
                    if operation_id:
                        check_name(operation_id, f"paths.{path}.{method}.operationId")
        
        # Check component names
        components = spec.get('components', {})
        for component_type in ['schemas', 'responses', 'parameters', 'requestBodies']:
            component_group = components.get(component_type, {})
            for name in component_group.keys():
                check_name(name, f"components.{component_type}.{name}")

    def _check_device_schema(self, spec: dict, result: ValidationResult):
        """Check Device schema if present"""
        result.checks_performed.append("Device schema validation")
        
        components = spec.get('components', {})
        schemas = components.get('schemas', {})
        device_schema = schemas.get('Device')
        
        if device_schema:
            properties = device_schema.get('properties', {})
            
            # Check for required device identifier properties
            expected_props = ['phoneNumber', 'networkAccessIdentifier']
            missing_props = []
            for prop in expected_props:
                if prop not in properties:
                    missing_props.append(prop)
            
            if missing_props:
                result.issues.append(ValidationIssue(
                    Severity.LOW, "Device Schema",
                    f"Device schema missing properties: {', '.join(missing_props)}",
                    "components.schemas.Device.properties",
                    "Consider adding missing device identifier properties"
                ))
            
            # Check minProperties
            min_props = device_schema.get('minProperties')
            if min_props != 1:
                result.issues.append(ValidationIssue(
                    Severity.MEDIUM, "Device Schema",
                    "Device schema should have minProperties: 1",
                    "components.schemas.Device.minProperties"
                ))

    def _check_file_naming(self, file_path: str, spec: dict, result: ValidationResult):
        """Check file naming conventions"""
        result.checks_performed.append("File naming validation")
        
        filename = Path(file_path).stem
        
        # Check kebab-case
        if not re.match(r'^[a-z0-9-]+$', filename):
            result.issues.append(ValidationIssue(
                Severity.MEDIUM, "File Naming",
                f"Filename should use kebab-case: {filename}",
                file_path,
                "Use lowercase letters, numbers, and hyphens only"
            ))

    def _check_work_in_progress_version(self, spec: dict, result: ValidationResult):
        """Check for work-in-progress versions that shouldn't be released"""
        result.checks_performed.append("Work-in-progress version validation")
        
        version = spec.get('info', {}).get('version', '')
        
        if version == 'wip':
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Version",
                "Work-in-progress version 'wip' cannot be released",
                "info.version",
                "Update to proper semantic version (e.g., 0.1.0-rc.1)"
            ))
        
        # Check server URL for vwip
        servers = spec.get('servers', [])
        if servers:
            server_url = servers[0].get('url', '')
            if 'vwip' in server_url:
                result.issues.append(ValidationIssue(
                    Severity.CRITICAL, "Server URL",
                    "Server URL contains 'vwip' - not valid for release",
                    "servers[0].url",
                    "Update to proper version format (e.g., v0.1rc1)"
                ))

    def _check_updated_generic401(self, spec: dict, result: ValidationResult):
        """Check for updated Generic401 response format (Commonalities 0.6)"""
        result.checks_performed.append("Updated Generic401 response validation")
        
        responses = spec.get('components', {}).get('responses', {})
        generic401 = responses.get('Generic401', {})
        
        if generic401:
            content = generic401.get('content', {})
            app_json = content.get('application/json', {})
            examples = app_json.get('examples', {})
            
            # Check for updated message in examples
            for example_name, example in examples.items():
                if 'UNAUTHENTICATED' in example_name:
                    example_value = example.get('value', {})
                    message = example_value.get('message', '')
                    
                    if 'A new authentication is required' not in message:
                        result.issues.append(ValidationIssue(
                            Severity.CRITICAL, "Error Responses",
                            "Generic401 response missing updated message format",
                            f"components.responses.Generic401.examples.{example_name}",
                            "Add 'A new authentication is required.' to message"
                        ))

    # ===========================================
    # Project Consistency and Test Validation (unchanged)
    # ===========================================

    def validate_project_consistency(self, api_files: List[str]) -> ConsistencyResult:
        """Check shared schema validation across multiple API files"""
        result = ConsistencyResult()
        result.checks_performed.append("Project-wide shared schema validation")
        
        if len(api_files) < 2:
            return result
            
        # Load all API specs
        specs = {}
        for api_file in api_files:
            try:
                with open(api_file, 'r', encoding='utf-8') as f:
                    specs[api_file] = yaml.safe_load(f)
            except Exception as e:
                result.issues.append(ValidationIssue(
                    Severity.CRITICAL, "File Loading",
                    f"Failed to load {api_file}: {str(e)}",
                    api_file
                ))
                continue
        
        if len(specs) < 2:
            return result
            
        # Define common schemas that should be identical
        common_schema_names = [
            'XCorrelator', 'ErrorInfo', 'Device', 'DeviceResponse', 
            'PhoneNumber', 'NetworkAccessIdentifier', 'DeviceIpv4Addr', 
            'DeviceIpv6Address', 'SingleIpv4Addr', 'Port', 'Point', 
            'Latitude', 'Longitude', 'Area', 'AreaType', 'Circle'
        ]
        
        # Check each common schema
        for schema_name in common_schema_names:
            self._validate_shared_schema(schema_name, specs, result)
        
        # Check license consistency
        self._validate_license_consistency(specs, result)
        
        # Check commonalities version consistency
        self._validate_commonalities_consistency(specs, result)
        
        return result

    def _validate_shared_schema(self, schema_name: str, specs: dict, result: ConsistencyResult):
        """Validate that a shared schema is consistent across files"""
        schemas_found = {}
        
        # Collect schema definitions from all files
        for file_path, spec in specs.items():
            schemas = spec.get('components', {}).get('schemas', {})
            if schema_name in schemas:
                schemas_found[file_path] = schemas[schema_name]
        
        if len(schemas_found) < 2:
            return  # Schema not used in multiple files
            
        # Compare all schemas for consistency
        reference_file = list(schemas_found.keys())[0]
        reference_schema = schemas_found[reference_file]
        
        for file_path, schema in schemas_found.items():
            if file_path == reference_file:
                continue
                
            if not self._schemas_equivalent(reference_schema, schema):
                result.issues.append(ValidationIssue(
                    Severity.CRITICAL, "Shared Schema Consistency",
                    f"Schema '{schema_name}' differs between files",
                    f"{Path(reference_file).name} vs {Path(file_path).name}",
                    f"Ensure '{schema_name}' schema is identical in all files"
                ))

    def _schemas_equivalent(self, schema1: dict, schema2: dict) -> bool:
        """Deep comparison of two schema objects"""
        # Remove description fields for comparison as they may vary
        def normalize_schema(schema):
            if isinstance(schema, dict):
                normalized = {}
                for key, value in schema.items():
                    if key != 'description':  # Allow description differences
                        normalized[key] = normalize_schema(value)
                return normalized
            elif isinstance(schema, list):
                return [normalize_schema(item) for item in schema]
            return schema
        
        return normalize_schema(schema1) == normalize_schema(schema2)

    def _validate_license_consistency(self, specs: dict, result: ConsistencyResult):
        """Check that license information is consistent"""
        licenses = {}
        
        for file_path, spec in specs.items():
            license_info = spec.get('info', {}).get('license', {})
            if license_info:
                licenses[file_path] = license_info
        
        if len(licenses) < 2:
            return
            
        reference_file = list(licenses.keys())[0]
        reference_license = licenses[reference_file]
        
        for file_path, license_info in licenses.items():
            if file_path == reference_file:
                continue
                
            if license_info != reference_license:
                result.issues.append(ValidationIssue(
                    Severity.MEDIUM, "License Consistency",
                    "License information differs between files",
                    f"{Path(reference_file).name} vs {Path(file_path).name}",
                    "Ensure all files have identical license information"
                ))

    def _validate_commonalities_consistency(self, specs: dict, result: ConsistencyResult):
        """Check that commonalities version is consistent"""
        versions = {}
        
        for file_path, spec in specs.items():
            version = spec.get('info', {}).get('x-camara-commonalities')
            if version:
                versions[file_path] = str(version)
        
        if len(versions) < 2:
            return
            
        reference_file = list(versions.keys())[0]
        reference_version = versions[reference_file]
        
        for file_path, version in versions.items():
            if file_path == reference_file:
                continue
                
            if version != reference_version:
                result.issues.append(ValidationIssue(
                    Severity.MEDIUM, "Commonalities Consistency",
                    f"Commonalities version differs: {reference_version} vs {version}",
                    f"{Path(reference_file).name} vs {Path(file_path).name}",
                    "Ensure all files use the same commonalities version"
                ))

    def validate_test_alignment(self, api_file: str, test_dir: str) -> TestAlignmentResult:
        """Validate test definitions alignment with API specs"""
        result = TestAlignmentResult(api_file=api_file)
        result.checks_performed.append("Test alignment validation")
        
        # Load API spec
        try:
            with open(api_file, 'r', encoding='utf-8') as f:
                api_spec = yaml.safe_load(f)
        except Exception as e:
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "API Loading",
                f"Failed to load API file: {str(e)}",
                api_file
            ))
            return result
        
        # Extract API info
        api_info = api_spec.get('info', {})
        api_version = api_info.get('version', '')
        api_title = api_info.get('title', '')
        
        # Extract api-name from filename
        api_name = Path(api_file).stem
        
        # Find test files
        test_files = self._find_test_files(test_dir, api_name)
        result.test_files = test_files
        
        if not test_files:
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Test Files",
                f"No test files found for API '{api_name}'",
                test_dir,
                f"Create either '{api_name}.feature' or '{api_name}-<operationId>.feature' files"
            ))
            return result
        
        # Extract operation IDs from API
        api_operations = self._extract_operation_ids(api_spec)
        
        # Validate each test file
        for test_file in test_files:
            self._validate_test_file(test_file, api_name, api_version, api_title, 
                                   api_operations, result)
        
        return result

    def _find_test_files(self, test_dir: str, api_name: str) -> List[str]:
        """Find test files for the given API"""
        test_files = []
        test_path = Path(test_dir)
        
        if not test_path.exists():
            return test_files
        
        # Look for api-name.feature
        main_test = test_path / f"{api_name}.feature"
        if main_test.exists():
            test_files.append(str(main_test))
        
        # Look for api-name-*.feature files
        for test_file in test_path.glob(f"{api_name}-*.feature"):
            test_files.append(str(test_file))
        
        return test_files

    def _extract_operation_ids(self, api_spec: dict) -> List[str]:
        """Extract all operation IDs from API spec"""
        operation_ids = []
        
        paths = api_spec.get('paths', {})
        for path, path_obj in paths.items():
            for method, operation in path_obj.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    operation_id = operation.get('operationId')
                    if operation_id:
                        operation_ids.append(operation_id)
        
        return operation_ids

def _validate_test_file(self, test_file: str, api_name: str, api_version: str, 
                       api_title: str, api_operations: List[str], result: TestAlignmentResult):
    """Validate individual test file"""
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        result.issues.append(ValidationIssue(
            Severity.CRITICAL, "Test File Loading",
            f"Failed to load test file: {str(e)}",
            test_file
        ))
        return
    
    lines = content.split('\n')
    
    # Check for version in Feature line (can be line 1 or 2)
    feature_line = None
    feature_line_number = None
    
    # Check first two lines for Feature line
    for i, line in enumerate(lines[:2]):
        stripped_line = line.strip()
        if stripped_line.startswith('Feature:'):
            feature_line = stripped_line
            feature_line_number = i + 1
            break
    
    if feature_line:
        if not self._validate_test_version_line(feature_line, api_version, api_title):
            result.issues.append(ValidationIssue(
                Severity.MEDIUM, "Test Version",
                f"Feature line doesn't mention API version {api_version}",
                f"{test_file}:line {feature_line_number}",
                f"Include version {api_version} in Feature line: {feature_line}"
            ))
    else:
        result.issues.append(ValidationIssue(
            Severity.MEDIUM, "Test Structure",
            "No Feature line found in first two lines",
            f"{test_file}:lines 1-2",
            "Add Feature line with API name and version"
        ))
    
    # Check operation IDs referenced in test
    test_operations = self._extract_test_operations(content)
    
    # Validate that test operations exist in API
    for test_op in test_operations:
        if test_op not in api_operations:
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Test Operation IDs",
                f"Test references unknown operation '{test_op}'",
                test_file,
                f"Use valid operation ID from: {', '.join(api_operations)}"
            ))
    
    # For operation-specific test files, validate naming
    test_filename = Path(test_file).stem
    if test_filename.startswith(f"{api_name}-"):
        expected_operation = test_filename.replace(f"{api_name}-", "")
        if expected_operation not in api_operations:
            result.issues.append(ValidationIssue(
                Severity.MEDIUM, "Test File Naming",
                f"Test file suggests operation '{expected_operation}' but it doesn't exist in API",
                test_file,
                f"Use valid operation from: {', '.join(api_operations)}"
            ))

def _validate_test_version_line(self, feature_line: str, api_version: str, api_title: str) -> bool:
    """Check if Feature line contains the API version"""
    # Look for version pattern in Feature line
    version_pattern = r'v?\d+\.\d+\.\d+(?:-rc\.\d+|-alpha\.\d+)?'
    found_versions = re.findall(version_pattern, feature_line)
    
    # Check for both exact version and version with 'v' prefix
    return api_version in found_versions or f'v{api_version}' in found_versions

    def _extract_test_operations(self, content: str) -> List[str]:
        """Extract operation IDs referenced in test content"""
        # Look for patterns like 'request "operationId"'
        operation_pattern = r'request\s+"([^"]+)"'
        operations = re.findall(operation_pattern, content)
        
        return list(set(operations))  # Remove duplicates


def find_api_files(directory: str) -> List[str]:
    """Find all YAML files in the API definitions directory"""
    api_dir = Path(directory) / "code" / "API_definitions"
    
    if not api_dir.exists():
        return []
    
    yaml_files = []
    for pattern in ['*.yaml', '*.yml']:
        yaml_files.extend(api_dir.glob(pattern))
    
    return [str(f) for f in yaml_files]

def generate_report(results: List[ValidationResult], output_dir: str, repo_name: str = "", pr_number: str = "", 
                   consistency_result: Optional[ConsistencyResult] = None, 
                   test_results: List[TestAlignmentResult] = None):
    """Generate comprehensive report and summary with enhanced API type detection"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate unique filename with repository name, PR number, and timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if repo_name and pr_number:
        report_filename = f"camara-api-review_{repo_name}_pr{pr_number}_{timestamp}.md"
    elif repo_name:
        report_filename = f"camara-api-review_{repo_name}_{timestamp}.md"
    else:
        report_filename = f"camara-api-review_{timestamp}.md"
    
    report_path = f"{output_dir}/{report_filename}"
    
    # Calculate summary statistics
    total_critical = sum(r.critical_count for r in results)
    total_medium = sum(r.medium_count for r in results)
    total_low = sum(r.low_count for r in results)
    
    # Add consistency and test results to totals
    if consistency_result:
        total_critical += len([i for i in consistency_result.issues if i.severity == Severity.CRITICAL])
        total_medium += len([i for i in consistency_result.issues if i.severity == Severity.MEDIUM])
        total_low += len([i for i in consistency_result.issues if i.severity == Severity.LOW])
    
    if test_results:
        for test_result in test_results:
            total_critical += len([i for i in test_result.issues if i.severity == Severity.CRITICAL])
            total_medium += len([i for i in test_result.issues if i.severity == Severity.MEDIUM])
            total_low += len([i for i in test_result.issues if i.severity == Severity.LOW])
    
    # API Type breakdown
    type_counts = {}
    for result in results:
        api_type = result.api_type.value
        type_counts[api_type] = type_counts.get(api_type, 0) + 1
    
    # Collect unique checks performed across all APIs (for later sections)
    all_checks_performed = set()
    all_manual_checks = set()
    
    for result in results:
        all_checks_performed.update(result.checks_performed)
        all_manual_checks.update(result.manual_checks_needed)
    
    if consistency_result:
        all_checks_performed.update(consistency_result.checks_performed)
    
    if test_results:
        for test_result in test_results:
            all_checks_performed.update(test_result.checks_performed)
    
    # Generate detailed report
    with open(report_path, "w") as f:
        f.write("# CAMARA API Review - Enhanced Report with Subscription Type Detection (Commonalities 0.6)\n\n")
        
        # Add header information
        if repo_name:
            f.write(f"**Repository**: {repo_name}\n")
        if pr_number:
            f.write(f"**Pull Request**: #{pr_number}\n")
        f.write(f"**Generated**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"**Report File**: {report_filename}\n")
        f.write(f"**Validator**: Enhanced CAMARA API Review Validator with Subscription Type Detection v0.6\n\n")
        
        # 1. SUMMARY
        f.write("## Summary\n\n")
        f.write(f"- **APIs Reviewed**: {len(results)}\n")
        f.write(f"- **Critical Issues**: {total_critical}\n")
        f.write(f"- **Medium Issues**: {total_medium}\n")
        f.write(f"- **Low Priority Issues**: {total_low}\n\n")
        
        # API Type breakdown
        f.write("## API Types Detected\n\n")
        for api_type, count in type_counts.items():
            f.write(f"- **{api_type}**: {count} API(s)\n")
        f.write("\n")
        
        # 2. INDIVIDUAL API RESULTS
        f.write("## Individual API Results\n\n")
        
        for result in results:
            f.write(f"### {result.api_name} (v{result.version})\n\n")
            f.write(f"**File**: `{result.file_path}`\n")
            f.write(f"**API Type**: {result.api_type.value}\n\n")
            
            # Add type-specific indicators
            if result.api_type == APIType.EXPLICIT_SUBSCRIPTION:
                f.write("🔔 **Explicit Subscription API** - Full subscription management validation applied\n\n")
            elif result.api_type == APIType.IMPLICIT_SUBSCRIPTION:
                f.write("📧 **Implicit Subscription API** - Notification-focused validation applied\n\n")
            else:
                f.write("📄 **Regular API** - Standard validation applied\n\n")
            
            if result.issues:
                # Group issues by severity
                critical_issues = [i for i in result.issues if i.severity == Severity.CRITICAL]
                medium_issues = [i for i in result.issues if i.severity == Severity.MEDIUM]
                low_issues = [i for i in result.issues if i.severity == Severity.LOW]
                
                for severity, issues in [
                    ("🔴 Critical Issues", critical_issues),
                    ("🟡 Medium Priority Issues", medium_issues),
                    ("🔵 Low Priority Issues", low_issues)
                ]:
                    if issues:
                        f.write(f"#### {severity}\n\n")
                        for issue in issues:
                            f.write(f"**{issue.category}**: {issue.description}\n")
                            if issue.location:
                                f.write(f"- **Location**: `{issue.location}`\n")
                            if issue.fix_suggestion:
                                f.write(f"- **Fix**: {issue.fix_suggestion}\n")
                            f.write("\n")
            else:
                f.write("✅ **No issues found**\n\n")
            
            f.write("---\n\n")
        
        # 3. TEST ALIGNMENT RESULTS
        if test_results:
            f.write("## Test Alignment Results\n\n")
            
            for test_result in test_results:
                api_name = Path(test_result.api_file).stem
                f.write(f"### {api_name} Test Alignment\n\n")
                
                if test_result.test_files:
                    f.write(f"**Test Files Found**: {len(test_result.test_files)}\n")
                    for test_file in test_result.test_files:
                        f.write(f"- `{Path(test_file).name}`\n")
                    f.write("\n")
                
                if test_result.issues:
                    critical_test = [i for i in test_result.issues if i.severity == Severity.CRITICAL]
                    medium_test = [i for i in test_result.issues if i.severity == Severity.MEDIUM]
                    low_test = [i for i in test_result.issues if i.severity == Severity.LOW]
                    
                    for severity, issues in [
                        ("🔴 Critical Test Issues", critical_test),
                        ("🟡 Medium Test Issues", medium_test),
                        ("🔵 Low Test Issues", low_test)
                    ]:
                        if issues:
                            f.write(f"#### {severity}\n\n")
                            for issue in issues:
                                f.write(f"**{issue.category}**: {issue.description}\n")
                                if issue.location:
                                    f.write(f"- **Location**: `{issue.location}`\n")
                                if issue.fix_suggestion:
                                    f.write(f"- **Fix**: {issue.fix_suggestion}\n")
                                f.write("\n")
                else:
                    f.write("✅ **No test alignment issues found**\n\n")
            
            f.write("---\n\n")
        
        # 4. PROJECT-WIDE CONSISTENCY ISSUES
        if consistency_result and consistency_result.issues:
            f.write("## Project-Wide Consistency Issues\n\n")
            
            critical_consistency = [i for i in consistency_result.issues if i.severity == Severity.CRITICAL]
            medium_consistency = [i for i in consistency_result.issues if i.severity == Severity.MEDIUM]
            low_consistency = [i for i in consistency_result.issues if i.severity == Severity.LOW]
            
            for severity, issues in [
                ("🔴 Critical Cross-File Issues", critical_consistency),
                ("🟡 Medium Cross-File Issues", medium_consistency),
                ("🔵 Low Cross-File Issues", low_consistency)
            ]:
                if issues:
                    f.write(f"### {severity}\n\n")
                    for issue in issues:
                        f.write(f"**{issue.category}**: {issue.description}\n")
                        if issue.location:
                            f.write(f"- **Location**: `{issue.location}`\n")
                        if issue.fix_suggestion:
                            f.write(f"- **Fix**: {issue.fix_suggestion}\n")
                        f.write("\n")
            f.write("---\n\n")
        
        # 5. AUTOMATED CHECKS PERFORMED
        if all_checks_performed:
            f.write("## Automated Checks Performed\n\n")
            for check in sorted(all_checks_performed):
                f.write(f"- {check}\n")
            f.write("\n")
        
        # 6. MANUAL REVIEW REQUIRED
        if all_manual_checks:
            f.write("## Manual Review Required\n\n")
            for check in sorted(all_manual_checks):
                f.write(f"- {check}\n")
            f.write("\n")
    
    # Generate summary for GitHub comment with 25-item limit
    with open(f"{output_dir}/summary.md", "w") as f:
        if not results:
            f.write("❌ **No API definition files found**\n\n")
            f.write("Please ensure YAML files are located in `/code/API_definitions/`\n")
            return report_filename
        
        # Overall status
        if total_critical == 0:
            if total_medium == 0:
                status = "✅ **Ready for Release**"
            else:
                status = "⚠️ **Conditional Approval**"
        else:
            status = "❌ **Critical Issues Found**"
        
        f.write(f"### {status}\n\n")
        
        # APIs found with types
        f.write("**APIs Reviewed**:\n")
        for result in results:
            type_indicator = {
                APIType.EXPLICIT_SUBSCRIPTION: "🔔",
                APIType.IMPLICIT_SUBSCRIPTION: "📧", 
                APIType.REGULAR: "📄"
            }.get(result.api_type, "📄")
            
            f.write(f"- {type_indicator} `{result.api_name}` v{result.version} ({result.api_type.value})\n")
        f.write("\n")
        
        # Issue summary
        f.write("**Issues Summary**:\n")
        f.write(f"- 🔴 Critical: {total_critical}\n")
        f.write(f"- 🟡 Medium: {total_medium}\n")
        f.write(f"- 🔵 Low: {total_low}\n\n")
        
        # Enhanced issues detail with 25-item limit, prioritizing critical then medium
        if total_critical > 0 or total_medium > 0:
            f.write("**Issues Requiring Attention**:\n")
            
            # Collect all issues from all sources
            all_critical_issues = []
            all_medium_issues = []
            
            # From individual API results
            for result in results:
                critical_issues = [i for i in result.issues if i.severity == Severity.CRITICAL]
                medium_issues = [i for i in result.issues if i.severity == Severity.MEDIUM]
                
                for issue in critical_issues:
                    all_critical_issues.append((result.api_name, issue))
                for issue in medium_issues:
                    all_medium_issues.append((result.api_name, issue))
            
            # From consistency results
            if consistency_result:
                critical_issues = [i for i in consistency_result.issues if i.severity == Severity.CRITICAL]
                medium_issues = [i for i in consistency_result.issues if i.severity == Severity.MEDIUM]
                
                for issue in critical_issues:
                    all_critical_issues.append(("Project-wide", issue))
                for issue in medium_issues:
                    all_medium_issues.append(("Project-wide", issue))
            
            # From test results
            if test_results:
                for test_result in test_results:
                    critical_issues = [i for i in test_result.issues if i.severity == Severity.CRITICAL]
                    medium_issues = [i for i in test_result.issues if i.severity == Severity.MEDIUM]
                    
                    api_name = Path(test_result.api_file).stem
                    for issue in critical_issues:
                        all_critical_issues.append((f"{api_name} Tests", issue))
                    for issue in medium_issues:
                        all_medium_issues.append((f"{api_name} Tests", issue))
            
            # Show critical issues first (up to 20 to leave room for medium)
            critical_to_show = min(len(all_critical_issues), 20)
            
            if critical_to_show > 0:
                f.write(f"\n**🔴 Critical Issues ({critical_to_show}):**\n")
                for source_name, issue in all_critical_issues[:critical_to_show]:
                    f.write(f"- *{source_name}*: **{issue.category}** - {issue.description}\n")
            
            # Show medium issues if there's room
            remaining_slots = 25 - critical_to_show
            medium_to_show = min(len(all_medium_issues), remaining_slots)
            
            if medium_to_show > 0:
                f.write(f"\n**🟡 Medium Priority Issues ({medium_to_show}):**\n")
                for source_name, issue in all_medium_issues[:medium_to_show]:
                    f.write(f"- *{source_name}*: **{issue.category}** - {issue.description}\n")
            
            # Note if there are more issues not shown
            total_not_shown = (total_critical + total_medium) - 25
            if total_not_shown > 0:
                f.write(f"\n*Note: {total_not_shown} additional issues not shown above. See detailed report for complete analysis.*\n")
            
            f.write("\n")
        
        # Recommendation
        if total_critical == 0 and total_medium == 0:
            f.write("**Recommendation**: ✅ Approved for release\n")
        elif total_critical == 0:
            f.write("**Recommendation**: ⚠️ Approved with medium-priority improvements recommended\n")
        else:
            f.write(f"**Recommendation**: ❌ Address {total_critical} critical issue(s) before release\n")
        
        f.write(f"\n📄 **Detailed Report**: {report_filename}\n")
        f.write("\n📄 **Download**: Available as workflow artifact for complete analysis\n")
        f.write("\n🔍 **Enhanced Validation**: This review includes subscription type detection, scope naming, filename consistency, project consistency, and test alignment validation\n")
    
    # Return the report filename for use by the workflow
    return report_filename

def main():
    """Main function - enhanced with subscription type detection"""
    if len(sys.argv) < 4:
        print("Usage: python enhanced_api_review_validator_v0_6.py <repo_directory> <commonalities_version> <output_directory> [repo_name] [pr_number] [additional_args...]")
        print("")
        print("This script analyzes API definitions with enhanced subscription type detection.")
        print("Enhanced version includes:")
        print("- Differentiated validation for explicit vs implicit subscription APIs")
        print("- Proper classification of subscription API types")
        print("- Targeted validation checks based on API type")
        print("- All previous validation features maintained")
        print("")
        print("Parameters:")
        print("  repo_directory: Path to the repository to analyze")
        print("  commonalities_version: CAMARA Commonalities version (e.g., 0.6)")
        print("  output_directory: Where to write the reports")
        print("  repo_name: (optional) Repository name for unique filename")
        print("  pr_number: (optional) PR number for unique filename")
        print("  additional_args: (optional) Additional arguments - ignored")
        sys.exit(0)
    
    repo_dir = sys.argv[1]
    commonalities_version = sys.argv[2]
    output_dir = sys.argv[3]
    repo_name = sys.argv[4] if len(sys.argv) > 4 else ""
    pr_number = sys.argv[5] if len(sys.argv) > 5 else ""
    
    # Log any additional arguments (but ignore them)
    if len(sys.argv) > 6:
        additional_args = sys.argv[6:]
        print(f"📋 Additional arguments (ignored): {additional_args}")
    
    print(f"🚀 Starting Enhanced CAMARA API validation with Subscription Type Detection (Commonalities {commonalities_version})")
    print(f"📁 Repository directory: {repo_dir}")
    print(f"📊 Output directory: {output_dir}")
    if repo_name:
        print(f"📦 Repository: {repo_name}")
    if pr_number:
        print(f"🔗 PR Number: {pr_number}")
    
    # Find API files
    api_files = find_api_files(repo_dir)
    
    if not api_files:
        print("❌ No API definition files found")
        print("Checked location: {}/code/API_definitions/".format(repo_dir))
        print("📄 Creating empty results report...")
        # Create empty results for summary
        try:
            report_filename = generate_report([], output_dir, repo_name, pr_number)
            print(f"📄 Empty report generated: {report_filename}")
        except Exception as e:
            print(f"❌ Error generating empty report: {str(e)}")
        sys.exit(0)
    
    print(f"🔍 Found {len(api_files)} API definition file(s)")
    for file in api_files:
        print(f"  - {file}")
    
    # Validate each file
    validator = CAMARAAPIValidator(commonalities_version)
    results = []
    
    for api_file in api_files:
        print(f"\n📋 Validating {api_file}...")
        try:
            result = validator.validate_api_file(api_file)
            results.append(result)
            
            print(f"  📄 API Type: {result.api_type.value}")
            print(f"  🔴 Critical: {result.critical_count}")
            print(f"  🟡 Medium: {result.medium_count}")
            print(f"  🔵 Low: {result.low_count}")
                
        except Exception as e:
            print(f"  ❌ Error validating {api_file}: {str(e)}")
            # Create error result
            error_result = ValidationResult(file_path=api_file)
            error_result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Validation Error", f"Failed to validate file: {str(e)}"
            ))
            results.append(error_result)
    
    # Enhanced: Project-wide consistency validation
    consistency_result = None
    if len(api_files) > 1:
        print(f"\n🔗 Performing project consistency validation...")
        try:
            consistency_result = validator.validate_project_consistency(api_files)
            consistency_critical = len([i for i in consistency_result.issues if i.severity == Severity.CRITICAL])
            consistency_medium = len([i for i in consistency_result.issues if i.severity == Severity.MEDIUM])
            consistency_low = len([i for i in consistency_result.issues if i.severity == Severity.LOW])
            
            print(f"  🔴 Critical: {consistency_critical}")
            print(f"  🟡 Medium: {consistency_medium}")
            print(f"  🔵 Low: {consistency_low}")
        except Exception as e:
            print(f"  ❌ Error in consistency validation: {str(e)}")
    
    # Enhanced: Test alignment validation
    test_results = []
    test_dir = os.path.join(repo_dir, "code", "Test_definitions")
    if os.path.exists(test_dir):
        print(f"\n🧪 Performing test alignment validation...")
        for api_file in api_files:
            try:
                test_result = validator.validate_test_alignment(api_file, test_dir)
                test_results.append(test_result)
                
                api_name = Path(api_file).stem
                test_critical = len([i for i in test_result.issues if i.severity == Severity.CRITICAL])
                test_medium = len([i for i in test_result.issues if i.severity == Severity.MEDIUM])
                test_low = len([i for i in test_result.issues if i.severity == Severity.LOW])
                
                print(f"  {api_name}: 🔴 {test_critical} 🟡 {test_medium} 🔵 {test_low} | Files: {len(test_result.test_files)}")
            except Exception as e:
                print(f"  ❌ Error validating tests for {api_file}: {str(e)}")
    else:
        print(f"\n📝 No test directory found at {test_dir}")
    
    print(f"\n📊 Enhanced validation analysis completed")
    
    # Generate reports with enhanced data
    print(f"📄 Generating enhanced reports in {output_dir}...")
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        report_filename = generate_report(results, output_dir, repo_name, pr_number, 
                                        consistency_result, test_results)
        
        # Verify summary was created
        summary_path = os.path.join(output_dir, "summary.md")
        if os.path.exists(summary_path):
            print("✅ Summary report generated successfully")
        else:
            print("❌ Summary report not created - check generate_report function")
            
        print(f"✅ Enhanced reports generated successfully")
        print(f"📄 Detailed report: {report_filename}")
        
    except Exception as e:
        print(f"❌ Error generating reports: {str(e)}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        
        # Create minimal fallback report
        try:
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, "summary.md"), "w") as f:
                f.write("❌ **API Review Failed**\n\nReport generation error occurred.\n")
            print("📄 Fallback summary report created")
        except Exception as fallback_error:
            print(f"❌ Even fallback report failed: {str(fallback_error)}")
    
    # Calculate totals including consistency and test results
    total_critical = sum(r.critical_count for r in results)
    total_medium = sum(r.medium_count for r in results)
    total_low = sum(r.low_count for r in results)
    
    if consistency_result:
        total_critical += len([i for i in consistency_result.issues if i.severity == Severity.CRITICAL])
        total_medium += len([i for i in consistency_result.issues if i.severity == Severity.MEDIUM])
        total_low += len([i for i in consistency_result.issues if i.severity == Severity.LOW])
    
    if test_results:
        for test_result in test_results:
            total_critical += len([i for i in test_result.issues if i.severity == Severity.CRITICAL])
            total_medium += len([i for i in test_result.issues if i.severity == Severity.MEDIUM])
            total_low += len([i for i in test_result.issues if i.severity == Severity.LOW])
    
    # API type summary
    type_counts = {}
    for result in results:
        api_type = result.api_type.value
        type_counts[api_type] = type_counts.get(api_type, 0) + 1
    
    print(f"\n🎯 **Enhanced Review Complete with Subscription Type Detection** (Commonalities {commonalities_version})")
    if repo_name:
        print(f"Repository: {repo_name}")
    if pr_number:
        print(f"PR: #{pr_number}")
    print(f"Individual APIs: {len(results)}")
    for api_type, count in type_counts.items():
        print(f"  - {api_type}: {count}")
    print(f"Multi-file Consistency: {'✅ Checked' if consistency_result else '⏭️ Skipped (single file)'}")
    print(f"Test Alignment: {'✅ Checked' if test_results else '⏭️ Skipped (no tests found)'}")
    print(f"Total Critical Issues: {total_critical}")
    print(f"Total Medium Issues: {total_medium}")
    print(f"Total Low Issues: {total_low}")
    
    # Always exit successfully - we are a reporter, not a judge
    print("\n📋 Enhanced analysis complete with proper subscription API type detection.")
    sys.exit(0)

if __name__ == "__main__":
    main()
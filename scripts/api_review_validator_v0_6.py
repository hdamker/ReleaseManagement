#!/usr/bin/env python3
"""
Enhanced CAMARA API Review Validator - Version 0.6
Automated validation of CAMARA API definitions with enhanced event subscription support

This script analyzes API definitions and reports findings, focusing on Commonalities 0.6
requirements including event subscriptions, CloudEvents, and updated error responses.
"""

import os
import sys
import yaml
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import datetime

class Severity(Enum):
    CRITICAL = "🔴 Critical"
    MEDIUM = "🟡 Medium"
    LOW = "🔵 Low"
    INFO = "ℹ️ Info"

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
            
            # Extract basic info
            result.api_name = api_spec.get('info', {}).get('title', 'Unknown')
            result.version = api_spec.get('info', {}).get('version', 'Unknown')
            
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
            
            # Event subscription specific checks
            if self._is_subscription_api(api_spec):
                self._check_event_subscription_compliance(api_spec, result)
                self._check_cloudevents_compliance(api_spec, result)
                self._check_event_type_naming(api_spec, result)
                self._check_subscription_lifecycle_events(api_spec, result)
                self._check_sink_validation(api_spec, result)
                self._check_subscription_error_codes(api_spec, result)
            
            # Add manual checks needed
            result.manual_checks_needed = [
                "Business logic appropriateness review",
                "Documentation quality assessment",
                "API design patterns validation",
                "Use case coverage evaluation",
                "Security considerations beyond structure",
                "Cross-file reference validation (if multi-API)",
                "Performance and scalability considerations",
                "Event notification flow testing (for subscription APIs)"
            ]
            
        except yaml.YAMLError as e:
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "YAML Syntax", f"YAML parsing error: {str(e)}"
            ))
        except Exception as e:
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Validation Error", f"Unexpected error: {str(e)}"
            ))
        
        return result

    def _is_subscription_api(self, spec: dict) -> bool:
        """Check if this is an event subscription API"""
        title = spec.get('info', {}).get('title', '').lower()
        paths = spec.get('paths', {})
        
        # Check if API name contains 'subscription'
        if 'subscription' in title:
            return True
            
        # Check if has /subscriptions path
        if '/subscriptions' in paths:
            return True
            
        # Check for CloudEvent schemas
        schemas = spec.get('components', {}).get('schemas', {})
        if 'CloudEvent' in schemas:
            return True
            
        return False

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

    def _check_event_subscription_compliance(self, spec: dict, result: ValidationResult):
        """Check general event subscription compliance"""
        result.checks_performed.append("Event subscription compliance validation")
        
        # Check for subscription endpoint naming
        paths = spec.get('paths', {})
        has_subscriptions_path = False
        
        for path in paths.keys():
            if path.endswith('/subscriptions') or '/subscriptions/' in path:
                has_subscriptions_path = True
                break
        
        if not has_subscriptions_path:
            result.issues.append(ValidationIssue(
                Severity.MEDIUM, "Event Subscriptions",
                "Subscription API should have /subscriptions endpoint",
                "paths"
            ))

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

    # Existing methods from the original validator...
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
                result.issues.append(ValidationIssue(
                    Severity.MEDIUM, "ExternalDocs",
                    "Should use standard description: 'Product documentation at CAMARA'",
                    "externalDocs.description"
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
        
        # Check consistency with server URL (if possible)
        servers = spec.get('servers', [])
        if servers:
            server_url = servers[0].get('url', '')
            # Extract API name from URL pattern
            url_match = re.search(r'/([a-z0-9-]+)/v\d+', server_url)
            if url_match:
                url_api_name = url_match.group(1)
                if filename != url_api_name and not filename.startswith(url_api_name):
                    result.issues.append(ValidationIssue(
                        Severity.MEDIUM, "File Naming",
                        f"Filename '{filename}' inconsistent with server URL API name '{url_api_name}'",
                        file_path
                    ))


def find_api_files(directory: str) -> List[str]:
    """Find all YAML files in the API definitions directory"""
    api_dir = Path(directory) / "code" / "API_definitions"
    
    if not api_dir.exists():
        return []
    
    yaml_files = []
    for pattern in ['*.yaml', '*.yml']:
        yaml_files.extend(api_dir.glob(pattern))
    
    return [str(f) for f in yaml_files]

def generate_report(results: List[ValidationResult], output_dir: str):
    """Generate comprehensive report and summary"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate detailed report
    with open(f"{output_dir}/detailed-report.md", "w") as f:
        f.write("# CAMARA API Review - Detailed Report (Enhanced for Commonalities 0.6)\n\n")
        f.write(f"**Generated**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        
        # Summary statistics
        total_critical = sum(r.critical_count for r in results)
        total_medium = sum(r.medium_count for r in results)
        total_low = sum(r.low_count for r in results)
        
        f.write("## Summary\n\n")
        f.write(f"- **APIs Reviewed**: {len(results)}\n")
        f.write(f"- **Critical Issues**: {total_critical}\n")
        f.write(f"- **Medium Issues**: {total_medium}\n")
        f.write(f"- **Low Priority Issues**: {total_low}\n\n")
        
        # Detailed results for each API
        for result in results:
            f.write(f"## {result.api_name} (v{result.version})\n\n")
            f.write(f"**File**: `{result.file_path}`\n\n")
            
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
                        f.write(f"### {severity}\n\n")
                        for issue in issues:
                            f.write(f"**{issue.category}**: {issue.description}\n")
                            if issue.location:
                                f.write(f"- **Location**: `{issue.location}`\n")
                            if issue.fix_suggestion:
                                f.write(f"- **Fix**: {issue.fix_suggestion}\n")
                            f.write("\n")
            else:
                f.write("✅ **No issues found**\n\n")
            
            # Checks performed
            f.write("### Automated Checks Performed\n\n")
            for check in result.checks_performed:
                f.write(f"- {check}\n")
            
            # Manual checks needed
            f.write("\n### Manual Review Required\n\n")
            for check in result.manual_checks_needed:
                f.write(f"- {check}\n")
            
            f.write("\n---\n\n")
    
    # Generate summary for GitHub comment
    with open(f"{output_dir}/summary.md", "w") as f:
        if not results:
            f.write("❌ **No API definition files found**\n\n")
            f.write("Please ensure YAML files are located in `/code/API_definitions/`\n")
            return
        
        total_critical = sum(r.critical_count for r in results)
        total_medium = sum(r.medium_count for r in results)
        
        # Overall status
        if total_critical == 0:
            if total_medium == 0:
                status = "✅ **Ready for Release**"
            else:
                status = "⚠️ **Conditional Approval**"
        else:
            status = "❌ **Critical Issues Found**"
        
        f.write(f"### {status}\n\n")
        
        # APIs found
        f.write("**APIs Reviewed**:\n")
        for result in results:
            f.write(f"- `{result.api_name}` v{result.version}\n")
        f.write("\n")
        
        # Issue summary
        f.write("**Issues Summary**:\n")
        f.write(f"- 🔴 Critical: {total_critical}\n")
        f.write(f"- 🟡 Medium: {total_medium}\n")
        f.write(f"- 🔵 Low: {sum(r.low_count for r in results)}\n\n")
        
        # Enhanced issues detail with smart medium issue inclusion
        if total_critical > 0 or (total_critical + total_medium < 10 and total_medium > 0):
            # Determine what to show based on count
            if total_critical + total_medium < 10:
                # Show both critical and medium when total is manageable
                f.write("**Issues Requiring Attention**:\n")
                
                # Show critical issues first
                for result in results:
                    critical_issues = [i for i in result.issues if i.severity == Severity.CRITICAL]
                    medium_issues = [i for i in result.issues if i.severity == Severity.MEDIUM]
                    
                    if critical_issues or medium_issues:
                        f.write(f"\n*{result.api_name}*:\n")
                        
                        # Show all critical issues
                        for issue in critical_issues:
                            f.write(f"- 🔴 **{issue.category}**: {issue.description}\n")
                        
                        # Show medium issues if space allows
                        remaining_slots = 10 - total_critical
                        medium_to_show = min(len(medium_issues), remaining_slots)
                        
                        for issue in medium_issues[:medium_to_show]:
                            f.write(f"- 🟡 **{issue.category}**: {issue.description}\n")
                        
                        if len(medium_issues) > medium_to_show:
                            f.write(f"- 🟡 ... and {len(medium_issues) - medium_to_show} more medium priority issues\n")
            else:
                # Only show critical issues when there are too many total issues
                f.write("**Critical Issues Requiring Immediate Attention**:\n")
                for result in results:
                    critical_issues = [i for i in result.issues if i.severity == Severity.CRITICAL]
                    if critical_issues:
                        f.write(f"\n*{result.api_name}*:\n")
                        for issue in critical_issues[:3]:  # Limit to first 3
                            f.write(f"- {issue.category}: {issue.description}\n")
                        if len(critical_issues) > 3:
                            f.write(f"- ... and {len(critical_issues) - 3} more\n")
                
                # Add note about medium issues
                if total_medium > 0:
                    f.write(f"\n*Note: {total_medium} medium priority issues also found. See detailed report for complete list.*\n")
            
            f.write("\n")
        
        # Recommendation
        if total_critical == 0 and total_medium == 0:
            f.write("**Recommendation**: ✅ Approved for release\n")
        elif total_critical == 0:
            f.write("**Recommendation**: ⚠️ Approved with medium-priority improvements recommended\n")
        else:
            f.write(f"**Recommendation**: ❌ Address {total_critical} critical issue(s) before release\n")
        
        f.write("\n📄 **Detailed Report**: Download the `api-review-detailed-report` artifact from the workflow run for complete analysis\n")
        f.write("\n🔍 **Enhanced Validation**: This review includes Commonalities 0.6 compliance and event subscription validation\n")

def main():
    """Main function - always exits with success after reporting findings"""
    if len(sys.argv) != 4:
        print("Usage: python api_review_validator_v0_6.py <repo_directory> <commonalities_version> <output_directory>")
        print("")
        print("This script analyzes API definitions and reports findings.")
        print("Enhanced version includes event subscription and CloudEvents validation.")
        sys.exit(0)  # Exit successfully even for usage errors
    
    repo_dir = sys.argv[1]
    commonalities_version = sys.argv[2]
    output_dir = sys.argv[3]
    
    # Find API files
    api_files = find_api_files(repo_dir)
    
    if not api_files:
        print("❌ No API definition files found")
        print("Checked location: {}/code/API_definitions/".format(repo_dir))
        # Create empty results for summary
        generate_report([], output_dir)
        sys.exit(0)  # Exit successfully even when no files found
    
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
            
            print(f"  🔴 Critical: {result.critical_count}")
            print(f"  🟡 Medium: {result.medium_count}")
            print(f"  🔵 Low: {result.low_count}")
            
            # Check if this is a subscription API
            with open(api_file, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)
            if validator._is_subscription_api(spec):
                print(f"  📡 Event Subscription API detected - enhanced validation applied")
                
        except Exception as e:
            print(f"  ❌ Error validating {api_file}: {str(e)}")
            # Create error result
            error_result = ValidationResult(file_path=api_file)
            error_result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Validation Error", f"Failed to validate file: {str(e)}"
            ))
            results.append(error_result)
    
    # Generate reports
    print(f"\n📄 Generating reports in {output_dir}...")
    try:
        generate_report(results, output_dir)
        print("✅ Reports generated successfully")
    except Exception as e:
        print(f"❌ Error generating reports: {str(e)}")
        # Still exit successfully - we've done our job of analyzing
    
    total_critical = sum(r.critical_count for r in results)
    total_medium = sum(r.medium_count for r in results)
    
    print(f"\n🎯 **Enhanced Review Complete** (Commonalities {commonalities_version})")
    print(f"Critical Issues: {total_critical}")
    print(f"Medium Issues: {total_medium}")
    print(f"Low Issues: {sum(r.low_count for r in results)}")
    
    # Always exit successfully - we are a reporter, not a judge
    print("\n📋 Analysis complete. Decision on release readiness is left to the workflow.")
    sys.exit(0)

if __name__ == "__main__":
    main()
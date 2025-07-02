#!/usr/bin/env python3
"""
CAMARA API Review Validator - Complete Version with All Enhancements
Automated validation of CAMARA API definitions based on the comprehensive checklist

This script analyzes API definitions and reports findings, but does not judge
whether findings constitute a "failure" - that decision is left to the workflow.

Enhanced features:
- Consolidated checks in summary (not repeated per API)
- Unique filename generation with repo name, PR number, timestamp
- Extended summary to 25 items with critical and medium priority
- Improved issue organization and presentation
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
            
            # Add manual checks needed
            result.manual_checks_needed = [
                "Business logic appropriateness review",
                "Documentation quality assessment",
                "API design patterns validation",
                "Use case coverage evaluation",
                "Security considerations beyond structure",
                "Cross-file reference validation (if multi-API)",
                "Performance and scalability considerations"
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
        
        # Version check
        version = info.get('version', '')
        if not re.match(r'^\d+\.\d+\.\d+(-rc\.\d+|-alpha\.\d+)?$', version):
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
        
        # Check URL format for RC versions
        if '-rc.' in version:
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

def generate_report(results: List[ValidationResult], output_dir: str, repo_name: str = "", pr_number: str = ""):
    """Generate comprehensive report and summary with unique filename"""
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
    
    # Generate detailed report
    with open(report_path, "w") as f:
        f.write("# CAMARA API Review - Detailed Report\n\n")
        
        # Add header information
        if repo_name:
            f.write(f"**Repository**: {repo_name}\n")
        if pr_number:
            f.write(f"**Pull Request**: #{pr_number}\n")
        f.write(f"**Generated**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"**Report File**: {report_filename}\n\n")
        
        # Summary statistics
        total_critical = sum(r.critical_count for r in results)
        total_medium = sum(r.medium_count for r in results)
        total_low = sum(r.low_count for r in results)
        
        f.write("## Summary\n\n")
        f.write(f"- **APIs Reviewed**: {len(results)}\n")
        f.write(f"- **Critical Issues**: {total_critical}\n")
        f.write(f"- **Medium Issues**: {total_medium}\n")
        f.write(f"- **Low Priority Issues**: {total_low}\n\n")
        
        # Collect unique checks performed across all APIs
        all_checks_performed = set()
        all_manual_checks = set()
        
        for result in results:
            all_checks_performed.update(result.checks_performed)
            all_manual_checks.update(result.manual_checks_needed)
        
        # Add consolidated check sections to summary
        if all_checks_performed:
            f.write("## Automated Checks Performed\n\n")
            for check in sorted(all_checks_performed):
                f.write(f"- {check}\n")
            f.write("\n")
        
        if all_manual_checks:
            f.write("## Manual Review Required\n\n")
            for check in sorted(all_manual_checks):
                f.write(f"- {check}\n")
            f.write("\n")
        
        # Detailed results for each API (simplified - no repeated check sections)
        f.write("## API-Specific Results\n\n")
        
        for result in results:
            f.write(f"### {result.api_name} (v{result.version})\n\n")
            f.write(f"**File**: `{result.file_path}`\n\n")
            
            if result.issues:
                # Group issues by severity
                critical_issues = [i for i in result.issues if i.severity == Severity.CRITICAL]
                medium_issues = [i for i in result.issues if i.severity == Severity.MEDIUM]
                low_issues = [i for i in result.issues if i.severity == Severity.LOW]
                
                for severity, issues in [
                    ("Critical Issues", critical_issues),
                    ("Medium Priority Issues", medium_issues),
                    ("Low Priority Issues", low_issues)
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
    
    # Generate summary for GitHub comment with 25-item limit
    with open(f"{output_dir}/summary.md", "w") as f:
        if not results:
            f.write("❌ **No API definition files found**\n\n")
            f.write("Please ensure YAML files are located in `/code/API_definitions/`\n")
            return report_filename
        
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
        
        # Enhanced issues detail with 25-item limit, prioritizing critical then medium
        if total_critical > 0 or total_medium > 0:
            # Determine what to show based on count - now using 25 as the limit
            if total_critical + total_medium <= 25:
                # Show both critical and medium when total is manageable (≤25)
                f.write("**Issues Requiring Attention**:\n")
                
                # Collect all issues from all APIs with their source
                all_critical_issues = []
                all_medium_issues = []
                
                for result in results:
                    critical_issues = [i for i in result.issues if i.severity == Severity.CRITICAL]
                    medium_issues = [i for i in result.issues if i.severity == Severity.MEDIUM]
                    
                    # Add API name to each issue for context
                    for issue in critical_issues:
                        all_critical_issues.append((result.api_name, issue))
                    for issue in medium_issues:
                        all_medium_issues.append((result.api_name, issue))
                
                # Show all critical issues first
                if all_critical_issues:
                    f.write(f"\n**🔴 Critical Issues ({len(all_critical_issues)}):**\n")
                    for api_name, issue in all_critical_issues:
                        f.write(f"- *{api_name}*: **{issue.category}** - {issue.description}\n")
                
                # Fill remaining slots with medium issues
                remaining_slots = 25 - len(all_critical_issues)
                medium_to_show = min(len(all_medium_issues), remaining_slots)
                
                if medium_to_show > 0:
                    f.write(f"\n**🟡 Medium Priority Issues ({medium_to_show}):**\n")
                    for api_name, issue in all_medium_issues[:medium_to_show]:
                        f.write(f"- *{api_name}*: **{issue.category}** - {issue.description}\n")
                
                # Note if there are more medium issues not shown
                if len(all_medium_issues) > medium_to_show:
                    f.write(f"\n*Note: {len(all_medium_issues) - medium_to_show} additional medium priority issues found. See detailed report for complete list.*\n")
            
            else:
                # Too many issues (>25 total) - show critical issues with selective medium
                f.write("**Critical Issues Requiring Immediate Attention**:\n")
                
                # Collect all critical issues
                all_critical_issues = []
                for result in results:
                    critical_issues = [i for i in result.issues if i.severity == Severity.CRITICAL]
                    for issue in critical_issues:
                        all_critical_issues.append((result.api_name, issue))
                
                # Show critical issues (up to 20 to leave room for some medium)
                critical_to_show = min(len(all_critical_issues), 20)
                
                if critical_to_show > 0:
                    f.write(f"\n**🔴 Critical Issues ({critical_to_show} of {len(all_critical_issues)}):**\n")
                    for api_name, issue in all_critical_issues[:critical_to_show]:
                        f.write(f"- *{api_name}*: **{issue.category}** - {issue.description}\n")
                
                # Note if more critical issues exist
                if len(all_critical_issues) > critical_to_show:
                    f.write(f"\n*... and {len(all_critical_issues) - critical_to_show} more critical issues*\n")
                
                # Show some medium issues if there's room and they exist
                remaining_slots = 25 - critical_to_show
                if remaining_slots > 0 and total_medium > 0:
                    all_medium_issues = []
                    for result in results:
                        medium_issues = [i for i in result.issues if i.severity == Severity.MEDIUM]
                        for issue in medium_issues:
                            all_medium_issues.append((result.api_name, issue))
                    
                    medium_to_show = min(len(all_medium_issues), remaining_slots)
                    if medium_to_show > 0:
                        f.write(f"\n**🟡 Sample Medium Priority Issues ({medium_to_show} of {len(all_medium_issues)}):**\n")
                        for api_name, issue in all_medium_issues[:medium_to_show]:
                            f.write(f"- *{api_name}*: **{issue.category}** - {issue.description}\n")
                
                # Add comprehensive note about remaining issues
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
    
    # Return the report filename for use by the workflow
    return report_filename

def main():
    """Main function - always exits with success after reporting findings"""
    if len(sys.argv) < 4 or len(sys.argv) > 6:
        print("Usage: python api_review_validator.py <repo_directory> <commonalities_version> <output_directory> [repo_name] [pr_number]")
        print("")
        print("This script analyzes API definitions and reports findings.")
        print("It does not judge whether findings constitute a failure - that decision is left to the workflow.")
        print("")
        print("Parameters:")
        print("  repo_directory: Path to the repository to analyze")
        print("  commonalities_version: CAMARA Commonalities version (e.g., 0.6)")
        print("  output_directory: Where to write the reports")
        print("  repo_name: (optional) Repository name for unique filename")
        print("  pr_number: (optional) PR number for unique filename")
        sys.exit(0)
    
    repo_dir = sys.argv[1]
    commonalities_version = sys.argv[2]
    output_dir = sys.argv[3]
    repo_name = sys.argv[4] if len(sys.argv) > 4 else ""
    pr_number = sys.argv[5] if len(sys.argv) > 5 else ""
    
    # Find API files
    api_files = find_api_files(repo_dir)
    
    if not api_files:
        print("❌ No API definition files found")
        print("Checked location: {}/code/API_definitions/".format(repo_dir))
        # Create empty results for summary
        report_filename = generate_report([], output_dir, repo_name, pr_number)
        print(f"📄 Empty report generated: {report_filename}")
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
    
    # Generate reports
    print(f"\n📄 Generating reports in {output_dir}...")
    try:
        report_filename = generate_report(results, output_dir, repo_name, pr_number)
        print(f"✅ Reports generated successfully")
        print(f"📄 Detailed report: {report_filename}")
    except Exception as e:
        print(f"❌ Error generating reports: {str(e)}")
        # Still exit successfully - we've done our job of analyzing
    
    total_critical = sum(r.critical_count for r in results)
    total_medium = sum(r.medium_count for r in results)
    
    print(f"\n🎯 **Review Complete**")
    if repo_name:
        print(f"Repository: {repo_name}")
    if pr_number:
        print(f"PR: #{pr_number}")
    print(f"Critical Issues: {total_critical}")
    print(f"Medium Issues: {total_medium}")
    print(f"Low Issues: {sum(r.low_count for r in results)}")
    
    # Always exit successfully - we are a reporter, not a judge
    print("\n📋 Analysis complete. Decision on release readiness is left to the workflow.")
    sys.exit(0)

if __name__ == "__main__":
    main()
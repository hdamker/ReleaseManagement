#!/usr/bin/env python3
"""
Debug Version - CAMARA API Review Validator v0.6
Focus on ensuring files are actually created and debugging issues
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
import traceback

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
    
    @property
    def critical_count(self) -> int:
        return len([i for i in self.issues if i.severity == Severity.CRITICAL])
    
    @property
    def medium_count(self) -> int:
        return len([i for i in self.issues if i.severity == Severity.MEDIUM])
    
    @property
    def low_count(self) -> int:
        return len([i for i in self.issues if i.severity == Severity.LOW])

def find_api_files(directory: str) -> List[str]:
    """Find all YAML files in the API definitions directory"""
    print(f"🔍 Looking for API files in: {directory}")
    
    # Try multiple possible locations
    possible_dirs = [
        os.path.join(directory, "code", "API_definitions"),
        os.path.join(directory, "API_definitions"),
        directory
    ]
    
    for api_dir in possible_dirs:
        print(f"  📁 Checking: {api_dir}")
        if os.path.exists(api_dir):
            print(f"  ✅ Directory exists: {api_dir}")
            yaml_files = []
            for pattern in ['*.yaml', '*.yml']:
                yaml_files.extend(Path(api_dir).glob(pattern))
            
            if yaml_files:
                print(f"  📄 Found {len(yaml_files)} YAML files")
                return [str(f) for f in yaml_files]
        else:
            print(f"  ❌ Directory not found: {api_dir}")
    
    return []

def validate_basic_api(file_path: str) -> ValidationResult:
    """Basic validation to test the pipeline"""
    print(f"📋 Validating: {file_path}")
    result = ValidationResult(file_path=file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            api_spec = yaml.safe_load(f)
        
        if not api_spec:
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "File Structure", "Empty or invalid YAML file"
            ))
            return result
        
        # Extract basic info
        info = api_spec.get('info', {})
        result.api_name = info.get('title', 'Unknown')
        result.version = info.get('version', 'Unknown')
        
        print(f"  📄 API: {result.api_name}")
        print(f"  🏷️ Version: {result.version}")
        
        # Basic checks
        result.checks_performed.append("OpenAPI version validation")
        openapi_version = api_spec.get('openapi')
        if openapi_version != '3.0.3':
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "OpenAPI Version",
                f"Must use OpenAPI 3.0.3, found: {openapi_version}",
                "Root level"
            ))
        
        # Check for wip version
        result.checks_performed.append("Work-in-progress version check")
        version = info.get('version', '')
        if version == 'wip':
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Version",
                "Work-in-progress version 'wip' cannot be released",
                "info.version"
            ))
        
        # Check commonalities version
        result.checks_performed.append("Commonalities version check")
        commonalities = info.get('x-camara-commonalities')
        if str(commonalities) != "0.6":
            result.issues.append(ValidationIssue(
                Severity.MEDIUM, "Info Object",
                f"Expected commonalities 0.6, found: {commonalities}",
                "info.x-camara-commonalities"
            ))
        
        # Check external docs
        result.checks_performed.append("ExternalDocs validation")
        external_docs = api_spec.get('externalDocs')
        if not external_docs:
            result.issues.append(ValidationIssue(
                Severity.CRITICAL, "ExternalDocs",
                "Missing externalDocs object",
                "externalDocs"
            ))
        
        # Check server URL for wip
        result.checks_performed.append("Server URL validation")
        servers = api_spec.get('servers', [])
        if servers:
            server_url = servers[0].get('url', '')
            if 'vwip' in server_url:
                result.issues.append(ValidationIssue(
                    Severity.CRITICAL, "Server URL",
                    "Server URL contains 'vwip' - not valid for release",
                    "servers[0].url"
                ))
        
        print(f"  ✅ Validation complete: {result.critical_count} critical, {result.medium_count} medium, {result.low_count} low")
        
    except yaml.YAMLError as e:
        result.issues.append(ValidationIssue(
            Severity.CRITICAL, "YAML Syntax", f"YAML parsing error: {str(e)}"
        ))
        print(f"  ❌ YAML Error: {str(e)}")
    except Exception as e:
        result.issues.append(ValidationIssue(
            Severity.CRITICAL, "Validation Error", f"Unexpected error: {str(e)}"
        ))
        print(f"  ❌ Validation Error: {str(e)}")
        print(f"  📋 Traceback: {traceback.format_exc()}")
    
    return result

def create_reports(results: List[ValidationResult], output_dir: str):
    """Create report files with extensive debugging"""
    print(f"\n📄 Starting report generation...")
    print(f"📁 Output directory: {output_dir}")
    print(f"📊 Results to process: {len(results)}")
    
    # Ensure output directory exists
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"✅ Output directory created/verified: {output_dir}")
        
        # Verify directory is writable
        test_file = os.path.join(output_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        print(f"✅ Directory is writable")
        
    except Exception as e:
        print(f"❌ Error with output directory: {str(e)}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        raise
    
    # Create summary report
    summary_path = os.path.join(output_dir, "summary.md")
    print(f"📝 Creating summary at: {summary_path}")
    
    try:
        with open(summary_path, "w", encoding='utf-8') as f:
            print(f"📄 Writing summary content...")
            
            if not results:
                f.write("❌ **No API definition files found**\n\n")
                f.write("Please ensure YAML files are located in `/code/API_definitions/`\n")
                print(f"📄 Wrote empty results summary")
            else:
                total_critical = sum(r.critical_count for r in results)
                total_medium = sum(r.medium_count for r in results)
                total_low = sum(r.low_count for r in results)
                
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
                f.write(f"- 🔵 Low: {total_low}\n\n")
                
                # Show critical issues
                if total_critical > 0:
                    f.write("**Critical Issues Requiring Immediate Attention**:\n")
                    for result in results:
                        critical_issues = [i for i in result.issues if i.severity == Severity.CRITICAL]
                        if critical_issues:
                            f.write(f"\n*{result.api_name}*:\n")
                            for issue in critical_issues[:5]:  # Show first 5
                                f.write(f"- **{issue.category}**: {issue.description}\n")
                            if len(critical_issues) > 5:
                                f.write(f"- ... and {len(critical_issues) - 5} more critical issues\n")
                    f.write("\n")
                
                # Recommendation
                if total_critical == 0 and total_medium == 0:
                    f.write("**Recommendation**: ✅ Approved for release\n")
                elif total_critical == 0:
                    f.write("**Recommendation**: ⚠️ Approved with improvements recommended\n")
                else:
                    f.write(f"**Recommendation**: ❌ Address {total_critical} critical issue(s) before release\n")
                
                f.write("\n📄 **Detailed Report**: Download the artifact for complete analysis\n")
                
                print(f"📄 Wrote summary with {total_critical} critical and {total_medium} medium issues")
        
        # Verify file was created and has content
        if os.path.exists(summary_path):
            file_size = os.path.getsize(summary_path)
            print(f"✅ Summary file created successfully")
            print(f"📊 File size: {file_size} bytes")
            
            # Read back first few lines to verify content
            with open(summary_path, "r", encoding='utf-8') as f:
                first_lines = f.readlines()[:3]
                print(f"📄 First lines: {[line.strip() for line in first_lines]}")
        else:
            print(f"❌ Summary file was not created!")
            
    except Exception as e:
        print(f"❌ Error creating summary: {str(e)}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        
        # Create minimal fallback
        try:
            print(f"📄 Creating fallback summary...")
            with open(summary_path, "w", encoding='utf-8') as f:
                f.write("❌ **API Review Error**\n\n")
                f.write(f"Report generation failed: {str(e)}\n\n")
                if results:
                    f.write(f"Found {len(results)} API file(s) but couldn't process fully.\n")
            print(f"✅ Fallback summary created")
        except Exception as fallback_error:
            print(f"❌ Even fallback failed: {str(fallback_error)}")
    
    # Create detailed report
    detailed_path = os.path.join(output_dir, "detailed-report.md")
    print(f"📝 Creating detailed report at: {detailed_path}")
    
    try:
        with open(detailed_path, "w", encoding='utf-8') as f:
            f.write("# CAMARA API Review - Detailed Report\n\n")
            f.write(f"**Generated**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
            
            if not results:
                f.write("No API files found for review.\n")
            else:
                total_critical = sum(r.critical_count for r in results)
                total_medium = sum(r.medium_count for r in results)
                total_low = sum(r.low_count for r in results)
                
                f.write("## Summary\n\n")
                f.write(f"- **APIs Reviewed**: {len(results)}\n")
                f.write(f"- **Critical Issues**: {total_critical}\n")
                f.write(f"- **Medium Issues**: {total_medium}\n")
                f.write(f"- **Low Priority Issues**: {total_low}\n\n")
                
                # Details for each API
                for result in results:
                    f.write(f"## {result.api_name} (v{result.version})\n\n")
                    f.write(f"**File**: `{result.file_path}`\n\n")
                    
                    if result.issues:
                        # Group by severity
                        critical_issues = [i for i in result.issues if i.severity == Severity.CRITICAL]
                        medium_issues = [i for i in result.issues if i.severity == Severity.MEDIUM]
                        low_issues = [i for i in result.issues if i.severity == Severity.LOW]
                        
                        for severity_name, issues in [
                            ("Critical Issues", critical_issues),
                            ("Medium Priority Issues", medium_issues),
                            ("Low Priority Issues", low_issues)
                        ]:
                            if issues:
                                f.write(f"### {severity_name}\n\n")
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
                    f.write("### Checks Performed\n\n")
                    for check in result.checks_performed:
                        f.write(f"- {check}\n")
                    f.write("\n---\n\n")
        
        if os.path.exists(detailed_path):
            file_size = os.path.getsize(detailed_path)
            print(f"✅ Detailed report created successfully ({file_size} bytes)")
        else:
            print(f"❌ Detailed report was not created!")
            
    except Exception as e:
        print(f"❌ Error creating detailed report: {str(e)}")
        print(f"📋 Traceback: {traceback.format_exc()}")
    
    # Final verification
    print(f"\n📋 Final verification:")
    for filename in ["summary.md", "detailed-report.md"]:
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"  ✅ {filename}: {size} bytes")
        else:
            print(f"  ❌ {filename}: NOT FOUND")

def main():
    """Main function with extensive debugging"""
    print("🚀 CAMARA API Review Validator v0.6 (Debug Version)")
    print(f"📋 Command line args: {sys.argv}")
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Current working directory: {os.getcwd()}")
    
    if len(sys.argv) != 4:
        print("❌ Usage: python api_review_validator_v0_6.py <repo_directory> <commonalities_version> <output_directory>")
        sys.exit(0)
    
    repo_dir = sys.argv[1]
    commonalities_version = sys.argv[2]
    output_dir = sys.argv[3]
    
    print(f"📁 Repository directory: {repo_dir}")
    print(f"🏷️ Commonalities version: {commonalities_version}")
    print(f"📊 Output directory: {output_dir}")
    
    # Check if repo directory exists
    if not os.path.exists(repo_dir):
        print(f"❌ Repository directory does not exist: {repo_dir}")
        # Create empty report anyway
        try:
            create_reports([], output_dir)
        except Exception as e:
            print(f"❌ Failed to create empty reports: {str(e)}")
        sys.exit(0)
    
    print(f"✅ Repository directory exists")
    
    # Find API files
    api_files = find_api_files(repo_dir)
    
    if not api_files:
        print("❌ No API definition files found")
        try:
            create_reports([], output_dir)
        except Exception as e:
            print(f"❌ Failed to create empty reports: {str(e)}")
        sys.exit(0)
    
    print(f"✅ Found {len(api_files)} API file(s):")
    for file in api_files:
        print(f"  📄 {file}")
    
    # Validate each file
    results = []
    for api_file in api_files:
        try:
            result = validate_basic_api(api_file)
            results.append(result)
        except Exception as e:
            print(f"❌ Error validating {api_file}: {str(e)}")
            error_result = ValidationResult(file_path=api_file)
            error_result.issues.append(ValidationIssue(
                Severity.CRITICAL, "Validation Error", f"Failed to validate: {str(e)}"
            ))
            results.append(error_result)
    
    print(f"\n📊 Validation Summary:")
    total_critical = sum(r.critical_count for r in results)
    total_medium = sum(r.medium_count for r in results)
    total_low = sum(r.low_count for r in results)
    
    print(f"  🔴 Critical: {total_critical}")
    print(f"  🟡 Medium: {total_medium}")
    print(f"  🔵 Low: {total_low}")
    
    # Create reports
    try:
        create_reports(results, output_dir)
        print(f"✅ Report creation completed")
    except Exception as e:
        print(f"❌ Report creation failed: {str(e)}")
        print(f"📋 Traceback: {traceback.format_exc()}")
    
    print(f"\n🎯 Review Complete!")
    sys.exit(0)

if __name__ == "__main__":
    main()
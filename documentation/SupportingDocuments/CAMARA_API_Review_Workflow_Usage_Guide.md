# CAMARA API Review Workflow - Usage Guide

**Location**: `/documentation/SupportingDocuments/CAMARA_API_Review_Workflow_Usage_Guide.md`

## Overview

This GitHub workflow system provides automated validation of CAMARA API definitions against the comprehensive review checklist. It can be triggered in two ways: **automatically via issue comments** or **manually via workflow dispatch** from the ReleaseManagement repository to review pull requests in any CAMARA project repository.

## Quick Start (Recommended Method)

**For most release reviews, use the comment trigger:**

1. **Prepare issue**: Ensure your release review issue has the PR URL on line 3 or 4:
   ```markdown
   # Release Review for MyAPI v1.0.0-rc.1
   
   https://github.com/camaraproject/MyAPI/pull/123
   ```

2. **Trigger review**: Comment `/rc-api-review` in the issue

3. **Wait for results**: Bot will post results automatically in the same issue

**That's it!** The workflow uses sensible defaults for most release candidate reviews.

---

| Aspect | Comment Trigger | Manual Trigger |
|--------|----------------|----------------|
| **Convenience** | ⭐⭐⭐ Very easy - just comment `/rc-api-review` | ⭐⭐ Requires navigating to Actions tab |
| **Setup Required** | PR URL must be in issue description (lines 3-4) | Manual entry of all parameters |
| **Customization** | Uses defaults (release-candidate, v0.6) | Full control over all parameters |
| **Use Case** | Standard release reviews | Special cases, different parameters |
| **User Permission** | Anyone who can comment on issues | Users with Actions workflow permissions |
| **Audit Trail** | Visible in issue comments | Visible in Actions history |

## Architecture

```
ReleaseManagement Repo (Trigger)
    ↓ Manual Dispatch
┌─────────────────────────────────┐
│  api-review-trigger.yml         │
│  - Validates inputs             │
│  - Calls reusable workflow      │
│  - Posts results to issue       │
└─────────────────────────────────┘
    ↓ Calls
┌─────────────────────────────────┐
│  api-review-reusable.yml        │
│  - Checks out PR branch         │
│  - Runs validation script       │
│  - Generates reports            │
│  - Creates artifacts            │
└─────────────────────────────────┘
```

## Setup Instructions

### 1. Install Workflows in ReleaseManagement Repository

Place the workflow files in the `.github/workflows/` directory of the ReleaseManagement repository:

```
ReleaseManagement/
├── .github/
│   └── workflows/
│       ├── api-review-trigger.yml      # Main trigger workflow
│       └── api-review-reusable.yml     # Reusable validation workflow
└── documentation/
    └── SupportingDocuments/
        └── CAMARA_API_Review_Workflow_Usage_Guide.md  # This guide
```

### 2. Required Permissions

Ensure the ReleaseManagement repository has:

- **Read access** to all CAMARA project repositories
- **Write access** to post comments on its own issues
- **Actions permissions** to run workflows

### 3. GitHub Token Configuration

The workflows use `secrets.GITHUB_TOKEN` which should have sufficient permissions to:
- Read pull requests from other CAMARA repositories
- Post comments to issues in ReleaseManagement repository
- Access repository contents

## Usage Instructions

The workflow can be triggered in two ways:

### Method 1: Comment Trigger (Recommended)

This is the most convenient method for release managers.

#### Step 1: Prepare the Release Review Issue

1. Create or navigate to a release review issue in the ReleaseManagement repository
2. Ensure the issue description contains the PR URL on line 3 or 4
3. The URL must be in the format: `https://github.com/camaraproject/[repo]/pull/[number]`

**Example issue description:**
```markdown
# Release Review for QualityOnDemand v1.2.0-rc.1

Review request for the following pull request:
https://github.com/camaraproject/QualityOnDemand/pull/456

Please review the API definitions and provide feedback.
```

#### Step 2: Trigger the Review

1. In the release review issue, add a comment that starts with: `/rc-api-review`
2. The workflow will automatically:
   - Extract the PR URL from the issue description (lines 3-4)
   - Use default values: `review_type=release-candidate`, `commonalities_version=0.6`
   - Post results back to the same issue

**Example comment:**
```
/rc-api-review
```

You can add additional text after the trigger:
```
/rc-api-review

Please run the automated review for the latest changes.
```

#### Step 3: Monitor Results

1. The bot will immediately post an acknowledgment comment
2. Review results will be posted to the same issue when complete
3. Detailed reports are available as workflow artifacts

### Method 2: Manual Trigger (Alternative)

For more control over parameters or when the issue format doesn't match expectations.

#### Step 1: Create or Identify Release Review Issue

1. Create or navigate to a release review issue in the ReleaseManagement repository
2. Note the issue number (e.g., #123)

#### Step 2: Identify Target Pull Request

1. Navigate to the CAMARA project repository (e.g., QualityOnDemand, DeviceLocation)
2. Find the pull request you want to review
3. Copy the full PR URL (e.g., `https://github.com/camaraproject/QualityOnDemand/pull/456`)

#### Step 3: Trigger the Review

1. Go to **Actions** tab in ReleaseManagement repository
2. Select **"CAMARA API Review Trigger"** workflow
3. Click **"Run workflow"**
4. Fill in the required parameters:

   ```
   Pull Request URL: https://github.com/camaraproject/QualityOnDemand/pull/456
   Issue Number: 123
   Review Type: release-candidate
   Commonalities Version: 0.6
   ```

5. Click **"Run workflow"**

### Monitor Execution and Review Results

Both trigger methods follow the same execution and results process:

#### Workflow Execution
1. Watch the workflow execution in the Actions tab (for manual triggers) or wait for completion (for comment triggers)
2. The workflow will:
   - Validate the PR URL and check PR status
   - Check out the PR branch
   - Find API definition files in `/code/API_definitions/`
   - Run comprehensive validation checks
   - Generate reports

#### Automatic Issue Comment
A summary will be automatically posted to the specified issue, including:
- Trigger method (comment by user or manual dispatch)
- List of APIs found and their versions
- Count of critical, medium, and low priority issues
- Summary of critical issues requiring immediate attention
- Overall recommendation (Ready/Conditional/Critical Issues)

#### Detailed Report Download
1. Go to the workflow run page (link provided in issue comment)
2. Scroll to **"Artifacts"** section
3. Download **"api-review-detailed-report"**
4. Open `detailed-report.md` for complete analysis

## Comment Trigger Examples

### Valid Issue Description Formats

**Format 1 - PR URL on line 3:**
```markdown
# Release Review for DeviceLocation v0.3.0-rc.2

API review needed for:
https://github.com/camaraproject/DeviceLocation/pull/234

Deadline: March 15, 2024
```

**Format 2 - PR URL on line 4:**
```markdown
# Release Review for SimSwap v1.0.0-rc.1

This release includes the following changes:
- Updated error handling
https://github.com/camaraproject/SimSwap/pull/89

Please review and approve.
```

**Format 3 - PR URL embedded in text (line 3):**
```markdown
# Release Review for QualityOnDemand v2.1.0-rc.1

Ready for review: https://github.com/camaraproject/QualityOnDemand/pull/456 contains all changes.

Status: Pending review
```

### Comment Trigger Examples

**Simple trigger:**
```
/rc-api-review
```

**With additional context:**
```
/rc-api-review

Running automated review for the latest API changes. Please hold manual review until this completes.
```

**Response to previous comments:**
```
@developer123 thanks for the updates!

/rc-api-review

Let's run the automated checks before final approval.
```

### Expected Bot Responses

**Acknowledgment comment (immediate):**
```
🤖 **API Review Triggered**

Starting automated CAMARA API review...

**Details:**
- Pull Request: https://github.com/camaraproject/QualityOnDemand/pull/456
- Review Type: release-candidate
- Commonalities Version: 0.6

Results will be posted here when the review completes.
```

**Results comment (after completion):**
```
## 🤖 Automated CAMARA API Review Results

**Triggered by**: Comment `/rc-api-review` by @release-manager
**Pull Request**: [camaraproject/QualityOnDemand#456](https://github.com/camaraproject/QualityOnDemand/pull/456)
**Review Type**: release-candidate
**Workflow Run**: [View Details](...)

### ⚠️ **Conditional Approval**

**APIs Reviewed**:
- `Quality On Demand` v2.1.0-rc.1

**Issues Summary**:
- 🔴 Critical: 1
- 🟡 Medium: 2
- 🔵 Low: 0

**Critical Issues Requiring Immediate Attention**:

*Quality On Demand*:
- ExternalDocs: Missing externalDocs object

**Recommendation**: ❌ Address 1 critical issue(s) before release

📄 **[Download Detailed Report](...)** for complete analysis
```

## Supported Review Types

### `release-candidate`
- For versions like `0.1.0-rc.1`, `1.2.0-rc.3`
- Validates server URL format: `v0.1rc1`, `v2rc3`
- Strict compliance checking

### `alpha`  
- For versions like `0.1.0-alpha.2`
- Validates server URL format: `v0.1alpha2`
- Allows some flexibility for experimental features

### `public-release`
- For stable versions like `1.0.0`, `0.3.0`
- Validates server URL format: `v1`, `v0.3`
- Strictest compliance requirements

## What Gets Checked Automatically

### ✅ **Critical Compliance Checks**
- OpenAPI 3.0.3 specification compliance
- Info object validation (title, version, license)
- Server URL format for version type
- ExternalDocs object presence
- Security schemes validation
- Forbidden error codes (IDENTIFIER_MISMATCH, AUTHENTICATION_REQUIRED)
- X-correlator pattern compliance
- Mandatory description templates

### ✅ **Medium Priority Checks**
- RFC 3339 descriptions for date-time fields
- Reserved words usage
- File naming conventions
- License and commonalities version alignment
- Device schema compliance (if applicable)

### ✅ **Low Priority Checks**
- Code style and naming conventions
- Schema completeness
- Documentation quality indicators

### ❌ **Manual Review Still Required**
- Business logic appropriateness
- API design patterns validation
- Use case coverage evaluation
- Security considerations beyond structure
- Cross-file reference validation
- Performance and scalability considerations

## Example Workflow Run

### Input:
```yaml
Pull Request URL: https://github.com/camaraproject/DedicatedNetworks/pull/42
Issue Number: 156
Review Type: release-candidate
Commonalities Version: 0.6
```

### Output Summary (Posted to Issue #156):
```markdown
## 🤖 Automated CAMARA API Review Results

**Pull Request**: [camaraproject/DedicatedNetworks#42](https://github.com/camaraproject/DedicatedNetworks/pull/42)
**Review Type**: release-candidate
**Workflow Run**: [View Details](...)

### ⚠️ **Conditional Approval**

**APIs Reviewed**:
- `Dedicated Network - Networks` v0.1.0-rc.1
- `Dedicated Network - Network Profiles` v0.1.0-rc.1
- `Dedicated Network - Accesses` v0.1.0-rc.1

**Issues Summary**:
- 🔴 Critical: 3
- 🟡 Medium: 2
- 🔵 Low: 1

**Critical Issues Requiring Immediate Attention**:

*Dedicated Network - Networks*:
- ExternalDocs: Missing externalDocs object

*Dedicated Network - Accesses*:
- Error Responses: Forbidden error code 'IDENTIFIER_MISMATCH' found
- Security Schemes: Undefined security scheme 'oAuth2' referenced

**Recommendation**: ❌ Address 3 critical issue(s) before release

📄 **[Download Detailed Report](...)** for complete analysis
```

## Troubleshooting

### Comment Trigger Issues

#### "No valid CAMARA PR URL found in lines 3-4 of issue description"
- Ensure the PR URL is on line 3 or 4 of the issue description
- URL must start with `https://github.com/camaraproject/`
- URL must follow exact format: `https://github.com/camaraproject/[repo]/pull/[number]`
- Check for extra characters or formatting

**Example of correct format:**
```markdown
Line 1: # Release Review Title
Line 2: 
Line 3: https://github.com/camaraproject/QualityOnDemand/pull/456
Line 4: 
```

#### "Comment does not start with '/rc-api-review'"
- Ensure the comment starts exactly with `/rc-api-review`
- Case sensitive - must be lowercase
- No spaces before the command
- Additional text after the command is allowed

#### No Response from Bot
- Check that the comment was posted in the ReleaseManagement repository
- Verify GitHub Actions are enabled in the repository
- Check workflow permissions in repository settings
- Look for workflow runs in the Actions tab

#### Bot Posts Acknowledgment but No Results
- Check the workflow run for errors (link provided in acknowledgment)
- Verify the target repository and PR are accessible
- Check if API definition files exist in expected locations

### Manual Trigger Issues

#### "Invalid PR URL format"
- Ensure URL follows exact format: `https://github.com/owner/repo/pull/123`
- No trailing slashes or query parameters
- Must be from camaraproject organization

#### "Repository must be from camaraproject organization"
- URL must start with `https://github.com/camaraproject/`
- Verify the repository name is correct

### Common Issues (Both Methods)

#### "PR is not open or does not exist"
- Verify the PR number is correct
- Ensure the PR is still open
- Check repository name spelling

#### "No API definition files found"
- Verify files are in `/code/API_definitions/`
- Ensure files have `.yaml` or `.yml` extensions
- Check the PR branch has the expected file structure

#### "Workflow failed"
- Check the Actions logs for specific error messages
- Verify GitHub token permissions
- Ensure target repository is accessible

### Permission Issues

#### Comment Trigger Not Working
1. **Repository Settings**:
   - Ensure GitHub Actions are enabled
   - Check workflow permissions allow issue comments
   - Verify the bot has write access to issues

2. **Issue Access**:
   - Confirm the issue is in the ReleaseManagement repository
   - Check that the issue is open
   - Verify issue permissions

#### Manual Trigger Access Denied
1. **For ReleaseManagement repository**:
   - Ensure GitHub Actions are enabled
   - Check workflow permissions in repository settings
   - Verify user has Actions execution permissions

2. **For target repositories**:
   - Verify the GitHub token has read access
   - Check if the repository is private and permissions are sufficient

### Debug Steps

#### For Comment Triggers
1. Check if the comment appears in the issue
2. Look for workflow runs in ReleaseManagement → Actions
3. Search for runs triggered by "issue_comment"
4. Review the "check-comment-trigger" job logs

#### For Manual Triggers
1. Go to ReleaseManagement → Actions
2. Find the manually triggered workflow run
3. Review the "validate-input" job logs
4. Check PR URL parsing and validation steps

#### For Both Methods
1. Verify the target PR exists and is open
2. Check that API files exist in `/code/API_definitions/`
3. Review the detailed validation logs in the "api-review" job
4. Download workflow artifacts if available

## Customization

### Modifying Validation Rules

To add or modify validation checks:

1. Edit the embedded Python script in `api-review-reusable.yml`
2. Add new validation methods to the `CAMARAAPIValidator` class
3. Call new methods from `validate_api_file()`
4. Update the `manual_checks_needed` list as appropriate

### Adding New Review Types

To support additional review types:

1. Add new option to `review_type` input in trigger workflow
2. Update URL validation logic in reusable workflow
3. Modify Python script to handle new version patterns

### Changing Report Format

To customize report generation:

1. Modify the `generate_report()` function in the Python script
2. Update markdown templates for summary and detailed reports
3. Adjust artifact names and retention policies as needed

## Security Considerations

- Workflows only have **read access** to target repositories
- No sensitive data is stored or transmitted
- All validation is performed in isolated GitHub Actions runners
- Reports contain only structural/compliance information, not business logic details

## Limitations

1. **File Location**: Only checks standard CAMARA directories
2. **Cross-file References**: Limited validation of external references
3. **Business Logic**: Cannot validate API design appropriateness
4. **Real-time Data**: No validation against external systems or live endpoints
5. **Language Support**: Currently focused on YAML/OpenAPI definitions only

## Support and Feedback

For issues with the workflow system:
1. Check the GitHub Actions logs for detailed error information
2. Review this usage guide for common troubleshooting steps
3. Create an issue in the ReleaseManagement repository with workflow run details
# CAMARA API Review Workflow - Usage Guide

**Location**: `/documentation/SupportingDocuments/CAMARA_API_Review_Workflow_Usage_Guide.md`

## Overview

This GitHub workflow system provides automated validation of CAMARA API definitions against the comprehensive review checklist. It can be triggered in two ways: **automatically via issue comments** or **manually via workflow dispatch** from the ReleaseManagement repository to review pull requests in any CAMARA project repository.

The system uses **version-specific validators** to ensure compatibility with different CAMARA Commonalities releases, providing accurate validation rules for each version.

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

## Version Support

The workflow supports different CAMARA Commonalities versions with dedicated validation logic:

| Commonalities Version | Validator Script | Status | Key Validation Rules |
|----------------------|------------------|---------|---------------------|
| **0.6** | `api_review_validator_v0_6.py` | ✅ **Supported** | - Updated XCorrelator pattern<br>- UNAUTHENTICATED (not AUTHENTICATION_REQUIRED)<br>- No IDENTIFIER_MISMATCH<br>- Mandatory description templates |
| **0.7** | `api_review_validator_v0_7.py` | 📅 **Planned** | Future Commonalities 0.7 requirements |
| **0.8** | `api_review_validator_v0_8.py` | 📅 **Planned** | Future Commonalities 0.8 requirements |
| **1.0** | `api_review_validator_v1_0.py` | 📅 **Planned** | Future Commonalities 1.0 requirements |

## Architecture

```
ReleaseManagement Repo (Trigger & Reusable Workflows)
    ↓ Manual Dispatch or Comment Trigger
┌─────────────────────────────────────────┐
│  api-review-trigger.yml                 │
│  - Validates inputs                     │
│  - Validates version support            │
│  - Calls reusable workflow              │
│  - Posts results to issue               │
└─────────────────────────────────────────┘
    ↓ Calls
┌─────────────────────────────────────────┐
│  api-review-reusable.yml                │
│  - Validates Commonalities version      │
│  - Loads version-specific validator     │
│  - Checks out workflow repo             │
│  - Checks out PR branch                 │
│  - Runs validation script               │
│  - Generates reports                    │
│  - Creates artifacts                    │
└─────────────────────────────────────────┘
    ↓ Uses Version-Specific Script
┌─────────────────────────────────────────┐
│  /scripts/api_review_validator_v0_6.py  │
│  - Commonalities 0.6 validation logic  │
│  - Version-specific rules               │
│  - Must be in workflow repository       │
└─────────────────────────────────────────┘
```

## Setup Instructions

### 1. Install Components in ReleaseManagement Repository

Place the workflow files and validation scripts in the appropriate directories:

```
ReleaseManagement/
├── .github/
│   └── workflows/
│       ├── api-review-trigger.yml      # Main trigger workflow
│       └── api-review-reusable.yml     # Reusable validation workflow
├── scripts/
│   ├── api_review_validator_v0_6.py    # REQUIRED: Commonalities 0.6 validator
│   ├── api_review_validator_v0_7.py    # Future: Commonalities 0.7 validator
│   └── api_review_validator_v1_0.py    # Future: Commonalities 1.0 validator
└── documentation/
    └── SupportingDocuments/
        └── CAMARA_API_Review_Workflow_Usage_Guide.md  # This guide
```

**⚠️ CRITICAL REQUIREMENT**: Version-specific validator scripts **MUST** be present in the `/scripts/` directory. The workflow will fail with a helpful error message if the required script for the specified Commonalities version is missing.

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

## Self-Contained Design

The reusable workflow is **self-contained** and looks for its dependencies in the **same repository where it's defined**:

- ✅ **Workflow Repository** (`${{ github.repository }}`): Contains workflows and validation scripts
- ✅ **Target Repository**: The CAMARA project repository being reviewed
- ✅ **Version-Specific Scripts**: Each Commonalities version has its own validator
- ✅ **Separation Ready**: Trigger and reusable workflows can be in different repositories

**Example**:
- Workflows run from: `camaraproject/ReleaseManagement`
- Script expected at: `camaraproject/ReleaseManagement/scripts/api_review_validator_v0_6.py`
- Target review: `camaraproject/QualityOnDemand/pull/456`

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
   - Load the appropriate version-specific validator script
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

1. The bot will immediately post an acknowledgment comment with version information
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
   Commonalities Version: 0.6  (select from dropdown)
   ```

5. Click **"Run workflow"**

**Available Commonalities Versions:**
- ✅ `0.6` - Fully supported
- ⏳ `0.7` - Shows helpful error message
- ⏳ `0.8` - Shows helpful error message  
- ⏳ `1.0` - Shows helpful error message

### Monitor Execution and Review Results

Both trigger methods follow the same execution and results process:

#### Workflow Execution
1. Watch the workflow execution in the Actions tab (for manual triggers) or wait for completion (for comment triggers)
2. The workflow will:
   - Validate the Commonalities version support
   - Validate the PR URL and check PR status
   - Check out the workflow repository (for validation script)
   - Load the version-specific validator script
   - Check out the PR branch (target repository)
   - Find API definition files in `/code/API_definitions/`
   - Run comprehensive validation checks using the correct validator
   - Generate reports

#### Automatic Issue Comment
A summary will be automatically posted to the specified issue, including:
- Trigger method (comment by user or manual dispatch)
- Commonalities version and validator used
- List of APIs found and their versions
- Count of critical, medium, and low priority issues
- Summary of critical issues requiring immediate attention
- Overall recommendation (Ready/Conditional/Critical Issues)

#### Detailed Report Download
1. Go to the workflow run page (link provided in issue comment)
2. Scroll to **"Artifacts"** section
3. Download **"api-review-detailed-report-{version}"** (e.g., `api-review-detailed-report-0.6`)
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

**Version Support:**
- ✅ Commonalities 0.6: Fully supported
- ⏳ Commonalities 0.7+: Coming soon

Results will be posted here when the review completes.
```

**Results comment (after completion):**
```
## 🤖 Automated CAMARA API Review Results

**Triggered by**: Comment `/rc-api-review` by @release-manager
**Pull Request**: [camaraproject/QualityOnDemand#456](https://github.com/camaraproject/QualityOnDemand/pull/456)
**Review Type**: release-candidate
**Commonalities Version**: 0.6
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

📄 **Detailed Report**: Download the `api-review-detailed-report-0.6` artifact from the workflow run for complete analysis
```

**Unsupported version error:**
```
## 🤖 Automated CAMARA API Review Results

**Triggered by**: Manual workflow dispatch
**Pull Request**: [camaraproject/QualityOnDemand#456](...)
**Review Type**: release-candidate
**Commonalities Version**: 0.7
**Workflow Run**: [View Details](...)

### ❌ **Unsupported Commonalities Version**

**Error**: Commonalities version 0.7 is not yet supported. Currently supported versions: 0.6

**Requested Version**: `0.7`
**Currently Supported**: `0.6`

**What to do:**
1. **For Commonalities 0.6**: Change the version parameter to `0.6`
2. **For other versions**: Wait for support to be added or contact the maintainers

**Upcoming Support:**
- 📅 Commonalities 0.7: Planned
- 📅 Commonalities 0.8: Planned  
- 📅 Commonalities 1.0: Planned

**Manual Review Required**: Please use the manual review process for unsupported Commonalities versions.
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

### Version-Specific Validation (Commonalities 0.6)

#### ✅ **Critical Compliance Checks**
- OpenAPI 3.0.3 specification compliance
- Info object validation (title, version, license)
- Server URL format for version type
- ExternalDocs object presence
- Security schemes validation
- **Forbidden error codes**: IDENTIFIER_MISMATCH, AUTHENTICATION_REQUIRED
- **Required error codes**: UNAUTHENTICATED (instead of AUTHENTICATION_REQUIRED)
- **X-correlator pattern**: `^[a-zA-Z0-9-_:;.\/<>{}]{0,256}$`
- Mandatory description templates

#### ✅ **Medium Priority Checks**
- RFC 3339 descriptions for date-time fields
- Reserved words usage
- File naming conventions
- License and commonalities version alignment
- Device schema compliance (if applicable)

#### ✅ **Low Priority Checks**
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
**Commonalities Version**: 0.6
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

📄 **Detailed Report**: Download the `api-review-detailed-report-0.6` artifact from the workflow run for complete analysis
```

## Troubleshooting

### Version-Specific Issues

#### "❌ Version-specific API Validator script not found!"
This is the most common issue when the required validator script is missing:

```
❌ Version-specific API Validator script not found!
Expected location: review-tools/scripts/api_review_validator_v0_6.py
Workflow repository: camaraproject/ReleaseManagement
Commonalities version: 0.6

📋 Supported Commonalities versions and their scripts:
  - 0.6: api_review_validator_v0_6.py
  - Future versions will have their own scripts
```

**Solutions:**
1. **Check script location**: Ensure `api_review_validator_v0_6.py` exists at `/scripts/api_review_validator_v0_6.py` in your workflow repository
2. **Check file permissions**: Make sure the script is readable
3. **Check repository**: Verify you're running workflows from the repository that contains the script
4. **Check naming**: Script name must be exact: `api_review_validator_v0_6.py`

#### "❌ Unsupported Commonalities Version"
**Expected behavior** for versions other than 0.6:

```
❌ Commonalities 0.7 is not yet supported
```

**Solutions:**
1. **Use 0.6**: Change version parameter to `0.6` for current reviews  
2. **Wait for support**: Future versions will be added as new Commonalities releases
3. **Manual review**: Use traditional review process for unsupported versions

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
- **Most common**: Check if the Python validation script exists

### Debug Steps

#### For Version-Specific Issues
1. **Verify script exists**: Check `scripts/api_review_validator_v0_6.py` in your workflow repository
2. **Check workflow logs**: Look for the "Locate Version-Specific API Validator Script" step
3. **Verify version support**: Ensure you're using Commonalities 0.6
4. **Check version validation**: Look for "Validate Commonalities Version Support" step

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
5. **Always check**: Ensure version-specific validator script exists in workflow repository

## Repository Setup Requirements

### For Running Your Own Instance

If you want to run the workflows from your own fork or repository:

1. **Fork or copy** the ReleaseManagement repository
2. **Ensure the following files exist**:
   ```
   your-repo/
   ├── .github/workflows/
   │   ├── api-review-trigger.yml
   │   └── api-review-reusable.yml
   ├── scripts/
   │   └── api_review_validator_v0_6.py  # CRITICAL: Must exist for 0.6 support
   └── documentation/...
   ```
3. **Configure permissions** for accessing other CAMARA repositories
4. **Test with a simple PR** to verify everything works

### For Official CAMARA Usage

When using in production CAMARA environment:

1. **Upload all required files** to `camaraproject/ReleaseManagement`:
   - `api-review-trigger.yml`
   - `api-review-reusable.yml` 
   - `scripts/api_review_validator_v0_6.py`
2. **Configure repository permissions** for cross-repository access
3. **Test thoroughly** with existing release candidate PRs
4. **Plan for future versions** by adding validator scripts as new Commonalities releases

## Adding Support for Future Versions

### For Maintainers: Adding New Commonalities Version

When a new Commonalities version (e.g., 0.7) is released:

1. **Create version-specific validator script**:
   ```
   scripts/api_review_validator_v0_7.py
   ```

2. **Update version validation logic** in `api-review-reusable.yml`:
   ```yaml
   case "$COMMONALITIES_VERSION" in
     "0.6")
       echo "validator_script=api_review_validator_v0_6.py" >> $GITHUB_OUTPUT
       ;;
     "0.7")  # Add new version
       echo "validator_script=api_review_validator_v0_7.py" >> $GITHUB_OUTPUT
       ;;
   ```

3. **Update trigger workflow** dropdown options in `api-review-trigger.yml`:
   ```yaml
   commonalities_version:
     type: choice
     options:
       - '0.6'
       - '0.7'  # Add new option
   ```

4. **Test thoroughly** with both comment and manual triggers
5. **Update documentation** to reflect new version support

## Security Considerations

- Workflows only have **read access** to target repositories
- No sensitive data is stored or transmitted
- All validation is performed in isolated GitHub Actions runners
- Reports contain only structural/compliance information, not business logic details
- **Version-specific scripts** must be maintained and secured in the workflow repository
- **Script isolation**: Each version uses its own validator to prevent cross-contamination

## Limitations

1. **File Location**: Only checks standard CAMARA directories (`/code/API_definitions/`)
2. **Cross-file References**: Limited validation of external references
3. **Business Logic**: Cannot validate API design appropriateness
4. **Real-time Data**: No validation against external systems or live endpoints
5. **Language Support**: Currently focused on YAML/OpenAPI definitions only
6. **Version Dependencies**: Requires manual maintenance of version-specific validation scripts
7. **Version Support**: Currently limited to Commonalities 0.6

## Support and Feedback

For issues with the workflow system:
1. **Check version compatibility**: Verify you're using Commonalities 0.6
2. **Check script location**: Verify `scripts/api_review_validator_v0_6.py` exists in workflow repository
3. **Check the GitHub Actions logs** for detailed error information
4. **Review this usage guide** for common troubleshooting steps
5. **Create an issue** in the ReleaseManagement repository with:
   - Workflow run details
   - Commonalities version used
   - Error messages from logs
   - Expected vs. actual behavior
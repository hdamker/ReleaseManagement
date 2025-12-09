# PROPOSED PRESENTATION CONTENT PLAN

## Slide 1: Title
- **Headline**: CAMARA Release Process Update
- **Sub-headline**: Introduction to the Metadata-Driven Release Workflow

## Slide 2: Context & Motivation
- **Title**: Context & Motivation
- **Content (Bullet Points)**:
    - **Current Challenges**:
        - Manual Overhead: Manually creating release notes, changelogs, and tagging releases is time-consuming.
        - Inconsistency: Different APIs have different release artifacts and quality.
        - Versioning Errors: Manual SemVer management leads to mistakes.
    - **Objectives of the New Process**:
        - Automation: Generate artifacts (Changelogs, API bundles) automatically.
        - Consistency: Uniform structure and quality across all repositories.
        - Reliability: Strict adherence to SemVer and release readiness standards.

## Slide 3: Legacy vs. New Process
- **Title**: Legacy vs. New Process
- **Content**:
    - **Table (Full Content)**:
        | Feature | Legacy Process (Wiki/Excel) | New Process (Metadata) |
        | :--- | :--- | :--- |
        | Tracking | Manual updates in Atlassian Wiki / Jira | release-plan.yaml (Living Plan in Repo) |
        | Versioning | Manually decided & committed | Calculated from Plan + Git History |
        | Artifacts | Manually written Release Notes | Auto-generated release-metadata.yaml & Changelogs |
        | Branching | Ad-hoc or strict GitFlow | Automated release/rX.Y branches |
        | Validation | Manual checks at release time | CI checks Planning & Readiness continuously |
    - **Visuals**: (Inserted small, to be arranged manually by user)
        - `manual_process_legacy.png`
        - `automated_process_modern.png`

## Slide 4: Key Concepts: The Control Files
- **Title**: Key Concept: The Control Files
- **Content**:
    - **1. release-plan.yaml (The Intent)**
        - **Where**: On main branch.
        - **Who Edits**: Codeowners.
        - **Purpose**: Tells the automation what you want to happen next.
        - **Example**: "We are aiming for version 1.1.0, and it's currently a Release Candidate."
    - **2. release-metadata.yaml (The Record)**
        - **Where**: On release tags (e.g., r1.2).
        - **Who Edits**: Automation (Robot).
        - **Purpose**: A frozen historical record of what was actually released.
        - **Example**: "This is release r1.2, released on Oct 10th, containing Location API v1.1.0-rc.1."
    - **Visuals**: (Inserted small/placeholder)
        - `release_plan_intent_v2.png`
        - `release_metadata_record.png`

## Slide 5: The New Release Workflow & Details
- **Title**: The New Release Workflow
- **Content Layout**:
    - **Left Column: The 5 Steps**:
        1. **Develop & Plan (on main)**: Update `release-plan.yaml`.
        2. **Trigger Release**: Add label `trigger-release`.
        3. **Automated Preparation**: CI creates release branch & artifacts.
        4. **Review PR**: Codeowners verify changes.
        5. **Approve & Publish**: Merging triggers tag & sync.
    - **Right Column: Deep Dive (Step 1 & 3)**:
        - **Step 1: Planning (Manual)**
            - Codeowners update `release-plan.yaml`.
            - CI checks validation.
        - **Step 3: Branch Creation (Automated)**
            - Input: Plan + Git History.
            - Output: `release/rX.Y` branch + `release-metadata.yaml`.
    - **Visual**: Vertical Workflow Diagram (nicer style).

## Slide 6: Release Tracks
- **Title**: Release Tracks
- **Content**:
    - "Not all APIs move at the same speed."
    - **1. Meta-Release Track (Coordinated)**
        - Aligned with CAMARA-wide Spring/Fall releases.
        - Strict deadlines (Code Freeze).
        - Ready for Telco deployment.
    - **2. Sandbox Track (Independent)**
        - For experimental or new APIs.
        - Release whenever you want.
        - Good for rapid iteration and feedback.

## Slide 7: Summary & Timeline
- **Title**: Summary & Next Steps
- **Content**:
    - **Status**: The process is defined but implementation is in progress.
    - **Rollout**:
        - Rollout of release-plan.yaml to all repositories within in **January 2026**
        - Initially mainly as replacement of manual wiki release trackers
    - **Pilot Phase of automation**
        - Selected repositories will pilot the automation.
        - Feedback from pilot will refine the tooling.
        - Gradual rollout of automation to all sub-projects in Q1 2026.
    - **Action**: Codeowners should start familiarizing themselves with `release-plan.yaml` concepts.


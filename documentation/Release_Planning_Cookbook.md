# Release Planning Cookbook

This guide provides practical "recipes" for editing your `release-plan.yaml`. This file, located at the root of your repository, is the source of truth for the release automation.

> **Tip**: The `release-plan.yaml` describes **what you want to happen**. It doesn't instantly trigger a release; it sets the stage for the next trigger.

## Basic Concepts

- **`target_version`**: The exact MAJOR.MINOR.PATCH version you want to release. Do not include suffixes like `-alpha.1` or `-rc.2`; the automation handles those.
- **`api_status`**: The maturity level of the API.
    - `draft`: Work in progress (no release).
    - `alpha`: Early feedback (creates `x.y.z-alpha.N`).
    - `rc`: Release Candidate (creates `x.y.z-rc.N`). Mandatory before public.
    - `public`: Official Release (creates `x.y.z`).

---

## Recipe 0: Drafting (Inception)
**Scenario**: You are starting a new API. You have no OpenAPI file yet, but want to register your intent.

**Yaml Configuration**:
```yaml
repository:
  release_track: sandbox
  release_tag: r1.1              # First release tag
  release_readiness: none        # Not ready for any release yet

apis:
  - api_name: example-api
    target_version: 0.1.0        # Planned first version
    api_status: draft            # Work in progress
```

---

## Recipe 1: The First Release (Alpha)
**Scenario**: You have a new API (`example-api`) and want to release an initial alpha version for feedback.

**Yaml Configuration**:
```yaml
repository:
  release_track: sandbox  # or meta-release
  release_tag: r1.1
  release_readiness: pre-release-alpha

apis:
  - api_name: example-api
    target_version: 0.1.0        # First version
    api_status: alpha            # Generates 0.1.0-alpha.1
```

---

## Recipe 2: Moving to Release Candidate
**Scenario**: Your alpha testing is complete. You want to freeze the API for final validation before the public launch.

**Yaml Configuration**:
```yaml
repository:
  release_track: sandbox
  release_tag: r1.2
  release_readiness: pre-release-rc

apis:
  - api_name: example-api
    target_version: 0.1.0        # Same base version
    api_status: rc               # Generates 0.1.0-rc.1
```

---

## Recipe 3: First Public Release
**Scenario**: Your Release Candidate (`rc.1` or `rc.2`) has passed all tests. You are ready to publish the official version.

**Yaml Configuration**:
```yaml
repository:
  release_track: sandbox
  release_tag: r1.3
  release_readiness: public-release

apis:
  - api_name: example-api
    target_version: 0.1.0        # Same base version
    api_status: public           # Generates 0.1.0 (Strictly)
```
> **Important**: This step requires that `0.1.0-rc.X` was previously released and validated.

---

## Recipe 4: Next Minor Release (Pre-1.0)
**Scenario**: You want to release the next minor version `0.2.0`. A new release cycle `r2` starts.

**Yaml Configuration**:
```yaml
repository:
  release_track: sandbox
  release_tag: r2.1
  release_readiness: pre-release-rc

apis:
  - api_name: example-api
    target_version: 0.2.0
    api_status: rc
```

---

## Recipe 5: First Stable Release (1.0.0)
**Scenario**: The API is mature. You are releasing the first stable public version `1.0.0`. This is part of release cycle `r3`.

**Yaml Configuration**:
```yaml
repository:
  release_track: sandbox
  release_tag: r3.3              # Assuming previous RCs (r3.1, r3.2)
  release_readiness: public-release

apis:
  - api_name: example-api
    target_version: 1.0.0
    api_status: public
```

---

## Recipe 6: A Major Update (Breaking Change)
**Scenario**: You are making breaking changes to an existing stable API (moving from `v1` to `v2` or `0.x` to `1.x`).

**Yaml Configuration**:
```yaml
repository:
  release_track: sandbox
  release_tag: r5.1              # New release tag (r5 for 2.0.0)
  release_readiness: pre-release-rc

apis:
  - api_name: example-api
    target_version: 2.0.0        # New Major version
    api_status: rc               # Start with RC for breaking changes
```

---

## Recipe 7: Maintenance Patch
**Scenario**: You found a bug in the released `1.1.0` version. You need to release `1.1.1` with a fix.
**Branch**: This edit happens on the **maintenance branch** (`maintenance-r4`), not `main`.

**Yaml Configuration**:
```yaml
repository:
  release_track: sandbox
  release_tag: r4.4              # Patch in r4 cycle
  release_readiness: patch-release

apis:
  - api_name: example-api
    target_version: 1.1.1        # Next patch version
    api_status: public           # Patches are usually public immediately
```

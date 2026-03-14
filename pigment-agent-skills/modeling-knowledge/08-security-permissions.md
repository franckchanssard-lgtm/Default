# Pigment Security & Permissions - Skill File

## Overview

Pigment security is built on Roles, Permissions, and Access Rights. Roles define what members can DO, while Access Rights define what data members can SEE.

## Core Security Concepts

### Three Pillars

1. **Roles**: Group of permissions assigned to members
2. **Permissions**: What actions a member can perform
3. **Access Rights**: What data a member can read/write

### Account Types for Security Management

Only these account types can manage security:
- **Primary Owner**: Full control
- **Security Admin**: Security management
- **Workspace Admin**: Workspace-level management

**Note**: Pigment Support cannot perform member management actions.

## Default Roles

### Admin Role
- All permissions enabled
- Full Application-level functions
- Can manage security settings

### Modeler Role
- Designed for Application builders
- All actions EXCEPT:
  - Security configuration
  - Block update history

### Reader Role
- View-only access to Boards
- **Write access: OFF**
- Can only read, not modify data

## Custom Roles

### Creating Custom Roles

1. Navigate to Role settings
2. Create new Role
3. Configure permissions
4. Set access rights
5. Assign to members

### Permission Categories

| Category | Examples |
|----------|----------|
| **Application** | Create, edit, delete Applications |
| **Blocks** | Create, edit, configure Blocks |
| **Boards** | Create, configure, share Boards |
| **Import/Export** | Data import, export permissions |
| **Security** | Manage roles, access rights |
| **Views** | Save public views, configure views |

## Access Rights

### Access States

| State | Description |
|-------|-------------|
| **Read & Write** | Full access |
| **Read Only** | View but not modify |
| **No Read / No Write** | No access (most restrictive) |

### Most Restrictive Rule Wins

When multiple access rights apply:
- The most restrictive setting takes precedence
- `No Read / No Write` overrides all other permissions
- This applies across all overlapping rules

### Access Rights Metrics

Create custom access rights using Metrics:

1. Create Metric with data type: **Access Rights**
2. Include **User List Dimension**
3. Add Dimension Lists for security scope
4. Define read/write permissions per combination

**Example Structure**:
```
Access_Rights_Metric
  Dimensions: User, Department, Region
  Values: Read & Write, Read Only, No Access
```

### User List Dimension

Essential for access rights configuration:
- Contains all workspace members
- Used in access rights Metrics
- Links roles to specific users

## Board Permissions

### Default Behavior

Board permissions inherit from Role Dimension via Users Role Metric.

### Board-Specific Permissions

Members with **Can configure** can restrict:
- Block Exploration access
- Export capabilities
- Other functionality

### Permission Levels

| Level | Capabilities |
|-------|-------------|
| **Can configure** | Full Board control |
| **Can comment** | View + comment |
| **Can open** | View only |

## Scenario Access Rights

### Controlling Scenario Access

Separate access rights for scenarios:
- Which scenarios members can view
- Which scenarios members can edit
- Scenario creation permissions

## Workspace vs Application Access

### Workspace Access

Managed by:
- Primary Owner
- Security Admin
- Workspace Admin

Grants access to the workspace itself.

### Application Access

Granted through Roles:
- Role assignment gives Application access
- Roles determine Block and Board access
- Different roles per Application possible

## SCIM Integration

### What is SCIM?

System for Cross-domain Identity Management - enables IT teams to manage access via identity provider.

### When SCIM is Enabled

- Member management moves to identity provider
- Cannot manually invite/deactivate in Pigment
- All provisioning through identity provider

### Benefits

- Centralized access management
- Automated onboarding/offboarding
- Compliance with IT policies
- SSO integration

## Security Best Practices

### 1. Principle of Least Privilege

Grant minimum permissions needed:
- Start with Reader role
- Add permissions as needed
- Regularly audit access

### 2. Role Design

- Create roles aligned with job functions
- Use descriptive role names
- Document role purposes
- Review roles periodically

### 3. Sensitive Data Protection

- Use Access Rights Metrics for sensitive data
- Restrict by dimension (department, region, etc.)
- Test access configurations before deploying

### 4. Audit and Monitoring

- Review member access regularly
- Check for unused accounts
- Monitor permission changes
- Document security decisions

### 5. Onboarding/Offboarding

- Use SCIM for automated provisioning
- Have clear processes for role assignment
- Promptly revoke access for departed members

## Common Patterns

### Department-Based Access

```
Access_Rights_By_Department
  Dimensions: User, Department
  Rule: User can only access their Department's data
```

### Regional Data Restriction

```
Access_Rights_By_Region
  Dimensions: User, Region
  Rule: Regional managers see only their region
```

### Time-Based Access

```
Access_Rights_By_Period
  Dimensions: User, Month
  Rule: Lock historical periods, allow current month edits
```

## Sources

- [Roles, Permissions and Access Rights](https://kb.pigment.com/docs/roles-permissions-access-rights)
- [Manage Pigment Roles](https://kb.pigment.com/docs/manage-pigment-roles)
- [Introduction to Access Rights](https://kb.pigment.com/docs/introduction-access-rights)
- [Access Rights Metrics and Rules](https://kb.pigment.com/docs/access-rights-metrics-rules)
- [Board Permissions](https://kb.pigment.com/docs/board-permissions-grant-board-access)
- [SCIM and Domain Restriction](https://kb.pigment.com/docs/manage-scim-domain-restriction)

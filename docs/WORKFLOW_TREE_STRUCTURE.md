# 🌳 GitHub Actions Workflow - Tree Structure

This document visualizes the complete CI/CD pipeline workflow with all branches and dependencies.

## Workflow Stages (Tree Branch Structure)

```
┌─────────────────────────────────────────────────────────────────┐
│                        PUSH TO MAIN                             │
│                     OR PULL REQUEST                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: VALIDATION & PREREQUISITES                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  🔐 validate-secrets                                      │  │
│  │  • Check all 28 required GitHub Secrets                  │  │
│  │  • Validate AWS credentials                              │  │
│  │  • Verify DynamoDB table names                           │  │
│  │  • Verify S3 bucket names                                │  │
│  │  • Verify Stripe & SMTP configuration                    │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
┌──────────────────────────┐  ┌──────────────────────────────────┐
│  STAGE 2: CODE QUALITY   │  │  STAGE 3: AWS TESTS              │
│  ┌────────────────────┐  │  │  ┌────────────────────────────┐  │
│  │ 🔍 lint-and-       │  │  │  │ ☁️ test-aws-                │  │
│  │    validate        │  │  │  │    infrastructure          │  │
│  │                    │  │  │  │                            │  │
│  │ • Lint Python code │  │  │  │ • Test S3 buckets          │  │
│  │ • Validate syntax  │  │  │  │ • Test DynamoDB tables     │  │
│  │ • Check imports    │  │  │  │ • Test Lambda function     │  │
│  │ • Validate HTML/JS │  │  │  │ • Test CloudFront dist     │  │
│  │ • Check CSS files  │  │  │  │ • Verify permissions       │  │
│  └────────────────────┘  │  │  └────────────────────────────┘  │
└────────────┬─────────────┘  └─────────────┬────────────────────┘
             │                              │
             └──────────────┬───────────────┘
                            │
                            ▼
                   ┌────────────────────┐
                   │  STAGE 4: TESTING  │
                   │  ┌──────────────┐  │
                   │  │ 🧪 test-     │  │
                   │  │    backend   │  │
                   │  │              │  │
                   │  │ • Unit tests │  │
                   │  │ • Import     │  │
                   │  │   tests      │  │
                   │  │ • Handler    │  │
                   │  │   validation │  │
                   │  └──────────────┘  │
                   └────────┬───────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  IF: push to main       │
              │  (skip on pull request) │
              └──────────┬──────────────┘
                         │
                ┌────────┴────────┐
                │                 │
                ▼                 ▼
┌─────────────────────┐  ┌─────────────────────┐
│  STAGE 5:           │  │  STAGE 6:           │
│  DEPLOY FRONTEND    │  │  DEPLOY BACKEND     │
│  ┌───────────────┐  │  │  ┌───────────────┐  │
│  │ 🌐 deploy-    │  │  │  │ ⚡ deploy-    │  │
│  │    frontend   │  │  │  │    backend    │  │
│  │               │  │  │  │               │  │
│  │ • S3 sync     │  │  │  │ • Package     │  │
│  │ • CloudFront  │  │  │  │   Lambda      │  │
│  │   update      │  │  │  │ • Deploy zip  │  │
│  │ • Cache       │  │  │  │ • Update env  │  │
│  │   invalidate  │  │  │  │ • Verify      │  │
│  └───────────────┘  │  │  └───────────────┘  │
└──────────┬──────────┘  └──────────┬──────────┘
           │                        │
           └────────┬───────────────┘
                    │
                    ▼
           ┌─────────────────┐
           │  STAGE 7:       │
           │  POST-DEPLOY    │
           │  ┌───────────┐  │
           │  │ ✅ test-  │  │
           │  │    deploy │  │
           │  │           │  │
           │  │ • Frontend│  │
           │  │   HTTP    │  │
           │  │ • Lambda  │  │
           │  │   invoke  │  │
           │  │ • Cloud-  │  │
           │  │   Front   │  │
           │  └───────────┘  │
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │  STAGE 8:       │
           │  SUMMARY        │
           │  ┌───────────┐  │
           │  │ 📊 deploy-│  │
           │  │    ment    │  │
           │  │    summary │  │
           │  │           │  │
           │  │ • Generate│  │
           │  │   report  │  │
           │  │ • Show    │  │
           │  │   status  │  │
           │  └───────────┘  │
           └─────────────────┘
                    │
                    ▼
           ┌─────────────────┐
           │  ✅ COMPLETE    │
           └─────────────────┘
```

## Workflow Stages Explained

### Stage 1: Validation & Prerequisites
**Job**: `validate-secrets`
- Runs **first**, blocks everything if fails
- Checks all 28 required GitHub Secrets
- Validates configuration completeness
- **Exit early** if any secret is missing

**Dependencies**: None  
**Runs on**: All events (push, pull request)

---

### Stage 2: Code Quality
**Job**: `lint-and-validate`
- Runs **after** secrets validation
- Lints Python code with flake8
- Validates Python syntax
- Tests critical imports
- Validates frontend structure (HTML, JS, CSS)

**Dependencies**: `validate-secrets`  
**Runs on**: All events

---

### Stage 3: AWS Infrastructure Tests
**Job**: `test-aws-infrastructure`
- Runs **in parallel** with Stage 2
- Tests S3 bucket accessibility
- Verifies DynamoDB tables exist
- Checks Lambda function status
- Validates CloudFront distribution

**Dependencies**: `validate-secrets`  
**Runs on**: All events

---

### Stage 4: Backend Testing
**Job**: `test-backend`
- Runs **after** Stages 2 & 3 complete
- Runs unit tests (if configured)
- Tests handler imports
- Validates all Lambda handlers load correctly

**Dependencies**: `validate-secrets`, `lint-and-validate`  
**Runs on**: All events

---

### Stage 5: Deploy Frontend
**Job**: `deploy-frontend`
- Runs **only on push to main**
- Waits for AWS tests & backend tests
- Syncs files to S3 with `--delete`
- Updates CloudFront function
- Invalidates cache

**Dependencies**: `test-aws-infrastructure`, `test-backend`  
**Runs on**: Push to main only (skipped on PR)

---

### Stage 6: Deploy Backend
**Job**: `deploy-backend`
- Runs **in parallel** with Stage 5
- Runs **only on push to main**
- Packages Lambda with dependencies
- Deploys to AWS Lambda
- Updates environment variables
- Verifies deployment

**Dependencies**: `test-aws-infrastructure`, `test-backend`  
**Runs on**: Push to main only (skipped on PR)

---

### Stage 7: Post-Deployment Tests
**Job**: `test-deployment`
- Runs **after** both deployments complete
- Tests frontend HTTP accessibility
- Invokes Lambda with test payload
- Verifies CloudFront status

**Dependencies**: `deploy-frontend`, `deploy-backend`  
**Runs on**: Push to main only

---

### Stage 8: Deployment Summary
**Job**: `deployment-summary`
- Runs **always** (even if previous steps fail)
- Generates comprehensive deployment report
- Shows status of all components
- Provides next steps

**Dependencies**: `deploy-frontend`, `deploy-backend`, `test-deployment`  
**Runs on**: Push to main only

---

## Job Dependencies Matrix

| Job | Depends On | Runs On | Can Fail? |
|-----|------------|---------|-----------|
| `validate-secrets` | None | All | ❌ Blocks all |
| `lint-and-validate` | `validate-secrets` | All | ❌ Blocks deploy |
| `test-aws-infrastructure` | `validate-secrets` | All | ❌ Blocks deploy |
| `test-backend` | `validate-secrets`, `lint-and-validate` | All | ❌ Blocks deploy |
| `deploy-frontend` | `test-aws-infrastructure`, `test-backend` | Main only | ⚠️ Rollback needed |
| `deploy-backend` | `test-aws-infrastructure`, `test-backend` | Main only | ⚠️ Rollback needed |
| `test-deployment` | `deploy-frontend`, `deploy-backend` | Main only | ⚠️ Manual fix |
| `deployment-summary` | All above | Main only | ✅ Always runs |

---

## Parallel Execution

The workflow maximizes speed through parallel execution:

```
Timeline:
0s  ├─ validate-secrets (30s)
    │
30s ├─┬─ lint-and-validate (60s)
    │ └─ test-aws-infrastructure (45s)
    │
90s ├─ test-backend (30s)
    │
120s├─┬─ deploy-frontend (90s)
     │ └─ deploy-backend (120s)
     │
240s├─ test-deployment (30s)
    │
270s└─ deployment-summary (10s)

Total: ~280 seconds (4.7 minutes)
```

---

## Failure Scenarios

### Scenario 1: Missing Secrets
```
validate-secrets ❌ FAIL
└─ All other jobs: SKIPPED
Result: No deployment, clear error message
```

### Scenario 2: Linting Error
```
validate-secrets ✅
lint-and-validate ❌ FAIL
test-aws-infrastructure ✅
└─ deploy-* : SKIPPED
Result: No deployment, fix code quality issues
```

### Scenario 3: AWS Infrastructure Missing
```
validate-secrets ✅
lint-and-validate ✅
test-aws-infrastructure ❌ FAIL (S3 bucket not found)
└─ deploy-* : SKIPPED
Result: No deployment, create missing AWS resources
```

### Scenario 4: Backend Tests Fail
```
validate-secrets ✅
lint-and-validate ✅
test-aws-infrastructure ✅
test-backend ❌ FAIL
└─ deploy-* : SKIPPED
Result: No deployment, fix failing tests
```

### Scenario 5: Deployment Success, Post-Test Fail
```
All tests pass ✅
deploy-frontend ✅
deploy-backend ✅
test-deployment ❌ FAIL (Lambda returns error)
└─ deployment-summary: Runs with warning
Result: Deployed but needs manual verification
```

---

## Pull Request vs Push to Main

### On Pull Request:
- ✅ Runs: Validation, linting, tests
- ❌ Skips: All deployment steps
- 📊 Result: Code quality verification only

### On Push to Main:
- ✅ Runs: Everything
- 🚀 Deploys: Frontend & Backend
- ✅ Tests: Post-deployment verification
- 📊 Result: Full deployment with testing

---

## Monitoring Workflow

### View Live Progress:
```
https://github.com/YOUR_USERNAME/galerly/actions
```

### Check Specific Job:
1. Click on workflow run
2. Click on job name (e.g., "Deploy Frontend")
3. Expand steps to see detailed logs

### Debugging Failed Jobs:
1. Identify which stage failed
2. Click on failed job
3. Review error output
4. Fix issue in code
5. Push again to retry

---

## Workflow Optimization

The workflow is optimized for:

1. **Speed**: Parallel execution where possible
2. **Safety**: Multiple validation stages
3. **Clarity**: Clear stage names and outputs
4. **Reliability**: Comprehensive error checking
5. **Auditability**: Detailed logs at each step

---

**This tree structure ensures no deployment happens unless all validations pass!** 🌳✅


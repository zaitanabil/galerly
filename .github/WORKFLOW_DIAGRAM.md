# CI/CD Pipeline - Visual Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TRIGGER: Push to main                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: BUILD                                                               │
│  ┌─────────────────────────┐    ┌──────────────────────────┐               │
│  │ Build Frontend          │    │ Package Lambda           │               │
│  │ - npm ci                │    │ - pip install deps       │               │
│  │ - npm run build         │    │ - zip function code      │               │
│  │ - Upload artifact       │    │ - Upload artifact        │               │
│  └─────────────────────────┘    └──────────────────────────┘               │
│          │                                   │                               │
│          └───────────────┬───────────────────┘                               │
└──────────────────────────┼─────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: UNIT TESTS                                                          │
│  ┌─────────────────────────┐    ┌──────────────────────────┐               │
│  │ Backend Tests           │    │ Frontend Tests           │               │
│  │ - pytest tests/ -v      │    │ - npm test               │               │
│  │ - 661 passing           │    │ - Upload results         │               │
│  └─────────────────────────┘    └──────────────────────────┘               │
│          │                                   │                               │
│          └───────────────┬───────────────────┘                               │
└──────────────────────────┼─────────────────────────────────────────────────┘
                           ▼
                  ┌────────────────┐
                  │ Tests Passed?  │
                  └────────┬───────┘
                           │ YES (main branch only)
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: DEPLOY PRODUCTION                                                   │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │ 1. Configure AWS credentials                                     │       │
│  │ 2. Backup current Lambda version → Store version number          │       │
│  │ 3. Download build artifacts                                      │       │
│  │ 4. Deploy frontend to S3                                         │       │
│  │ 5. Invalidate CloudFront cache                                   │       │
│  │ 6. Deploy Lambda function (publish new version)                  │       │
│  │ 7. Wait for Lambda to be ready                                   │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│          │                                                                    │
│          │ Outputs: lambda-version, previous-lambda-version                  │
└──────────┼────────────────────────────────────────────────────────────────┘
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 4: POST-DEPLOYMENT TESTS (Run in Parallel)                            │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │ 4.i Integration     │  │ 4.ii Verification   │  │ 4.iii Smoke Tests   │ │
│  │ Tests               │  │ Tests               │  │                     │ │
│  │ ─────────────────── │  │ ─────────────────── │  │ ─────────────────── │ │
│  │ • API endpoints     │  │ • Lambda invoke     │  │ • Frontend HTTP 200 │ │
│  │ • Database ops      │  │ • S3 deployment     │  │ • API health 200    │ │
│  │ • Auth flows        │  │ • CloudFront status │  │ • Lambda invoke OK  │ │
│  │ • Full workflows    │  │ • API Gateway       │  │ • Quick pass/fail   │ │
│  └──────────┬──────────┘  └──────────┬──────────┘  └──────────┬──────────┘ │
│             │                        │                        │             │
│             └────────────┬───────────┴───────────┬────────────┘             │
└──────────────────────────┼─────────────────────────────────────────────────┘
                           ▼
                  ┌────────────────┐
                  │ All Tests      │
                  │ Passed?        │
                  └────┬───────┬───┘
                       │       │
                   YES │       │ NO
                       │       │
                       ▼       ▼
         ┌──────────────┐  ┌─────────────────────────────────────────────────┐
         │ ✅ SUCCESS   │  │  STEP 5: AUTOMATIC ROLLBACK                     │
         │ Deployment   │  │  ┌───────────────────────────────────────────┐  │
         │ Complete     │  │  │ 1. Rollback Lambda to previous version    │  │
         └──────────────┘  │  │ 2. Update function configuration          │  │
                           │  │ 3. Create GitHub issue with details       │  │
                           │  │ 4. Notify team                            │  │
                           │  └───────────────────────────────────────────┘  │
                           │                                                  │
                           │  ❌ ROLLBACK COMPLETE                            │
                           │  • Previous version restored                     │
                           │  • Issue created for investigation               │
                           └──────────────────────────────────────────────────┘
```

## Workflow Jobs Summary

| Step | Job Name | Purpose | Runs On |
|------|----------|---------|---------|
| 1 | `build` | Build frontend and package Lambda | Every push |
| 2 | `unit-tests` | Run backend and frontend unit tests | Every push |
| 3 | `deploy-production` | Deploy to AWS (S3 + Lambda) | Only `main` branch |
| 4.i | `integration-tests` | Test API and workflows | After deploy (parallel) |
| 4.ii | `verification-tests` | Verify AWS resources | After deploy (parallel) |
| 4.iii | `smoke-tests` | Quick health checks | After deploy (parallel) |
| 5 | `rollback` | Rollback on test failure | If Step 4 fails |

## Job Dependencies

```
build
  └─> unit-tests
        └─> deploy-production (if main branch)
              ├─> integration-tests ─┐
              ├─> verification-tests ─┼─> rollback (if any fail)
              └─> smoke-tests ────────┘
```

## Rollback Trigger Conditions

The rollback job runs when:
- `always()` - Job always evaluates
- AND `github.ref == 'refs/heads/main'` - Only on main branch
- AND one of:
  - `integration-tests.result == 'failure'`
  - `verification-tests.result == 'failure'`  
  - `smoke-tests.result == 'failure'`

## Artifacts Created

| Artifact | Retention | Purpose |
|----------|-----------|---------|
| `frontend-dist-{SHA}` | 7 days | Built frontend for deployment |
| `lambda-package-{SHA}` | 7 days | Packaged Lambda for deployment |
| `test-results-{SHA}` | 30 days | Unit test results for analysis |
| `integration-results-{SHA}` | 30 days | Integration test results |

## Environment Variables

All 125 environment variables are automatically injected from:
- GitHub Secrets (7): `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `JWT_SECRET`, etc.
- GitHub Variables (118): All configuration values

## Monitoring Deployment

View workflow runs:
```bash
gh run list --limit 10
gh run watch
```

View specific job logs:
```bash
gh run view <RUN_ID> --log
gh run view <RUN_ID> --log-failed
```

## Success Criteria

✅ **Unit Tests**: All tests pass (or continue-on-error)  
✅ **Build**: Artifacts created successfully  
✅ **Deploy**: Lambda and S3 updated  
✅ **Integration**: API workflows function correctly  
✅ **Verification**: AWS resources healthy  
✅ **Smoke**: Basic functionality working  

If ANY Step 4 test fails → Automatic rollback to previous Lambda version.

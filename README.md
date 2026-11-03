# DevOps Activity 3A – Secure CI/CD Pipeline for a FastAPI Application

## 1. Project Overview

DevOps Activity 3A demonstrates the development, containerization, security validation, and automated deployment of a FastAPI application using a secure CI/CD pipeline.

The project integrates automated code quality checks, Python security analysis, dependency auditing, secret detection, Docker image scanning, Infrastructure as Code (IaC), and deployment to Google Cloud Run.

GitHub Actions orchestrates the pipeline, while Google Cloud Workload Identity Federation (WIF) provides keyless authentication.

### Key Features

- FastAPI REST API with inventory CRUD operations.
- Automated testing using pytest and coverage reporting.
- Multi-stage Docker build with a non-root runtime user.
- Terraform-managed Google Cloud infrastructure.
- Google Artifact Registry for container image storage.
- Google Cloud Run deployment.
- GitHub Actions CI/CD automation.
- Automated security scanning and vulnerability gates.
- Cloud Run health checks and automatic traffic rollback.
- OWASP ZAP baseline security scanning with downloadable reports.

## 2. Technology Stack

| Category | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Database | SQLite, SQLAlchemy |
| Testing | pytest, pytest-cov |
| Code Quality | Ruff |
| Python Security | Bandit, pip-audit |
| Secret Detection | Gitleaks |
| Containerization | Docker |
| Dockerfile Security | Hadolint |
| Container Scanning | Trivy |
| Infrastructure as Code | Terraform |
| Cloud Platform | Google Cloud Platform |
| Container Registry | Artifact Registry |
| Deployment | Cloud Run |
| CI/CD | GitHub Actions |
| Web Security | OWASP ZAP |
| State Management | Google Cloud Storage |

## 3. Application Architecture

The application follows this deployment flow:

1. Developer pushes code to the GitHub repository.
2. GitHub Actions executes quality, testing, and security checks.
3. Docker builds the application image.
4. Trivy scans the container image.
5. GitHub Actions authenticates to Google Cloud using Workload Identity Federation.
6. The image is pushed to Google Artifact Registry.
7. Terraform manages the infrastructure configuration.
8. A new Cloud Run revision is deployed without receiving production traffic.
9. The pipeline executes a health-check smoke test.
10. Successful revisions receive 100% traffic.
11. Failed health checks trigger automatic traffic rollback.
12. OWASP ZAP performs a baseline scan and publishes HTML and JSON reports.

## 4. Project Structure

```text
devops-activity-3a/
│
├── app/
│   ├── __init__.py
│   └── main.py
│
├── tests/
│   └── test_main.py
│
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── versions.tf
│   └── envs/
│       └── dev/
│           └── backend.hcl
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── Dockerfile
├── .dockerignore
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

## 5. FastAPI Application

The backend implements an inventory management REST API.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Application health check |
| POST | `/items` | Create an inventory item |
| GET | `/items` | Retrieve inventory items |
| GET | `/items/{item_id}` | Retrieve an individual item |
| PUT | `/items/{item_id}` | Update an inventory item |
| DELETE | `/items/{item_id}` | Delete an inventory item |

### Local Execution

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements-dev.txt
```

Start the application:

```bash
uvicorn app.main:app --reload
```

Access the application:

- API: http://127.0.0.1:8000
- Swagger documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## 6. Automated Testing and Code Quality

The project uses pytest for automated application testing.

The test suite contains seven test cases covering:

- Health endpoint.
- Item creation.
- Item listing.
- Missing item retrieval.
- Item updates.
- Item deletion.
- Negative quantity validation.

Execute the test suite:

```bash
python -m pytest tests --cov=app --cov-branch --cov-report=term-missing
```

The locally verified result was:

- Tests passed: 7
- Code coverage: 90.48%

Ruff checks Python code quality and formatting-related lint rules.

```bash
python -m ruff check app tests
```

## 7. Docker Containerization

The application uses a multi-stage Dockerfile.

### Docker implementation

- Python 3.13 slim base image.
- Separate builder and runtime stages.
- Dependencies installed in a virtual environment.
- Reduced runtime image contents.
- OS package upgrades during image construction.
- Dedicated non-root application user.
- Container listens on port 8080.

Build the image:

```bash
docker build -t activity-3a-api .
```

Run the container:

```bash
docker run --rm -p 8080:8080 activity-3a-api
```

Verify:

```bash
curl http://localhost:8080/health
```

## 8. Terraform Infrastructure

Terraform provisions and manages the Google Cloud deployment resources.

### Infrastructure Components

**Artifact Registry**

- Repository: `activity-3a-images`
- Region: `asia-south1`
- Format: Docker

**Cloud Run**

- Service: `activity-3a-api`
- Region: `asia-south1`
- Container port: 8080
- CPU allocation limit: 1 vCPU
- Memory limit: 512 MiB
- Minimum instances: 0
- Maximum instances: 2
- Deletion protection: enabled

**Runtime Identity**

A dedicated service account is configured for the Cloud Run application.

**Terraform Remote State**

Terraform state is stored in Google Cloud Storage:

```hcl
bucket = "lunar-works-316500-tfstate"
prefix = "activity-3a/dev"
```

### Terraform Commands

Initialize:

```bash
terraform -chdir=terraform init \
  -backend-config="envs/dev/backend.hcl"
```

Validate:

```bash
terraform -chdir=terraform validate
```

Review changes:

```bash
terraform -chdir=terraform plan
```

Apply approved infrastructure changes:

```bash
terraform -chdir=terraform apply
```

## 9. GitHub Actions CI/CD Pipeline

The pipeline is defined in:

`.github/workflows/ci.yml`

It runs on pushes to the main branch, pull requests targeting main, and manual workflow dispatch.

### Job 1: Python Quality and Security

- Installs application and development dependencies.
- Executes Ruff lint checks.
- Runs pytest with branch coverage.
- Uploads the coverage report.
- Performs Bandit security analysis.
- Audits dependencies using pip-audit.

### Job 2: Secret Detection

Gitleaks scans the repository history and source files for accidentally committed credentials and secrets.

### Job 3: Dockerfile and Container Security

- Validates Dockerfile instructions using Hadolint.
- Builds the Docker image.
- Performs a full Trivy vulnerability scan.
- Uploads the full vulnerability report.
- Enforces an actionable OS vulnerability gate for HIGH and CRITICAL findings with available fixes.

### Job 4: Deploy to Google Cloud Run

Deployment occurs only after the three validation jobs succeed.

Authentication uses Google Cloud Workload Identity Federation rather than a long-lived service-account JSON key.

The pipeline:

1. Authenticates to Google Cloud.
2. Builds and pushes the commit-specific image.
3. Captures the previous Cloud Run revision.
4. Deploys the new revision without production traffic.
5. Executes the `/health` smoke test.
6. Routes 100% traffic to the new revision when healthy.
7. Restores traffic to the previous revision if the smoke test fails.

### Job 5: OWASP ZAP Baseline Scan

After deployment, OWASP ZAP scans the Cloud Run Swagger documentation endpoint.

The scan generates:

- `zap-baseline-report.html`
- `zap-baseline-report.json`

Both reports are uploaded as the `zap-baseline-reports` GitHub Actions artifact.

## 10. Security Implementation

| Security Tool | Purpose |
|---|---|
| Ruff | Code quality validation |
| Bandit | Python security analysis |
| pip-audit | Dependency vulnerability auditing |
| Gitleaks | Secret detection |
| Hadolint | Dockerfile validation |
| Trivy | Container vulnerability scanning |
| OWASP ZAP | Web application baseline scanning |

The pipeline uses security gates to prevent deployment when mandatory checks fail.

## 11. OWASP ZAP Scan Results

The successful GitHub Actions baseline scan reported:

| Result | Count |
|---|---:|
| PASS | 57 |
| WARN-NEW | 11 |
| FAIL-NEW | 0 |
| FAIL-INPROG | 0 |
| WARN-INPROG | 0 |
| INFO | 0 |
| IGNORE | 0 |

The scan identified recommendations involving:

- Content Security Policy.
- Anti-clickjacking headers.
- X-Content-Type-Options.
- HTTP Strict Transport Security.
- Cache-control directives.
- Subresource Integrity.
- Permissions Policy.
- Cross-Origin Embedder Policy.

These findings should be reviewed and addressed according to the application's deployment requirements.

The successful baseline scan does not mean that every security recommendation has been remediated.

## 12. Deployment Information

**Google Cloud Project:** `lunar-works-316500`

**Region:** `asia-south1`

**Artifact Registry:**

`asia-south1-docker.pkg.dev/lunar-works-316500/activity-3a-images`

**Cloud Run Service:**

`activity-3a-api`

**Deployed Application:**

https://activity-3a-api-avbr4zsxia-el.a.run.app

**API Documentation:**

https://activity-3a-api-avbr4zsxia-el.a.run.app/docs

**Health Endpoint:**

https://activity-3a-api-avbr4zsxia-el.a.run.app/health

## 13. Pipeline Execution Evidence

The final successful GitHub Actions execution verified the following jobs:

- Python Quality and Security.
- Secret Detection.
- Dockerfile and Container Security.
- Deploy to Google Cloud Run.
- OWASP ZAP Baseline Scan.

The successful execution also produced downloadable CI/CD artifacts, including the ZAP baseline reports.

The project should additionally retain evidence of the deliberately blocked security pipeline execution and the corrected successful execution.

## 14. Important Limitations and Future Improvements

### Current limitations

1. SQLite uses `/tmp/inventory.db` in Cloud Run. This filesystem is ephemeral, so application data should not be treated as persistent across instance replacement or restart.
2. The Cloud Run service currently allows public invocation.
3. ZAP identified security-header recommendations that require further assessment.
4. The full Trivy report is uploaded without blocking the pipeline; the separate actionable OS scan is the enforced container vulnerability gate.

### Future improvements

- Migrate SQLite to Cloud SQL PostgreSQL.
- Implement authentication and authorization.
- Restrict public service access where appropriate.
- Configure security headers and review ZAP findings.
- Pin third-party GitHub Actions to verified immutable commit SHAs.
- Add application monitoring, structured logging and alerting.
- Introduce stronger container image provenance and software supply-chain controls.

## 15. Conclusion

DevOps Activity 3A demonstrates an automated and security-focused software delivery workflow.

The project integrates FastAPI application development, automated testing, Docker containerization, Terraform infrastructure management, Google Cloud deployment, keyless authentication, security scanning, deployment health verification, automatic rollback, and OWASP ZAP reporting.

The completed pipeline demonstrates how application quality, infrastructure automation, deployment reliability, and security validation can be incorporated into a repeatable CI/CD process.

---

**Project Repository:**  
https://github.com/rahul010699-design/devops-activity-3a

**Cloud Deployment:**  
https://activity-3a-api-avbr4zsxia-el.a.run.app
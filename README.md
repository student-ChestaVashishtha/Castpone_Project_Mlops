# 🚀 End-to-End MLOps Capstone Project (DVC + MLflow + AWS + EKS)

## 📌 Project Overview

This project demonstrates a **production-grade MLOps pipeline** covering experiment tracking, data versioning, CI/CD, Dockerization, Kubernetes (EKS) deployment, and monitoring using Prometheus & Grafana.

---

## 🗂 Project Setup & Repository Structure

### 1️⃣ Repository & Environment Setup

```bash
git clone <repo-url>
cd <repo-name>
conda create -n atlas python=3.10
conda activate atlas
pip install cookiecutter
cookiecutter -c v1 https://github.com/drivendata/cookiecutter-data-science
```

Rename:

```
src/models → src/model
```

Commit changes:

```bash
git add .
git commit -m "Initial project structure"
git push
```

---

## 📊 MLflow Experiment Tracking (DAGsHub)

### 2️⃣ DAGsHub Integration

1. Go to [https://dagshub.com/dashboard](https://dagshub.com/dashboard)
2. Create → New Repo → Connect GitHub Repo
3. Copy **MLflow Tracking URI & credentials**
4. Install dependencies:

```bash
pip install dagshub mlflow
```

5. Run experiment notebooks
6. Commit results:

```bash
git add .
git commit -m "MLflow experiments"
git push
```

---

## 📦 Data Versioning with DVC

### 3️⃣ Initialize DVC

```bash
dvc init
mkdir local_s3
dvc remote add -d mylocal local_s3
```

### 4️⃣ Pipeline Components

Add the following inside `src/`:

* logger/
* data_ingestion.py
* data_preprocessing.py
* feature_engineering.py
* model_building.py
* model_evaluation.py
* register_model.py

Create:

* `dvc.yaml` (till model evaluation metrics)
* `params.yaml`

Run pipeline:

```bash
dvc repro
dvc status
```

Commit:

```bash
git add .
git commit -m "DVC pipeline setup"
git push
```

---

## ☁️ AWS S3 as DVC Remote

### 5️⃣ AWS Setup

1. Create IAM User & S3 Bucket
2. Install:

```bash
pip install dvc[s3] awscli
aws configure
```

3. Add S3 remote:

```bash
dvc remote add -d myremote s3://<bucket-name>
dvc push
```

---

## 🌐 Flask Application

### 6️⃣ Flask App Setup

```bash
mkdir flask_app
pip install flask
```

Run locally:

```bash
python app.py
```

Freeze dependencies:

```bash
pip freeze > requirements.txt
```

---

## 🔁 CI/CD with GitHub Actions & DAGsHub

### 7️⃣ CI Setup

* Create `.github/workflows/ci.yaml`
* Add folders:

```
tests/
scripts/
```

### DAGsHub Token

1. Generate token from DAGsHub
2. Add token to **GitHub Secrets**

```env
CAPSTONE_TEST=<dagshub-token>
```

---

## 🐳 Dockerization

### 8️⃣ Docker Build & Run

```bash
pip install pipreqs
cd flask_app
pipreqs . --force
```

Build image:

```bash
docker build -t capstone-app:latest .
```

Run:

```bash
docker run -p 8888:5000 -e CAPSTONE_TEST=<token> capstone-app:latest
```

---

## ☁️ AWS ECR & CI/CD

### 9️⃣ AWS Secrets (GitHub)

Add:

* AWS_ACCESS_KEY_ID
* AWS_SECRET_ACCESS_KEY
* AWS_REGION
* AWS_ACCOUNT_ID
* ECR_REPOSITORY

Attach IAM Policy:

```
AmazonEC2ContainerRegistryFullAccess
```

CI/CD builds & pushes image to ECR.

---

## ☸ Kubernetes (EKS) Deployment

### 🔧 Prerequisites

Verify tools:

```bash
aws --version
kubectl version --client
eksctl version
```

### 🔹 Create EKS Cluster

```bash
eksctl create cluster \
--name flask-app-cluster \
--region us-east-1 \
--nodegroup-name flask-app-nodes \
--node-type t3.small \
--nodes 1 --managed
```

Update kubeconfig:

```bash
aws eks update-kubeconfig --name flask-app-cluster --region us-east-1
```

Verify:

```bash
kubectl get nodes
kubectl get pods
kubectl get svc
```

---

## 🌍 Application Access

```bash
kubectl get svc flask-app-service
curl http://<external-ip>:5000
```

---

## 📈 Monitoring with Prometheus

### 🔹 Prometheus Setup (EC2)

* Instance: t3.medium
* Ports: 9090, 22

Edit config:

```yaml
scrape_configs:
  - job_name: "flask-app"
    static_configs:
      - targets: ["<external-ip>:5000"]
```

Run:

```bash
/usr/local/bin/prometheus --config.file=/etc/prometheus/prometheus.yml
```

---

## 📊 Grafana Setup

* Instance: t3.medium
* Port: 3000

Install & start:

```bash
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

Add Prometheus datasource:

```
http://<prometheus-ip>:9090
```

---

## 🧹 AWS Resource Cleanup

```bash
kubectl delete deployment flask-app
kubectl delete service flask-app-service
kubectl delete secret capstone-secret
eksctl delete cluster --name flask-app-cluster --region us-east-1
```

(Optional)

* Delete S3 bucket
* Delete ECR repo
* Verify CloudFormation stack deletion

### I deleted my deployed link because of aws charges but this is video proof of it : https://drive.google.com/file/d/1PGAkGSD6g0u0IVQTug4UULZ54e2bISRP/view?usp=sharing
---


## 🚧 Challenges Faced & Key Learnings

### 1️⃣ EKS Cluster Deployment Failure (IAM Permissions)

**Challenge:**
While creating the EKS cluster using `eksctl`, node group creation failed due to **missing IAM permissions**, specifically related to EC2 Fleet Requests and ECR access.

**Root Cause:**
The IAM user lacked required policies such as:

* `AmazonEKSClusterPolicy`
* `AmazonEKSWorkerNodePolicy`
* `AmazonEC2ContainerRegistryFullAccess`

**Solution:**

* Attached the missing IAM policies to the user/role
* Verified permissions using AWS IAM console
* Recreated the cluster successfully after fixing access issues

**Learning:**
EKS heavily relies on IAM roles and CloudFormation stacks. Even a single missing permission can silently block cluster provisioning.

---

### 2️⃣ MLflow Model Logging Failure

**Challenge:**
MLflow experiments were tracked successfully, but **model logging failed**, especially when running inside notebooks and Docker containers.

**Root Cause:**

* Incorrect MLflow tracking URI
* Missing DAGsHub authentication token in environment variables
* Model logging attempted without proper artifact storage configuration

**Solution:**

* Explicitly set the MLflow tracking URI and credentials
* Passed DAGsHub token as an environment variable (`CAPSTONE_TEST`)
* Switched MLflow configuration to parameter-based setup for Docker compatibility

**Learning:**
MLflow requires consistent tracking configuration across local, CI, and containerized environments to log artifacts reliably.

---

### 3️⃣ Docker Container Failure Due to Dependency Version Mismatch

**Challenge:**
The Flask application container failed at runtime due to **Python package version mismatches** between the local development environment and the Docker image.

**Root Cause:**

* Dependencies were installed manually during development
* Docker image used a different base Python version
* Inconsistent versions of ML libraries (e.g., `mlflow`, `scikit-learn`, `pandas`) caused import and runtime errors

**Solution:**

* Generated dependencies directly from the application code using `pipreqs`
* Ensured consistent Python version across local, CI, and Docker environments
* Rebuilt the Docker image with aligned dependency versions

**Learning:**
Dependency mismatches are a common failure point in containerized ML systems; reproducible builds require strict version alignment across environments.

---

### 4️⃣ CI/CD Failures Due to Missing Secrets

**Challenge:**
GitHub Actions pipeline failed during Docker build and ECR push stages.

**Solution:**

* Added AWS credentials and DAGsHub token to GitHub Secrets
* Verified environment variables inside CI logs

**Learning:**
CI/CD pipelines are highly sensitive to missing secrets; validating secrets early avoids long debug cycles.

---

## ✅ Final Outcome

✔ Reproducible ML pipeline
✔ Versioned data & models
✔ CI/CD automation
✔ Scalable Kubernetes deployment
✔ Real-time monitoring



# 🚀 AIOps Guardian
### Enterprise AI Root Cause Investigation & Incident Response Platform

> An Agentic AI platform that automatically investigates production incidents by analyzing logs, metrics, deployments, infrastructure, and application health to identify the most likely root cause and recommend remediation actions.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20AI-purple)
![Docker](https://img.shields.io/badge/Docker-Containers-blue)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Orchestration-326CE5)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

# 📖 Overview

Modern production systems generate massive amounts of logs, metrics, events, and alerts.

When an application goes down, engineers spend valuable time manually investigating:

- Linux logs
- Docker logs
- Kubernetes events
- CPU & Memory usage
- Network health
- Database connectivity
- Recent deployments
- Application logs

AIOps Guardian automates this investigation using multiple specialized AI agents that collaborate to determine the most likely root cause of production failures.

Instead of manually checking dozens of dashboards, engineers receive an AI-generated investigation report within seconds.

---

# 🎯 Problem Statement

Traditional incident investigation requires engineers to manually inspect multiple systems before identifying the actual issue.

Typical investigation includes:

✔ Linux Logs

✔ Windows Event Viewer

✔ Docker Containers

✔ Kubernetes Pods

✔ Application Logs

✔ Database Health

✔ CPU & Memory Usage

✔ Network Connectivity

✔ Recent Deployments

✔ Infrastructure Metrics

This process often takes **30–90 minutes**.

AIOps Guardian reduces this to a few seconds by automating the investigation process.

---

# 🚀 Features

## 🤖 Agentic AI Investigation

- Multi-Agent Architecture
- Autonomous Incident Investigation
- Root Cause Reasoning
- Evidence Collection
- Confidence Scoring
- Recommendation Engine

---

## 📊 Infrastructure Monitoring

- CPU Monitoring
- Memory Monitoring
- Disk Usage
- Network Health
- Process Monitoring
- Service Health

---

## 🐳 Docker Monitoring

- Container Status
- Container Logs
- Restart Detection
- Container Health
- Resource Usage

---

## ☸ Kubernetes Investigation

- Pod Health
- CrashLoopBackOff Detection
- Failed Deployments
- Replica Issues
- Node Status
- Events Analysis

---

## 🖥 Linux Investigation

- journalctl Analysis
- syslog Analysis
- Authentication Logs
- Kernel Logs
- Service Logs

---

## 🪟 Windows Investigation

- Event Viewer Analysis
- Windows Services
- Security Logs
- Application Logs

---

## 📈 Observability

- Prometheus Metrics
- Grafana Dashboards
- Loki Logs
- Alert Correlation

---

## 📚 AI Knowledge Base

- Runbooks
- SOP Documents
- Incident History
- Troubleshooting Guides
- Company Documentation

(RAG Powered)

---

## 📑 Incident Report Generation

Automatically generates:

- Incident Summary
- Timeline
- Root Cause
- Supporting Evidence
- Confidence Score
- Recommended Actions

---

# 🧠 Multi-Agent Architecture

```

                    Coordinator Agent
                           │
      ┌────────────────────┼────────────────────┐
      │                    │                    │
 Linux Agent         Metrics Agent      Deployment Agent
      │                    │                    │
 Docker Agent        Kubernetes Agent     Network Agent
      │                    │                    │
 Database Agent      Log Analysis Agent   RAG Agent
      └────────────────────┼────────────────────┘
                           │
                   Root Cause Agent
                           │
                   Incident Report Agent

```

---

# ⚙ Investigation Workflow

```

Alert Triggered

↓

Coordinator Agent

↓

Collect Infrastructure Data

↓

Collect Logs

↓

Collect Metrics

↓

Collect Deployment History

↓

Analyze Incident

↓

Correlate Evidence

↓

Generate Root Cause

↓

Recommend Fix

↓

Generate Incident Report

```

---

# 🔍 AI Investigation Sources

The platform analyzes data from multiple sources.

## Infrastructure

- CPU
- Memory
- Disk
- Network
- Services

## Linux

- journalctl
- syslog
- auth.log

## Windows

- Event Viewer
- Application Logs
- Security Logs

## Docker

- Container Logs
- Container Status
- Restart Count

## Kubernetes

- Pod Events
- Pod Logs
- Node Health
- Replica Status
- Deployments

## Databases

- PostgreSQL
- MySQL
- MongoDB

## CI/CD

- GitHub Actions
- Jenkins
- GitLab CI

---

# 🧩 Example Investigation

## Alert

```

Website Down

```

AI Investigation

```

CPU ✔ Normal

Memory ✔ Normal

Disk ✔ Normal

Network ✔ Healthy

Docker ✔ Running

Kubernetes ❌ CrashLoopBackOff

Deployment ❌ Failed

Application Log

Database Connection Timeout

```

AI Conclusion

```

Root Cause

Incorrect database credentials were introduced during
the latest deployment.

Confidence

94%

Recommendation

Rollback deployment or update database credentials.

```

---

# 🛠 Tech Stack

## AI

- LangGraph
- LangChain
- Ollama
- Llama 3
- Qwen
- Gemma

---

## Backend

- FastAPI
- Python
- Redis
- PostgreSQL

---

## AI Memory

- ChromaDB

---

## Infrastructure

- Docker
- Kubernetes
- Minikube

---

## Monitoring

- Prometheus
- Grafana
- Loki
- Node Exporter

---

## Frontend

- Next.js
- React
- TailwindCSS

---

# 📂 Project Structure

```

AIOps-Guardian/

│

├── agents/

│ ├── coordinator/

│ ├── linux/

│ ├── windows/

│ ├── docker/

│ ├── kubernetes/

│ ├── deployment/

│ ├── network/

│ ├── metrics/

│ ├── database/

│ └── rootcause/

│

├── backend/

├── frontend/

├── rag/

├── monitoring/

├── docker/

├── kubernetes/

├── reports/

├── database/

├── docs/

└── tests/

```

---

# 📊 Dashboard

The platform provides:

- Live Infrastructure Monitoring
- Incident Timeline
- Root Cause Analysis
- Container Status
- Kubernetes Health
- AI Recommendations
- Historical Incidents
- AI Chat Assistant

---

# 💬 Natural Language Queries

Examples:

```

Why is my API down?

```

```

Show failed deployments.

```

```

Why did Kubernetes restart my pod?

```

```

Analyze yesterday's outage.

```

```

Generate incident report.

```

```

Show high CPU servers.

```

---

# 🎯 Future Enhancements

- BeyondTrust PAM Integration
- Active Directory Integration
- AWS CloudWatch
- Azure Monitor
- GCP Monitoring
- ServiceNow Integration
- Slack Notifications
- Microsoft Teams Integration
- Automatic Rollback Suggestions
- Predictive Incident Detection
- AI Auto Remediation
- Multi-Cloud Support

---

# 📈 Skills Demonstrated

- Agentic AI
- Multi-Agent Systems
- LangGraph
- RAG
- DevOps
- SRE
- Kubernetes
- Docker
- Observability
- Monitoring
- Root Cause Analysis
- Incident Response
- FastAPI
- PostgreSQL
- Redis
- Prometheus
- Grafana
- CI/CD
- Python

---

# 🌟 Why This Project?

This project demonstrates how Agentic AI can enhance modern Site Reliability Engineering (SRE) and DevOps workflows by automating production incident investigations, reducing Mean Time to Detect (MTTD), and Mean Time to Resolve (MTTR).

Instead of replacing engineers, AIOps Guardian acts as an intelligent investigation assistant that collects evidence, correlates data from multiple systems, and provides explainable root cause analysis with actionable recommendations.

---

# 📄 License

MIT License

---

## ⭐ If you find this project useful, consider giving it a star!
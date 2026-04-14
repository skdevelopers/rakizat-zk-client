
---

# 2) README.md for Python repo

## `README.md`

```md
# Rakizat ZK Client

Production-ready Python attendance sync client for **ZKTeco biometric devices** such as **MB2000** and **UFace800**.

This service is built to work with **Rakizat AI HRMS** and is responsible for securely polling devices, preserving raw attempts, normalizing valid attendance events, and sending them to the Laravel API.

## Author

**Salman**  
Senior AI & DevOps Engineer  
SK Developers

Experienced in:
- Laravel
- PHP
- Python
- DevOps
- FastAPI
- Node.js
- AI system architecture
- biometric attendance systems
- cloud and server deployment
- scalable enterprise application design

---

## Project Overview

**Rakizat ZK Client** is a dedicated edge-side attendance collector.

It is intentionally separated from the Laravel application so that device communication remains:

- isolated
- fault tolerant
- retry-safe
- easy to deploy near devices
- resilient against temporary API or network failure

---

## Create initial Python repo structure

cd ~/projects
mkdir -p rakizat-zk-client/{core,network,services,storage,tools}
cd rakizat-zk-client
touch README.md
touch main.py
touch config.py
touch requirements.txt
touch core/__init__.py
touch network/__init__.py
touch services/__init__.py
touch storage/__init__.py
touch tools/__init__.py
git init
git add .
git commit -m "Initial Python ZK client structure"
gh repo create skdevelopers/rakizat-zk-client --private --source=. --remote=origin --push --description "Production-ready Python ZKTeco attendance client for MB2000 and UFace800. Polls devices, preserves raw attempts, normalizes valid logs, and syncs securely to Rakizat AI HRMS API."

## Supported Goals

- connect to ZKTeco devices
- poll attendance data periodically
- preserve all raw attempts locally
- normalize valid numeric attendance logs
- queue valid records for API sync
- retry failed pushes safely
- prevent duplicate inserts
- support audit trail and diagnostics

---

## Supported Devices

Tested / intended for:

- ZKTeco MB2000
- ZKTeco UFace800

---

## Architecture

### Local Storage
This client uses **SQLite** locally with two important tables:

- `raw_events`
  - stores every raw device attempt
  - preserves bad timestamps, weird IDs, and device anomalies for audit

- `attendance_outbox`
  - stores only valid normalized rows ready for API sync
  - sent safely and idempotently to Laravel API

### Sync Strategy
- devices are polled periodically
- valid records are normalized
- valid records are pushed to Laravel API
- duplicates are safely ignored
- sent records are marked locally

---

## Why Separate Repo?

The device client is infrastructure and edge-sync logic.

It should remain separate from the Laravel application because it has different concerns:

- hardware communication
- local buffering
- retry logic
- field deployment
- non-technical operator execution

---

## Features

- TCP health checks
- ZK device connection wrapper
- raw attempt preservation
- normalized outbox pipeline
- local SQLite safety
- batch API push
- idempotent design
- WSL-friendly launcher scripts
- operator-friendly start/stop scripts

---

## Recommended Sync Policy

- device polling: every 15 seconds
- API push: every 30 to 60 seconds
- HTTP timeout: 20 seconds
- edge-safe local buffering enabled

---

## Project Structure

```text
rakizat-zk-client/
├── config.py
├── main.py
├── network/
│   ├── health.py
│   └── zk_client.py
├── core/
│   ├── device_sync.py
│   └── attendance.py
├── services/
│   └── api_client.py
├── storage/
│   ├── db.py
│   └── schema.py
├── tools/
│   ├── test_device_pull.py
│   ├── test_api_push.py
│   ├── view_raw.py
│   └── view_outbox.py
├── run.sh
├── stop.sh
└── README.md

## Use these exact repos:

 - https://github.com/skdevelopers/rakizat-ai-hrms
 - https://github.com/skdevelopers/rakizat-zk-client
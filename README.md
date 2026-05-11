AI-Driven Deception Network (Smart Honeypot)
============================================

Overview
--------

The AI-Driven Deception Network is an advanced cloud security project that demonstrates the power of "Active Defense". Instead of relying on static firewall rules, this system deploys a highly realistic, fake cloud environment (a honeypot) designed to trap attackers.

When an attacker breaches the fake network, a high-concurrency Go agent captures their telemetry and payloads. This data is streamed to a Python-based Large Language Model (LLM) backend that analyzes the threat's intent and autonomously executes an automated remediation script to block the attacker globally via an AWS Web Application Firewall (WAF).

Architecture
------------

This project is built using a multi-language microservice approach, divided into three core components:

*   **The Sandbox (Infrastructure):** Programmatically spun up via Terraform, creating an intentionally vulnerable, isolated AWS Virtual Private Cloud (VPC) with a safe blast radius.
    
*   **The Trap (Go):** A lightweight Go application mimicking a vulnerable Redis database on port 6379. It uses Go's native `net` package and `goroutines` to handle massive concurrent attacks with a low memory footprint.
    
*   **The Brain (Python & AI):** A FastAPI backend that receives attack telemetry, passes it to an LLM to extract Indicators of Compromise (IoCs), and leverages the `boto3` SDK to dynamically push blocking rules to an AWS WAF IP Set.
    

Tech Stack
----------

*   **Infrastructure as Code:** Terraform `v1.10.0+`.
    
*   **Networking & Concurrency (Muscle):** Go `1.26.3`.
    
*   **API & Automation (Brain):** Python `3.12+`, FastAPI `v0.136.1`.
    
*   **Cloud Provider & SDK:** AWS Sandbox Account, `boto3` SDK.
    
*   **AI Engine:** Google Gemini LLM API.

    
* * *

Setup & Installation
--------------------

### Prerequisites

*   An active AWS Sandbox Account configured with the AWS CLI.
    
*   Terraform installed locally.
    
*   Go and Python installed on your system.
    
*   An active API Key for Google Gemini (or your preferred LLM provider).
    

### 1\. Deploy the Sandbox Infrastructure

Navigate to the `terraform/` directory and deploy the isolated blast radius and empty AWS WAF IP Set.


    cd terraform
    terraform init
    terraform apply 

**Important:** Copy the `waf_ipset_id` output provided by Terraform upon successful completion.

### 2\. Configure the AI Brain

Navigate to the `python-brain/` directory, set up your virtual environment, and install dependencies.

    cd python-brain
    python3 -m venv venv
    source venv/bin/activate
    pip install "fastapi[standard]" pydantic google-generativeai boto3 

*   Set your environment variable for the LLM: `export GEMINI_API_KEY="your_api_key"`
    
*   In your `main.py` file, paste the Terraform `waf_ipset_id` into the `block_ip_in_waf` function so `boto3` knows where to route the blocked IP addresses.
    

### 3\. Initialize the Go Trap

Navigate to the `go/` directory to initialize the honeypot.

    cd go
    go mod init deception-trap 

* * *

Running the Pipeline
--------------------

To see the autonomous system react in real-time, you need three terminal windows:

1.  **Start the Brain:** In your `python-brain` terminal, run the API:
    
    
        fastapi dev main.py 
2.  **Start the Trap:** In your `deception-trap` terminal, start the honeypot listener:
    
    
        go run main.go 
3.  **Simulate the Attack:** In a third terminal, act as the attacker. Send a malicious payload via `netcat` using an IPv4 loopback address. _(The payload below simulates a classic Redis exploit used to drop SSH keys)_:
    
    Bash
    
        echo "CONFIG SET dir /root/.ssh/" | nc 127.0.0.1 6379 

**The Execution Flow:**

1.  The `netcat` payload connects via `127.0.0.1`.
    
2.  Go catches the connection, strips the ephemeral port to avoid AWS formatting errors, and forwards the clean IP and payload data via JSON to the Python backend.
    
3.  Python receives the data, appends the `/32` CIDR notation required by AWS, and queries the LLM.
    
4.  The AI analyzes the threat intent.
    
5.  `boto3` automatically pushes the formatted IPv4 address to your AWS WAF blocklist, locking the attacker out at the cloud edge.
    

Cleanup
-------

To avoid incurring unnecessary cloud costs, always tear down your AWS resources when finished experimenting. Navigate back to your `terraform/` directory and run:

Bash

    terraform destroy 

Confirm with `yes` to systematically dismantle the VPC, Subnets, Internet Gateway, and WAF IP Set.

## 📄 **`Raft-REST-Message-Queue` — Distributed Message Queue with Raft**

```markdown
# Raft REST Message Queue
*A lightweight distributed message queue using the Raft consensus algorithm and RESTful APIs*

## Overview
This project implements a fault-tolerant **distributed message queue** leveraging the **Raft consensus protocol** to ensure strong consistency across nodes. Designed for educational purposes, it mimics core functionalities of systems like Kafka but with a focus on clarity and reliability.

It exposes a simple RESTful interface for publishing and subscribing to topics.

## Key Features
- ⚖️ **Raft-Based Consensus**: Ensures leader election and log replication.
- 🌐 **RESTful API**: Easy-to-use endpoints for producers and consumers.
- 💾 **Persistent Queues**: Message durability across simulated node failures.
- 🔄 **Fault Tolerance**: Handles leader failover gracefully.

## Technologies Used
- **Python 3**
- Flask (for REST API)
- Custom Raft Implementation
- JSON for message serialization

## API Endpoints
- `POST /publish/<topic>` — Publish a message to a topic
- `GET /subscribe/<topic>` — Retrieve messages from a topic

## Getting Started
### Prerequisites
- Python 3.8+
- Flask

### Run the Server
```bash
pip install flask
python raftmq_server.py




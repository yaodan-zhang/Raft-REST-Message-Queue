# Raft REST Message Queue (RRMQ)
*A fault-tolerant distributed message queue implementing Raft consensus with a RESTful API*

## Overview
RRMQ is a distributed message queue system designed to ensure **consistency**, **availability**, and **fault tolerance** across multiple nodes using the **Raft consensus algorithm**. The system exposes a simple REST API for clients to create topics, publish messages, and consume messages in a **FIFO** manner.

This project was developed to explore core distributed systems principles such as leader election, log replication, and state consistency in the presence of node failures.

## Key Features
- **Raft-Based Leader Election**: Ensures reliable coordination among nodes with automatic failover.
- **Log Replication**: Guarantees consistent message state across nodes before committing operations.
- **RESTful API Interface**: Provides endpoints for topic management, message publishing, consumption, and system status.
- **Fault Tolerance**: Survives failures of up to ⌊ N/2 - 1 ⌋ nodes without service disruption.
- **FIFO Message Queue**: Ensures ordered delivery and single consumption semantics per message.

## System Architecture
- Built using **Python 3** with **Flask** for RESTful endpoints.
- Custom implementation of the **Raft consensus algorithm** without external libraries (e.g., no Zookeeper, etcd).
- Multi-threaded design to handle asynchronous leader heartbeats, elections, and client requests.

## REST API Endpoints
### **Topic Management**
- `PUT /topic` — Create a new topic  
- `GET /topic` — Retrieve list of existing topics

### **Message Queue**
- `PUT /message` — Publish a message to a topic  
- `GET /message/<topic>` — Consume the next message from a topic (FIFO, single-consumption)

### **Status**
- `GET /status` — Returns node role (`Leader`, `Candidate`, `Follower`) and current term

## Getting Started
### Prerequisites
- Python 3.8+
- Flask (`pip install flask`)

### Configuration Example
Define cluster nodes in `config.json`:
```json
{
  "addresses": [
    {"ip": "http://127.0.0.1", "port": 8567},
    {"ip": "http://127.0.0.1", "port": 9123},
    {"ip": "http://127.0.0.1", "port": 8889}
  ]
}
```

Launch Nodes:
```
python3 src/node.py config.json 0
python3 src/node.py config.json 1
python3 src/node.py config.json 2
```

### Testing
- Custom test suite provided in /test directory.  
- Supports automated leader failure and recovery scenarios.  
- Integration-tested with provided framework to ensure compliance with Raft behavior.

## Project Structure
```
src/
  node.py
test/
  election_test.py
  message_queue_test.py
  replication_test.py
  test_utils.py
  README.md
./requirements.txt
```

## Limitations
- Network partition handling limited to leader election.  
- Message delivery not guaranteed during active partition events.

## License
This software is provided for academic research purposes only. 
Commercial use is prohibited without prior written permission.

## Raft Consensus Demonstrations
https://raft.github.io/

https://thesecretlivesofdata.com/raft/

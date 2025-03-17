import sys
import json
import threading
import time
import random
import requests
from flask import Flask, request, jsonify

FOLLOWER = "Follower"
CANDIDATE = "Candidate"
LEADER = "Leader"

class MessageQueue:
    def __init__(self):
        self.data = {}  # Dictionary with topic names as keys and lists of messages as values
    
    def create_topic(self, topic):
        if topic in self.data:
            return False
        self.data[topic] = []
        return True
    
    def add_message(self, topic, message):
        if topic not in self.data:
            return False
        self.data[topic].append(message)
        return True
    
    def pop_message(self, topic):
        if (topic not in self.data) or (len(self.data[topic]) == 0):
            return False, ""
        return True, self.data[topic].pop(0)
    
    def get_topics(self) -> list:
        return list(self.data.keys())

class RaftNode:
    def __init__(self, node_index, config):
        self.node_index = node_index

        self.config = config
        self.address = config['addresses'][node_index]
        self.peers = [addr for i, addr in enumerate(config['addresses']) if i != node_index]

        self.state = FOLLOWER
        self.current_term = 0
        self.voted_for = None

        self.election_timeout = random.uniform(0.8 , 1.4)
        self.last_heartbeat = time.time()

        self.lock = threading.Lock()
        self.leader_address = None
        self.log = []

        self.commit_index = -1  # Index of the last committed log entry
        self.last_applied = -1  # Last applied log index

        self.shared_count = 0 # number of followers who have replied to each heartbeat

        threading.Thread(target=self.start_election_timer, daemon=True).start()

    def start_election_timer(self):
        while True:
            if self.state != LEADER and (time.time() - self.last_heartbeat) > self.election_timeout:
                self.start_election()

    def start_election(self):
        self.state = CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_index
        self.last_heartbeat = time.time()
        votes = 1
        
        print(f"⚡ Node {self.node_index} is starting an election for term {self.current_term}")

        threads = []

        def request_vote(peer):
            nonlocal votes
            try:
                response = requests.post(f"http://{peer['ip']}:{peer['port']}/request_vote",
                                        json={
                                            "term": self.current_term,
                                            "candidate_id": self.node_index,
                                            "log": self.log,
                                        },
                                        timeout = 0.1)
                
                data = response.json()
                    
                if data.get("vote_granted"):
                    with self.lock:
                        votes += 1
                    print(f"✅ Node {self.node_index} received vote from {peer}")
            
            except requests.exceptions.RequestException as e:
                print(f"❌ Node {self.node_index} failed to contact {peer} for vote.", e)

        for peer in self.peers:
            t = threading.Thread(target=request_vote, args=(peer,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        if votes > (len(self.peers)+1) // 2:
            self.become_leader()
        else:
            print(f"❌ Node {self.node_index} lost the election with {votes} votes.")

    def become_leader(self):
        self.state = LEADER
        self.leader_address = self.address

        # Update commit index
        self.commit_index = len(self.log) - 1

        # Apply unapplied entries
        self.apply_committed_entries()

        threading.Thread(target=self.send_heartbeats, daemon=True).start()
    
    def send_heartbeats(self):
        while self.state == LEADER:
            print(f"❤️ Leader {self.node_index} sending heartbeats...")
            shared_count = 1 # Leader itself
            threads = []

            def send_heartbeat(peer):
                nonlocal shared_count
                try:
                    response = requests.post(
                        f"http://{peer['ip']}:{peer['port']}/append_entries",
                        json={
                            "term": self.current_term,
                            "leader_id": self.node_index,
                            "leader_address": self.address,
                            "log": self.log,
                            "commit_index": self.commit_index
                            },
                        timeout = 0.1)
                    
                    if response.status_code == 200:
                        print(f"✅ Heartbeat acknowledged by {peer}")
                        with self.lock:
                            shared_count += 1     

                except requests.exceptions.RequestException:
                    print(f"❌ Failed to send heartbeat to {peer}")
            
            # Send heartbeat to peers
            for peer in self.peers:
                t = threading.Thread(target=send_heartbeat, args=(peer,))
                t.start()
                threads.append(t)

            for t in threads:
                t.join()

            # Update shared count in this heartbeat
            self.shared_count = shared_count

            time.sleep(0.2)

    def receive_heartbeat(self, leader_term, leader_address, log, commit_index):
        # Only listen to current leader
        if leader_term >= self.current_term:
            self.leader_address = leader_address
            self.log = log
            self.commit_index = commit_index
            self.last_heartbeat = time.time()

            self.apply_committed_entries()
    
    def apply_committed_entries(self):
        while self.last_applied < self.commit_index:
            self.last_applied += 1
            entry = self.log[self.last_applied]

            if entry["operation"] == "create_topic":
                response = message_queue.create_topic(entry['topic'])
                if not response:
                    print("Create topic error in node ", self.address)
                else:
                    print("Create topic " + entry['topic'] + "success!")

            elif entry["operation"] == "add_message":
                response = message_queue.add_message(entry['topic'], entry['message'])
                if not response:
                    print("Add message error in node ", self.address)
                else:
                    print("Add message \'" + entry['message'] + "\' to \'" + entry['topic'] + "\' success!")

            elif entry["operation"] == "get_topics":
                response = message_queue.get_topics()
                print("Get topics success! Topics are " + response.json()) 

            elif entry["operation"] == "get_message":
                sucess, message = message_queue.pop_message(entry['topic'])
                if not sucess:
                    print("Get message error in node ", self.address)
                else:
                    print("Get message \'" + message + "\' from topic \'" + entry['topic'] + "\'.")

    def get_status(self):
        return {
            "role": self.state,
            "term": self.current_term,
        }

# Flask End Points
app = Flask(__name__)

# Global MQ for current server
message_queue = MessageQueue()

@app.route('/topic', methods=['PUT'])
def create_topic():
    # Check leader, only leader communicates with client request
    if raft_node.state != LEADER:
        return jsonify({"success": False}), 400

    # Check data
    data = request.get_json()
    if (not data) or ('topic' not in data):
        return jsonify({"success": False}), 400
    
    # Append to Raft log 
    entry = {
        "term": raft_node.current_term,
        "topic": data["topic"],
        "operation": "create_topic"
        }
    raft_node.log.append(entry)
    
    # Collect quarum intention
    if raft_node.shared_count > (len(raft_node.peers)+1) // 2:
    
        # Commit entry
        raft_node.commit_index += 1
    
        # Leader directly applies entry
        success = message_queue.create_topic(data['topic'])
        if success:
            raft_node.last_applied += 1
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False}), 400
    else:
        return jsonify({"success": False}), 400

@app.route('/topic', methods=['GET'])
def get_topics():
    # Check leader, only leader communicates with client request
    if raft_node.state != LEADER:
        return jsonify({"success": False}), 400
    return jsonify({"success": True, "topics": message_queue.get_topics()}), 200
    
@app.route('/message', methods=['PUT'])
def add_message():
    # Check leader, only leader communicates with client request
    if raft_node.state != LEADER:
        return jsonify({"success": False}), 400
    
    # Check data
    data = request.get_json()
    if (not data) or ('topic' not in data) or ('message' not in data):
        return jsonify({"success": False}), 400
    
    # Leader append to log
    entry = {
        "term": raft_node.current_term,
        "topic": data["topic"],
        "message": data["message"],
        'operation':'add_message'
        }
    raft_node.log.append(entry)
    
    # Check quarum status
    if raft_node.shared_count > (len(raft_node.peers)+1) // 2:
        raft_node.commit_index += 1
        # Leader directly apply entry
        success = message_queue.add_message(data['topic'], data['message'])
        if success:
            raft_node.last_applied += 1
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False}), 400
    else:
        return jsonify({"success": False}), 400
    
@app.route('/message/<topic>', methods=['GET'])
def get_message(topic):
    # Check leader, only leader communicates with client request
    if raft_node.state != LEADER:
        return jsonify({"success": False}), 400
    
    # Leader append entry to log
    entry = {
        "term": raft_node.current_term,
        "operation": "get_message",
        "topic": topic,
        }
    raft_node.log.append(entry)

    # Check quarum status
    if raft_node.shared_count > (len(raft_node.peers)+1) // 2:
        # Commit entry
        raft_node.commit_index += 1

        # Leader directly apply entry
        success, message = message_queue.pop_message(topic)
        if success:
            raft_node.last_applied += 1
            return jsonify({"success": True, "message": message}), 200
        else:
            return jsonify({"success": False}), 400
    else:
        return jsonify({"success": False}), 400

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify(raft_node.get_status()), 200

@app.route('/request_vote', methods=['POST'])
def request_vote():
    # Get data
    data = request.get_json()
    term = data.get("term")
    candidate_id = data.get("candidate_id")
    log = data.get("log")
    
    # Only vote for candidate if candidate's term > self term
    # and candidate's log > self's log, no matter if the entries are applied or not.
    if term > raft_node.current_term and len(log) >= len(raft_node.log):
        raft_node.current_term = term
        raft_node.state = FOLLOWER
        raft_node.voted_for = candidate_id
        print(f"✅ Node {raft_node.node_index} voted for {candidate_id} in term {term}")
        return jsonify({"vote_granted": True}), 200

    else:
        print(f"❌ Node {raft_node.node_index} rejected vote request from {candidate_id} in term {term}")
        return jsonify({"vote_granted": False}), 400

@app.route('/append_entries', methods=['POST'])
def append_entries():
    # Get data
    data = request.get_json()
    leader_term = data.get("term")
    leader_address = data.get("leader_address")
    log = data.get("log", [])
    commit_index = data.get("commit_index", -1)
    raft_node.receive_heartbeat(leader_term, leader_address, log, commit_index)
    return jsonify({"success": True}), 200

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python src/node.py path_to_config index_to_server")
        sys.exit(1)
    
    config_path = sys.argv[1]

    node_index = int(sys.argv[2])
    
    with open(config_path, 'r') as file:
        config = json.load(file)
    
    raft_node = RaftNode(node_index, config)
    
    address = config['addresses'][node_index]
    
    app.run(host='0.0.0.0', port=address['port'])

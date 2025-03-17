## Test Description

`test_utils.py` has some classes that will manage a node and a group of nodes called swarm. nodes and swarms can be started and stopped. nodes can receive requests with function like `get_message`, `put_message`.

### step 1

`message_queue_test.py` will test the message queue implementation. test will try to getting/putting messages and topics verifying the expected output.

### step 2

`election_test.py` these test start 1 or 5 raft nodes and test if the leader is elected, unique and reelected after stopping and restarting nodes. there is a variable called `ELECTION_TIMEOUT` that sleeps the test to allow for election to happen.

### step 3
`replication_test.py` will test the ability to replicate information between raft nodes. it will start a swarm, find a leader, send some updates to it then kill it, the new leader should be in the appropriate state.

### Remark
`@pytest.fixture` are the functions called by tests before running. in this case we use them to start the nodes, then terminate them when the test is done.

`config.json` will be created in the root folder.

Each test will take care of generating a `config.json` and pass the right parameters to the node process as arguments (config and id). The test framework then will wait for the processes to startup and do elections if needed and will run one test. The test will be sending http requests to the local port given to the node.
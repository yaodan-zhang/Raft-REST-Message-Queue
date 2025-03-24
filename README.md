# raft-message-queue
Implement a distributed Raft Rest Message Queue according to the [Raft paper](https://www.usenix.org/conference/atc14/technical-sessions/presentation/ongaro).

# How to test with pytest
```bash
> pip3 install pytest
> pytest
```

run a specific file
```bash
> pytest message_queue_test.py
```

run a specific test
```bash
> pytest message_queue_test.py::test_create_topic
```



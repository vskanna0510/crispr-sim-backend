import json
from locust import HttpUser, task, between, events

class CrisprApiUser(HttpUser):
    # Think time between requests (simulating realistic user activity)
    wait_time = between(0.05, 0.2)

    @task(4)
    def health_probe(self):
        self.client.get("/health", name="GET /health")

    @task(2)
    def root_info(self):
        self.client.get("/", name="GET /")

    @task(3)
    def scan_pam(self):
        payload = {
            "sequence": "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCAGG",
            "cas_type": "cas9"
        }
        self.client.post("/crispr/scan", json=payload, name="POST /crispr/scan")

    @task(2)
    def cut_simulation(self):
        payload = {
            "sequence": "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCAGG",
            "pam_start": 44,
            "cas_type": "cas9"
        }
        self.client.post("/crispr/cut", json=payload, name="POST /crispr/cut")

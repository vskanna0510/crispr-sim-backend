"""Locust load testing scenario for CRISPR-Sim API.

Simulates 100 concurrent scientific researchers performing high-throughput
CRISPR-Cas target scanning, cleavage simulation, NHEJ repair, and comparative analyses.
"""

from locust import HttpUser, between, task


SAMPLE_DNA = (
    "ATGGTGCACCTGACTCCTGAGGAGAAGTCTGCCGTTACTGCCCTGTGGGGCAAGGTGAACGTGGATGAAG"
    "TTGGTGGTGAGGCCCTGGGCAGGCTGCTGGTGGTCTACCCTTGGACCCAGAGGTTCTTTGAGTCCTTTGG"
    "GGATCTGTCCACTCCTGATGCTGTTATGGGCAACCCTAAGGTGAAGGCTCATGGCAAGAAAGTGCTCGGT"
    "GCCTTTAGTGATGGCCTGGCTCACCTGGACAACCTCAAGGGCACCTTTGCCACACTGAGTGAGCTG"
)

SAMPLE_REPAIRED_DNA = (
    "ATGGTGCACCTGACTCCTGAGGAGAAGTCTGCCGTTACTGCCCTGTGGGGCAAGGTGAACGTGGATGAAG"
    "TTGGTGGTGAGGCCCTGGGCAGGCTGCTGGTGGTCTACCCTTGGACCCAGAGGTTCTTTGAGTCCTTTGG"
    "GGATCTGTCCACTCCTGATGCTGTTATGGGCAACCCTAAGGTGAAGGCTCATGGCAAGAAAGTGCTCGGT"
    "GCCTTTAGTGATGGCCTGGCTCACCTGGACAACCTCAAGGGCACCTTTGCCACACTG"
)


class CrisprApiUser(HttpUser):
    # Simulated realistic researcher think time between calls (20ms to 100ms)
    wait_time = between(0.02, 0.10)

    @task(6)
    def health_check(self):
        self.client.get("/health", name="GET /health")

    @task(3)
    def root_info(self):
        self.client.get("/", name="GET /")

    @task(4)
    def cas_systems(self):
        self.client.get("/advanced/cas-systems", name="GET /advanced/cas-systems")

    @task(5)
    def scan_pam(self):
        self.client.post(
            "/crispr/scan",
            json={"sequence": SAMPLE_DNA, "cas_type": "cas9"},
            name="POST /crispr/scan",
        )

    @task(4)
    def cut_simulation(self):
        self.client.post(
            "/crispr/cut",
            json={"sequence": SAMPLE_DNA, "pam_start": 3, "cas_type": "cas9"},
            name="POST /crispr/cut",
        )

    @task(4)
    def nhej_simulation(self):
        self.client.post(
            "/crispr/nhej",
            json={"sequence": SAMPLE_DNA, "cut_position": 0, "deletion_size": 3},
            name="POST /crispr/nhej",
        )

    @task(4)
    def comparative_analysis(self):
        self.client.post(
            "/analysis/compare",
            json={
                "original_sequence": SAMPLE_DNA,
                "edited_sequence": SAMPLE_REPAIRED_DNA,
                "repair_type": "NHEJ",
            },
            name="POST /analysis/compare",
        )

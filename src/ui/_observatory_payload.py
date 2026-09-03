"""Compressed one-page observatory payload (Etapa 2)."""

# The payload was split into two modules during GitHub API transfer.
# Keep the assembly here deliberately simple so Streamlit can import it
# without depending on non-existent intermediate chunk modules.
from src.ui._payload_a import PART_A
from src.ui._payload_b import PART_B

PAYLOAD = PART_A + PART_B

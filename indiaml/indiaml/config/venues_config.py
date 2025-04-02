from pydantic import BaseModel
from typing import List

class VenueConfig(BaseModel):
    conference: str
    year: int
    track: str
    source_adapter: str  # e.g., "openreview"
    source_id: str       # e.g., "NeurIPS.cc/2024/Conference"
    adapter_class: str   # e.g., "NeurIPSAdapter", "ICMLAdapter", "ICAIAdapter"

# Define your venue configurations here
VENUE_CONFIGS: List[VenueConfig] = [
    # VenueConfig(
    #     conference="NeurIPS",
    #     year=2024,
    #     track="Conference",
    #     source_adapter="openreview",
    #     source_id="NeurIPS.cc/2024/Conference",
    #     adapter_class="NeurIPSAdapter"
    # ),
    # VenueConfig(
    #     conference="ICML",
    #     year=2024,
    #     track="Conference",
    #     source_adapter="openreview",
    #     source_id="ICML.cc/2024/Conference",
    #     adapter_class="ICMLAdapter"
    # ),
    VenueConfig(
        conference="ICLR",
        year=2024,
        track="Conference",
        source_adapter="openreview",
        source_id="ICLR.cc/2024/Conference",
        adapter_class="ICAIAdapter"
    ),
    # VenueConfig(
    #     conference="ICLR",
    #     year=2025,
    #     track="Conference",
    #     source_adapter="openreview",
    #     source_id="ICLR.cc/2025/Conference",
    #     adapter_class="ICAIAdapter"
    # )
    # Add more VenueConfig instances as needed
]

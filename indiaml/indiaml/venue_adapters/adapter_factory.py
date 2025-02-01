# adapters/adapter_factory.py

from .base_adapter import BaseAdapter
from .neurips_adapter import NeurIPSAdapter
from .icml_adapter import ICMLAdapter
from .icai_adapter import ICAIAdapter

def get_adapter(config) -> BaseAdapter:
    """Factory function to get the appropriate adapter instance based on the config."""
    adapter_classes = {
        "NeurIPSAdapter": NeurIPSAdapter,
        "ICMLAdapter": ICMLAdapter,
        "ICAIAdapter": ICAIAdapter
        # Add other adapters here as needed
    }
    
    adapter_class = adapter_classes.get(config.adapter_class)
    if not adapter_class:
        raise ValueError(f"Unknown adapter class: {config.adapter_class}")
    
    return adapter_class(config)

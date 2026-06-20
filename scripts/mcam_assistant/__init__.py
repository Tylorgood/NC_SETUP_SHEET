"""MCAM Assistant v0.1 manufacturing pipeline."""

from .pipeline import ManufacturingPipeline
from .registry import PluginRegistry

__all__ = ["ManufacturingPipeline", "PluginRegistry"]

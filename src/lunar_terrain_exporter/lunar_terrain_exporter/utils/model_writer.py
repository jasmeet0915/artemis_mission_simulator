"""Backward-compatibility shim — use model_writers.sdf_model_writer instead."""

from ..model_writers.sdf_model_writer import SDFModelWriter as ModelWriter

__all__ = ["ModelWriter"]


"""
DTO module - Data Transfer Objects for unidirectional data flow.

This module provides ViewDTO and BuildDTO base classes that enable type-safe
data transformations between Domain models and external representations.

The DTOs enforce a unidirectional data flow:
- BuildDTO: External data → Domain (inbound)
- ViewDTO: Domain → External data (outbound)
"""

from .build import BuildDTO
from .view import ViewDTO

__all__ = ["BuildDTO", "ViewDTO"]

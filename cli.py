"""
File: scripts/cli.py

A package providing CLI utilities.
"""

import argparse
from abc import ABC, abstractmethod
from typing import Self


class ArgumentConfig(ABC, argparse.Namespace):
    @classmethod
    @abstractmethod
    def parse_args(cls) -> "Self":
        pass

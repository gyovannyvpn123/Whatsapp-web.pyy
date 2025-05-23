"""
Protocol handling module for WhatsApp Web binary and protobuf messages.
"""

from .binary_reader import BinaryReader
from .binary_writer import BinaryWriter
from .protobuf_handler import ProtobufHandler

__all__ = ["BinaryReader", "BinaryWriter", "ProtobufHandler"]

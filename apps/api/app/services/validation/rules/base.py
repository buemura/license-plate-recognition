"""Base plate rule interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CorrectionInfo:
    """Information about a correction made to plate text."""

    position: int
    original: str
    corrected: str
    reason: str


class PlateRule(ABC):
    """Abstract base class for plate format rules."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this rule (e.g., 'BR_MERCOSUL')."""
        pass

    @property
    @abstractmethod
    def region(self) -> str:
        """Region code (e.g., 'BR' for Brazil)."""
        pass

    @property
    @abstractmethod
    def pattern(self) -> str:
        """Regex pattern for matching valid plates."""
        pass

    @property
    @abstractmethod
    def example(self) -> str:
        """Example of a valid plate (e.g., 'ABC1D23')."""
        pass

    @abstractmethod
    def get_position_type(self, position: int) -> str | None:
        """Get expected character type for a position.

        Returns:
            'letter', 'digit', or None if position is out of range
        """
        pass

    @abstractmethod
    def get_correction(self, char: str, position: int) -> str | None:
        """Get the corrected character for a given position.

        Args:
            char: The character to potentially correct
            position: The position in the plate string

        Returns:
            Corrected character, or None if no correction needed
        """
        pass

    def get_plate_length(self) -> int:
        """Get the expected length of plates matching this format."""
        # Default implementation - override if needed
        return len(self.example)

"""Plate format registry for managing format rules."""

import re
from dataclasses import dataclass

from app.services.validation.rules.base import PlateRule
from app.services.validation.rules.brazil import BrazilMercosulRule, BrazilOldRule


@dataclass
class PlateFormat:
    """Wrapper for plate format information."""

    name: str
    region: str
    pattern: str
    example: str
    rule: PlateRule


class PlateFormatRegistry:
    """Registry for managing plate format rules.

    Allows registering and querying plate formats by region.
    """

    def __init__(self):
        self._formats: dict[str, list[PlateFormat]] = {}
        self._rules: dict[str, PlateRule] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default plate formats."""
        # Brazilian formats
        self.register_rule(BrazilMercosulRule())
        self.register_rule(BrazilOldRule())

    def register_rule(self, rule: PlateRule) -> None:
        """Register a plate format rule."""
        format_obj = PlateFormat(
            name=rule.name,
            region=rule.region,
            pattern=rule.pattern,
            example=rule.example,
            rule=rule,
        )

        if rule.region not in self._formats:
            self._formats[rule.region] = []
        self._formats[rule.region].append(format_obj)
        self._rules[rule.name] = rule

    def get_formats(self, region: str | None = None) -> list[PlateFormat]:
        """Get plate formats, optionally filtered by region."""
        if region:
            return self._formats.get(region, [])
        return [f for formats in self._formats.values() for f in formats]

    def get_rule(self, name: str) -> PlateRule | None:
        """Get a specific rule by name."""
        return self._rules.get(name)

    def get_regions(self) -> list[str]:
        """Get list of all registered regions."""
        return list(self._formats.keys())

    def match(self, text: str) -> tuple[PlateFormat | None, float]:
        """Find the best matching format for given text.

        Args:
            text: Plate text to match

        Returns:
            Tuple of (matched format, match score 0-1)
        """
        normalized = self._normalize(text)

        # First, try exact pattern matches
        for formats in self._formats.values():
            for fmt in formats:
                if re.match(fmt.pattern, normalized):
                    return fmt, 1.0

        # Try partial matching by calculating similarity score
        best_match = None
        best_score = 0.0

        for formats in self._formats.values():
            for fmt in formats:
                score = self._calculate_match_score(normalized, fmt)
                if score > best_score:
                    best_score = score
                    best_match = fmt

        return best_match, best_score

    def match_with_region(
        self, text: str, region: str
    ) -> tuple[PlateFormat | None, float]:
        """Match against formats from a specific region only."""
        normalized = self._normalize(text)
        formats = self._formats.get(region, [])

        # Try exact match first
        for fmt in formats:
            if re.match(fmt.pattern, normalized):
                return fmt, 1.0

        # Partial matching
        best_match = None
        best_score = 0.0

        for fmt in formats:
            score = self._calculate_match_score(normalized, fmt)
            if score > best_score:
                best_score = score
                best_match = fmt

        return best_match, best_score

    def _normalize(self, text: str) -> str:
        """Normalize text for matching."""
        # Remove spaces, hyphens, and convert to uppercase
        return re.sub(r"[\s\-]", "", text.upper())

    def _calculate_match_score(self, text: str, fmt: PlateFormat) -> float:
        """Calculate how well text matches a format.

        Returns score from 0 to 1.
        """
        expected_len = fmt.rule.get_plate_length()

        # Length penalty
        len_diff = abs(len(text) - expected_len)
        if len_diff > 2:
            return 0.0

        length_score = 1.0 - (len_diff * 0.2)

        # Position type matching score
        if len(text) == 0:
            return 0.0

        correct_positions = 0
        total_positions = min(len(text), expected_len)

        for i in range(total_positions):
            expected_type = fmt.rule.get_position_type(i)
            if expected_type is None:
                continue

            char = text[i]
            if expected_type == "letter" and char.isalpha():
                correct_positions += 1
            elif expected_type == "digit" and char.isdigit():
                correct_positions += 1

        position_score = correct_positions / total_positions if total_positions > 0 else 0

        # Combined score (weighted)
        return length_score * 0.3 + position_score * 0.7

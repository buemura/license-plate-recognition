"""Plate validator with auto-correction capabilities."""

import re
from dataclasses import dataclass, field

from app.services.validation.formats import PlateFormatRegistry
from app.services.validation.rules.base import CorrectionInfo


@dataclass
class ValidationResult:
    """Result of plate validation."""

    text: str  # Final validated/corrected text
    original_text: str  # Original input text
    confidence: float  # Validation confidence (0-1)
    region: str | None  # Detected region (e.g., 'BR')
    format_name: str | None  # Detected format name (e.g., 'BR_MERCOSUL')
    corrections_made: list[CorrectionInfo] = field(default_factory=list)
    is_valid: bool = False  # Whether the result matches a known format


@dataclass
class ValidationConfig:
    """Configuration for plate validation."""

    min_length: int = 6
    max_length: int = 8
    default_region: str = "BR"
    correction_confidence_penalty: float = 0.05  # Per correction


class PlateValidator:
    """Validates and corrects plate text based on format rules."""

    # Words commonly found on plates that are NOT the plate number
    BLACKLIST = {
        "BRASIL",
        "BRAZIL",
        "MERCOSUL",
        "MERCOSUR",
        "BR",
    }

    def __init__(
        self,
        registry: PlateFormatRegistry | None = None,
        config: ValidationConfig | None = None,
    ):
        self.registry = registry or PlateFormatRegistry()
        self.config = config or ValidationConfig()

    def validate(
        self,
        text: str,
        ocr_confidence: float = 1.0,
        region: str | None = None,
    ) -> ValidationResult:
        """Validate and potentially correct plate text.

        Args:
            text: Raw plate text from OCR
            ocr_confidence: Confidence from OCR (0-1)
            region: Restrict matching to specific region

        Returns:
            ValidationResult with corrected text and metadata
        """
        original = text
        normalized = self._normalize(text)

        # Check blacklist
        if self._is_blacklisted(normalized):
            return ValidationResult(
                text=normalized,
                original_text=original,
                confidence=0.0,
                region=None,
                format_name=None,
                corrections_made=[],
                is_valid=False,
            )

        # Check length
        if not self._is_valid_length(normalized):
            return ValidationResult(
                text=normalized,
                original_text=original,
                confidence=ocr_confidence * 0.3,  # Heavy penalty
                region=None,
                format_name=None,
                corrections_made=[],
                is_valid=False,
            )

        # Find matching format
        if region:
            format_match, match_score = self.registry.match_with_region(
                normalized, region
            )
        else:
            format_match, match_score = self.registry.match(normalized)

        if format_match and match_score == 1.0:
            # Exact match - no corrections needed
            return ValidationResult(
                text=normalized,
                original_text=original,
                confidence=ocr_confidence,
                region=format_match.region,
                format_name=format_match.name,
                corrections_made=[],
                is_valid=True,
            )

        if format_match:
            # Try to correct using the matched format's rules
            corrected, corrections = self._apply_corrections(
                normalized, format_match.rule
            )

            # Check if corrected text matches the pattern
            if re.match(format_match.pattern, corrected):
                # Calculate confidence penalty for corrections
                correction_penalty = len(corrections) * self.config.correction_confidence_penalty
                adjusted_confidence = max(0.0, ocr_confidence * match_score - correction_penalty)

                return ValidationResult(
                    text=corrected,
                    original_text=original,
                    confidence=adjusted_confidence,
                    region=format_match.region,
                    format_name=format_match.name,
                    corrections_made=corrections,
                    is_valid=True,
                )

        # No valid format match - check if it looks plate-like
        if self._looks_like_plate(normalized):
            return ValidationResult(
                text=normalized,
                original_text=original,
                confidence=ocr_confidence * 0.5,  # Penalty for no format match
                region=region,
                format_name=None,
                corrections_made=[],
                is_valid=False,
            )

        return ValidationResult(
            text=normalized,
            original_text=original,
            confidence=0.0,
            region=None,
            format_name=None,
            corrections_made=[],
            is_valid=False,
        )

    def _normalize(self, text: str) -> str:
        """Clean and normalize plate text."""
        # Remove special characters except alphanumeric
        cleaned = re.sub(r"[^A-Za-z0-9]", "", text)
        return cleaned.upper()

    def _is_blacklisted(self, text: str) -> bool:
        """Check if text is a blacklisted word."""
        return text in self.BLACKLIST

    def _is_valid_length(self, text: str) -> bool:
        """Check if text length is valid for a plate."""
        return self.config.min_length <= len(text) <= self.config.max_length

    def _looks_like_plate(self, text: str) -> bool:
        """Check if text could be a plate (has both letters and digits)."""
        has_letters = any(c.isalpha() for c in text)
        has_digits = any(c.isdigit() for c in text)
        return has_letters and has_digits

    def _apply_corrections(
        self, text: str, rule
    ) -> tuple[str, list[CorrectionInfo]]:
        """Apply format-specific corrections to text."""
        chars = list(text)
        corrections = []

        for i, char in enumerate(chars):
            expected_type = rule.get_position_type(i)
            if expected_type is None:
                continue

            correction = rule.get_correction(char, i)
            if correction:
                corrections.append(
                    CorrectionInfo(
                        position=i,
                        original=char,
                        corrected=correction,
                        reason=f"expected_{expected_type}",
                    )
                )
                chars[i] = correction

        return "".join(chars), corrections

    def validate_batch(
        self,
        candidates: list[tuple[str, float]],
        region: str | None = None,
    ) -> ValidationResult | None:
        """Validate multiple candidates and return the best match.

        Args:
            candidates: List of (text, confidence) tuples
            region: Restrict matching to specific region

        Returns:
            Best validation result, or None if no valid matches
        """
        results = []

        for text, confidence in candidates:
            result = self.validate(text, confidence, region)
            if result.is_valid or result.confidence > 0:
                results.append(result)

        if not results:
            return None

        # Sort by: is_valid (desc), confidence (desc)
        results.sort(
            key=lambda r: (r.is_valid, r.confidence),
            reverse=True,
        )

        return results[0]

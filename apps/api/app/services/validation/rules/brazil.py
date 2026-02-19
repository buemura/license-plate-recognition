"""Brazilian license plate format rules."""

from app.services.validation.rules.base import PlateRule


class BrazilMercosulRule(PlateRule):
    """Brazilian Mercosul format (2018+): ABC1D23

    Format: LLL D L DD (3 letters, 1 digit, 1 letter, 2 digits)
    """

    # Position type mapping: 0-2 letters, 3 digit, 4 letter, 5-6 digits
    _position_types = {
        0: "letter",
        1: "letter",
        2: "letter",
        3: "digit",
        4: "letter",
        5: "digit",
        6: "digit",
    }

    # Corrections for each position based on expected type
    _letter_to_digit = {
        "O": "0",
        "Q": "0",
        "D": "0",
        "I": "1",
        "L": "1",
        "Z": "2",
        "S": "5",
        "G": "6",
        "B": "8",
    }

    _digit_to_letter = {
        "0": "O",
        "1": "I",
        "2": "Z",
        "5": "S",
        "6": "G",
        "8": "B",
    }

    @property
    def name(self) -> str:
        return "BR_MERCOSUL"

    @property
    def region(self) -> str:
        return "BR"

    @property
    def pattern(self) -> str:
        return r"^[A-Z]{3}\d[A-Z]\d{2}$"

    @property
    def example(self) -> str:
        return "ABC1D23"

    def get_position_type(self, position: int) -> str | None:
        return self._position_types.get(position)

    def get_correction(self, char: str, position: int) -> str | None:
        expected_type = self.get_position_type(position)
        if expected_type is None:
            return None

        char_upper = char.upper()

        if expected_type == "letter":
            # If we have a digit but expect a letter
            if char_upper.isdigit():
                return self._digit_to_letter.get(char_upper)
        elif expected_type == "digit":
            # If we have a letter but expect a digit
            if char_upper.isalpha():
                return self._letter_to_digit.get(char_upper)

        return None


class BrazilOldRule(PlateRule):
    """Old Brazilian format (pre-2018): ABC1234

    Format: LLL DDDD (3 letters, 4 digits)
    """

    _position_types = {
        0: "letter",
        1: "letter",
        2: "letter",
        3: "digit",
        4: "digit",
        5: "digit",
        6: "digit",
    }

    _letter_to_digit = {
        "O": "0",
        "Q": "0",
        "D": "0",
        "I": "1",
        "L": "1",
        "Z": "2",
        "S": "5",
        "G": "6",
        "B": "8",
    }

    _digit_to_letter = {
        "0": "O",
        "1": "I",
        "2": "Z",
        "5": "S",
        "6": "G",
        "8": "B",
    }

    @property
    def name(self) -> str:
        return "BR_OLD"

    @property
    def region(self) -> str:
        return "BR"

    @property
    def pattern(self) -> str:
        return r"^[A-Z]{3}\d{4}$"

    @property
    def example(self) -> str:
        return "ABC1234"

    def get_position_type(self, position: int) -> str | None:
        return self._position_types.get(position)

    def get_correction(self, char: str, position: int) -> str | None:
        expected_type = self.get_position_type(position)
        if expected_type is None:
            return None

        char_upper = char.upper()

        if expected_type == "letter":
            if char_upper.isdigit():
                return self._digit_to_letter.get(char_upper)
        elif expected_type == "digit":
            if char_upper.isalpha():
                return self._letter_to_digit.get(char_upper)

        return None

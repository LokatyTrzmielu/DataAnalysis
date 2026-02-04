"""SKU normalization and collision detection."""

import re
from dataclasses import dataclass, field

import polars as pl


@dataclass
class SKUCollision:
    """SKU collision after normalization."""
    normalized_sku: str
    original_skus: list[str]
    collision_type: str  # "case", "whitespace", "special_chars"


@dataclass
class NormalizationResult:
    """SKU normalization result."""
    df: pl.DataFrame
    collisions: list[SKUCollision] = field(default_factory=list)
    total_original: int = 0
    total_normalized: int = 0
    total_collisions: int = 0


class SKUNormalizer:
    """SKU normalization and validation."""

    def __init__(
        self,
        uppercase: bool = True,
        strip_whitespace: bool = True,
        remove_special_chars: bool = False,
        replace_chars: dict[str, str] | None = None,
    ) -> None:
        """Initialize normalizer.

        Args:
            uppercase: Whether to convert to uppercase
            strip_whitespace: Whether to remove whitespace
            remove_special_chars: Whether to remove special characters
            replace_chars: Character replacement mapping
        """
        self.uppercase = uppercase
        self.strip_whitespace = strip_whitespace
        self.remove_special_chars = remove_special_chars
        self.replace_chars = replace_chars or {}

    def normalize_sku(self, sku: str | None) -> str:
        """Normalize single SKU.

        Args:
            sku: Original SKU

        Returns:
            Normalized SKU
        """
        if sku is None:
            return ""

        result = str(sku)

        # Remove whitespace
        if self.strip_whitespace:
            result = result.strip()
            result = re.sub(r"\s+", "", result)

        # Replace characters
        for old, new in self.replace_chars.items():
            result = result.replace(old, new)

        # Remove special characters
        if self.remove_special_chars:
            result = re.sub(r"[^a-zA-Z0-9\-_]", "", result)

        # Uppercase
        if self.uppercase:
            result = result.upper()

        return result

    def normalize_dataframe(
        self,
        df: pl.DataFrame,
        sku_column: str = "sku",
        output_column: str | None = None,
    ) -> NormalizationResult:
        """Normalize SKU column in DataFrame.

        Args:
            df: DataFrame with SKU column
            sku_column: SKU column name
            output_column: Output column name (default: overwrite)

        Returns:
            NormalizationResult with data and collisions
        """
        if output_column is None:
            output_column = sku_column

        # Get original SKUs
        original_skus = df[sku_column].to_list()
        total_original = len(original_skus)

        # Normalize
        normalized_skus = [self.normalize_sku(sku) for sku in original_skus]

        # Add column with normalized SKUs
        result_df = df.with_columns([
            pl.Series(output_column, normalized_skus),
        ])

        # Detect collisions
        collisions = self._detect_collisions(original_skus, normalized_skus)

        # Unique SKUs after normalization
        total_normalized = len(set(normalized_skus))

        return NormalizationResult(
            df=result_df,
            collisions=collisions,
            total_original=total_original,
            total_normalized=total_normalized,
            total_collisions=len(collisions),
        )

    def _detect_collisions(
        self,
        original_skus: list[str],
        normalized_skus: list[str],
    ) -> list[SKUCollision]:
        """Detect collisions after normalization.

        Collision occurs when different original SKUs
        have the same normalized SKU.
        """
        # Group original SKUs by normalized
        normalized_to_original: dict[str, set[str]] = {}
        for orig, norm in zip(original_skus, normalized_skus):
            if norm not in normalized_to_original:
                normalized_to_original[norm] = set()
            normalized_to_original[norm].add(str(orig))

        collisions = []
        for norm_sku, orig_set in normalized_to_original.items():
            if len(orig_set) > 1:
                # Determine collision type
                collision_type = self._determine_collision_type(list(orig_set))
                collisions.append(SKUCollision(
                    normalized_sku=norm_sku,
                    original_skus=sorted(orig_set),
                    collision_type=collision_type,
                ))

        return collisions

    def _determine_collision_type(self, skus: list[str]) -> str:
        """Determine collision type."""
        # Check if difference is only in letter case
        lowered = [s.lower() for s in skus]
        if len(set(lowered)) == 1:
            return "case"

        # Check if difference is only in whitespace
        stripped = [re.sub(r"\s+", "", s) for s in skus]
        if len(set(stripped)) == 1:
            return "whitespace"

        return "special_chars"


def normalize_sku_column(
    df: pl.DataFrame,
    sku_column: str = "sku",
    uppercase: bool = True,
) -> NormalizationResult:
    """Helper function for SKU normalization.

    Args:
        df: DataFrame
        sku_column: SKU column name
        uppercase: Whether to convert to uppercase

    Returns:
        NormalizationResult
    """
    normalizer = SKUNormalizer(uppercase=uppercase)
    return normalizer.normalize_dataframe(df, sku_column)

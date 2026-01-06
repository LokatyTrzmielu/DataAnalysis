"""Testy jednostkowe dla modulu ingest."""

import tempfile
from pathlib import Path

import polars as pl
import pytest

from src.ingest.readers import FileReader, read_file
from src.ingest.mapping import (
    MappingWizard,
    MASTERDATA_SCHEMA,
    ORDERS_SCHEMA,
    create_masterdata_wizard,
    create_orders_wizard,
)
from src.ingest.units import (
    UnitDetector,
    UnitConverter,
    LengthUnit,
    WeightUnit,
    LENGTH_TO_MM,
    WEIGHT_TO_KG,
)
from src.ingest.sku_normalize import SKUNormalizer, normalize_sku_column


FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ============================================================================
# Testy FileReader
# ============================================================================


class TestFileReader:
    """Testy dla klasy FileReader."""

    def test_detect_file_type_csv(self):
        """Test detekcji typu pliku CSV."""
        reader = FileReader(FIXTURES_DIR / "masterdata_clean.csv")
        assert reader.detect_file_type() == "csv"

    def test_detect_file_type_xlsx(self):
        """Test detekcji typu pliku XLSX."""
        reader = FileReader(FIXTURES_DIR / "test_masterdata.xlsx")
        assert reader.detect_file_type() == "xlsx"

    def test_file_not_found(self):
        """Test bledu dla nieistniejacego pliku."""
        with pytest.raises(FileNotFoundError):
            FileReader("nonexistent_file.csv")

    def test_unsupported_extension(self):
        """Test bledu dla nieobslugiwanego rozszerzenia."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        reader = FileReader(temp_path)
        with pytest.raises(ValueError, match="Unsupported extension"):
            reader.detect_file_type()

        Path(temp_path).unlink()

    def test_read_csv(self):
        """Test wczytania pliku CSV."""
        df = read_file(FIXTURES_DIR / "masterdata_clean.csv")
        assert isinstance(df, pl.DataFrame)
        assert len(df) > 0
        assert "sku" in df.columns

    def test_read_xlsx(self):
        """Test wczytania pliku XLSX."""
        df = read_file(FIXTURES_DIR / "test_masterdata.xlsx")
        assert isinstance(df, pl.DataFrame)
        assert len(df) > 0
        assert "sku" in df.columns

    def test_detect_separator_semicolon(self):
        """Test detekcji separatora semicolon."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write("a;b;c\n1;2;3\n4;5;6\n")
            temp_path = f.name

        reader = FileReader(temp_path)
        assert reader.detect_separator() == ";"
        Path(temp_path).unlink()

    def test_detect_separator_comma(self):
        """Test detekcji separatora comma."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write("a,b,c\n1,2,3\n4,5,6\n")
            temp_path = f.name

        reader = FileReader(temp_path)
        assert reader.detect_separator() == ","
        Path(temp_path).unlink()

    def test_get_preview(self):
        """Test podgladu danych."""
        reader = FileReader(FIXTURES_DIR / "masterdata_clean.csv")
        preview = reader.get_preview(n_rows=5)
        assert len(preview) == 5

    def test_get_columns(self):
        """Test pobierania listy kolumn."""
        reader = FileReader(FIXTURES_DIR / "masterdata_clean.csv")
        columns = reader.get_columns()
        assert isinstance(columns, list)
        assert len(columns) > 0

    def test_normalize_columns(self):
        """Test normalizacji nazw kolumn."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write("Column Name,UPPER CASE,  spaces  \n1,2,3\n")
            temp_path = f.name

        df = read_file(temp_path)
        assert "column_name" in df.columns
        assert "upper_case" in df.columns
        assert "spaces" in df.columns
        Path(temp_path).unlink()


# ============================================================================
# Testy MappingWizard
# ============================================================================


class TestMappingWizard:
    """Testy dla MappingWizard."""

    def test_create_masterdata_wizard(self):
        """Test tworzenia wizarda dla masterdata."""
        wizard = create_masterdata_wizard()
        assert wizard.schema == MASTERDATA_SCHEMA

    def test_create_orders_wizard(self):
        """Test tworzenia wizarda dla orders."""
        wizard = create_orders_wizard()
        assert wizard.schema == ORDERS_SCHEMA

    def test_auto_map_exact_match(self):
        """Test auto-mapowania z dokladnym dopasowaniem."""
        wizard = create_masterdata_wizard()
        columns = ["sku", "length", "width", "height", "weight", "stock"]
        result = wizard.auto_map(columns)

        assert result.is_complete
        assert len(result.missing_required) == 0
        assert result.get_source_column("sku") == "sku"
        assert result.get_source_column("length") == "length"

    def test_auto_map_alias_match(self):
        """Test auto-mapowania z aliasami."""
        wizard = create_masterdata_wizard()
        columns = ["artykul", "dlugosc", "szerokosc", "wysokosc", "waga", "ilosc"]
        result = wizard.auto_map(columns)

        assert result.is_complete
        assert result.get_source_column("sku") == "artykul"
        assert result.get_source_column("length") == "dlugosc"
        assert result.get_source_column("width") == "szerokosc"

    def test_auto_map_partial_match(self):
        """Test auto-mapowania z czesciowym dopasowaniem."""
        wizard = create_masterdata_wizard()
        columns = ["item_sku", "length_mm", "width_mm", "height_mm", "weight_kg"]
        result = wizard.auto_map(columns)

        assert result.get_source_column("length") == "length_mm"
        assert result.get_source_column("weight") == "weight_kg"

    def test_auto_map_missing_required(self):
        """Test auto-mapowania z brakujacymi wymaganymi polami."""
        wizard = create_masterdata_wizard()
        columns = ["sku", "price", "description"]  # Brak wymiarow i wagi
        result = wizard.auto_map(columns)

        assert not result.is_complete
        assert "length" in result.missing_required
        assert "width" in result.missing_required

    def test_get_suggestions(self):
        """Test pobierania sugestii mapowania."""
        wizard = create_masterdata_wizard()
        suggestions = wizard.get_suggestions("length_mm")

        assert len(suggestions) > 0
        assert suggestions[0][0] == "length"  # Najlepsza sugestia
        assert suggestions[0][1] == 1.0  # Pewnosc 100%

    def test_apply_mapping(self):
        """Test aplikowania mapowania do DataFrame."""
        wizard = create_masterdata_wizard()
        df = pl.DataFrame({
            "artykul": ["SKU1", "SKU2"],
            "dlugosc": [100, 200],
            "szerokosc": [50, 100],
            "wysokosc": [30, 60],
            "waga": [1.5, 3.0],
        })

        mapping = wizard.auto_map(df.columns)
        result_df = wizard.apply_mapping(df, mapping)

        assert "sku" in result_df.columns
        assert "length" in result_df.columns
        assert "width" in result_df.columns


# ============================================================================
# Testy UnitDetector
# ============================================================================


class TestUnitDetector:
    """Testy dla UnitDetector."""

    def test_detect_length_mm(self):
        """Test detekcji jednostki mm."""
        detector = UnitDetector()
        values = [100, 200, 300, 400, 500]  # Typowe wartosci w mm
        result = detector.detect_length_unit(values)

        assert result.detected_unit == LengthUnit.MM

    def test_detect_length_cm(self):
        """Test detekcji jednostki cm."""
        detector = UnitDetector()
        values = [10, 20, 30, 40, 50]  # Typowe wartosci w cm
        result = detector.detect_length_unit(values)

        assert result.detected_unit == LengthUnit.CM

    def test_detect_length_m(self):
        """Test detekcji jednostki m."""
        detector = UnitDetector()
        values = [0.5, 1.0, 1.5, 2.0, 2.5]  # Typowe wartosci w m
        result = detector.detect_length_unit(values)

        assert result.detected_unit == LengthUnit.M

    def test_detect_length_from_column_name(self):
        """Test detekcji jednostki z nazwy kolumny."""
        detector = UnitDetector()
        values = [50, 60, 70]  # Wartosci niejednoznaczne
        result = detector.detect_length_unit(values, column_name="length_mm")

        assert result.detected_unit == LengthUnit.MM
        assert result.confidence == 0.9

    def test_detect_weight_kg(self):
        """Test detekcji jednostki kg."""
        detector = UnitDetector()
        values = [1.5, 2.0, 5.0, 10.0, 20.0]  # Typowe wartosci w kg
        result = detector.detect_weight_unit(values)

        assert result.detected_unit == WeightUnit.KG

    def test_detect_weight_g(self):
        """Test detekcji jednostki g."""
        detector = UnitDetector()
        values = [500, 1000, 2000, 5000]  # Typowe wartosci w g
        result = detector.detect_weight_unit(values)

        assert result.detected_unit == WeightUnit.G

    def test_detect_weight_from_column_name(self):
        """Test detekcji jednostki wagi z nazwy kolumny."""
        detector = UnitDetector()
        values = [100, 200, 300]
        result = detector.detect_weight_unit(values, column_name="weight_kg")

        assert result.detected_unit == WeightUnit.KG

    def test_detect_empty_values(self):
        """Test detekcji z pustymi wartosciami."""
        detector = UnitDetector()
        result = detector.detect_length_unit([])

        assert result.confidence == 0.0


class TestUnitConverter:
    """Testy dla UnitConverter."""

    def test_convert_dimensions_cm_to_mm(self):
        """Test konwersji wymiarow z cm do mm."""
        converter = UnitConverter()
        df = pl.DataFrame({
            "length": [10.0, 20.0, 30.0],
            "width": [5.0, 10.0, 15.0],
            "height": [2.0, 4.0, 6.0],
        })

        result = converter.convert_dimensions_to_mm(
            df, "length", "width", "height",
            auto_detect=False, source_unit=LengthUnit.CM
        )

        assert result["length"].to_list() == [100.0, 200.0, 300.0]
        assert result["width"].to_list() == [50.0, 100.0, 150.0]

    def test_convert_weight_g_to_kg(self):
        """Test konwersji wagi z g do kg."""
        converter = UnitConverter()
        df = pl.DataFrame({
            "weight": [1000.0, 2000.0, 5000.0],
        })

        result = converter.convert_weight_to_kg(
            df, "weight",
            auto_detect=False, source_unit=WeightUnit.G
        )

        assert result["weight"].to_list() == [1.0, 2.0, 5.0]

    def test_no_conversion_needed(self):
        """Test gdy konwersja nie jest potrzebna."""
        converter = UnitConverter()
        df = pl.DataFrame({
            "length": [100.0, 200.0],
            "width": [50.0, 100.0],
            "height": [30.0, 60.0],
        })

        result = converter.convert_dimensions_to_mm(
            df, "length", "width", "height",
            auto_detect=False, source_unit=LengthUnit.MM
        )

        # DataFrame powinien byc taki sam
        assert result["length"].to_list() == df["length"].to_list()


# ============================================================================
# Testy SKUNormalizer
# ============================================================================


class TestSKUNormalizer:
    """Testy dla SKUNormalizer."""

    def test_normalize_uppercase(self):
        """Test normalizacji do uppercase."""
        normalizer = SKUNormalizer(uppercase=True)
        assert normalizer.normalize_sku("abc-123") == "ABC-123"

    def test_normalize_strip_whitespace(self):
        """Test usuwania bialych znakow."""
        normalizer = SKUNormalizer(strip_whitespace=True)
        assert normalizer.normalize_sku("  ABC  123  ") == "ABC123"

    def test_normalize_remove_special_chars(self):
        """Test usuwania znakow specjalnych."""
        normalizer = SKUNormalizer(remove_special_chars=True)
        assert normalizer.normalize_sku("ABC@#$123") == "ABC123"

    def test_normalize_replace_chars(self):
        """Test zamiany znakow."""
        normalizer = SKUNormalizer(replace_chars={"/": "-", "\\": "-"})
        assert normalizer.normalize_sku("ABC/123\\456") == "ABC-123-456"

    def test_normalize_none(self):
        """Test normalizacji None."""
        normalizer = SKUNormalizer()
        assert normalizer.normalize_sku(None) == ""

    def test_normalize_dataframe(self):
        """Test normalizacji DataFrame."""
        normalizer = SKUNormalizer()
        df = pl.DataFrame({"sku": ["abc-001", "DEF-002", "  ghi  003  "]})

        result = normalizer.normalize_dataframe(df, "sku")

        assert result.df["sku"].to_list() == ["ABC-001", "DEF-002", "GHI003"]
        assert result.total_original == 3
        assert result.total_normalized == 3

    def test_detect_collisions_case(self):
        """Test detekcji kolizji typu case."""
        normalizer = SKUNormalizer()
        df = pl.DataFrame({"sku": ["ABC-001", "abc-001", "Abc-001"]})

        result = normalizer.normalize_dataframe(df, "sku")

        assert result.total_collisions == 1
        assert result.collisions[0].collision_type == "case"
        assert len(result.collisions[0].original_skus) == 3

    def test_detect_collisions_whitespace(self):
        """Test detekcji kolizji typu whitespace."""
        normalizer = SKUNormalizer()
        df = pl.DataFrame({"sku": ["ABC001", "ABC 001", "ABC  001"]})

        result = normalizer.normalize_dataframe(df, "sku")

        assert result.total_collisions == 1
        assert result.collisions[0].collision_type == "whitespace"

    def test_normalize_sku_column_helper(self):
        """Test funkcji pomocniczej normalize_sku_column."""
        df = pl.DataFrame({"sku": ["abc", "def", "ghi"]})
        result = normalize_sku_column(df, "sku")

        assert result.df["sku"].to_list() == ["ABC", "DEF", "GHI"]


# ============================================================================
# Testy integracyjne
# ============================================================================


class TestIngestIntegration:
    """Testy integracyjne dla modulu ingest."""

    def test_full_masterdata_pipeline(self):
        """Test pelnego pipeline'u dla masterdata."""
        # 1. Wczytaj plik
        df = read_file(FIXTURES_DIR / "masterdata_clean.csv")
        assert len(df) > 0

        # 2. Auto-mapowanie
        wizard = create_masterdata_wizard()
        mapping = wizard.auto_map(df.columns)
        assert mapping.is_complete

        # 3. Zastosuj mapowanie
        mapped_df = wizard.apply_mapping(df, mapping)
        assert "sku" in mapped_df.columns

        # 4. Normalizuj SKU
        norm_result = normalize_sku_column(mapped_df, "sku")
        assert norm_result.df is not None

    def test_full_orders_pipeline(self):
        """Test pelnego pipeline'u dla orders."""
        # 1. Wczytaj plik
        df = read_file(FIXTURES_DIR / "orders_clean.csv")
        assert len(df) > 0

        # 2. Auto-mapowanie
        wizard = create_orders_wizard()
        mapping = wizard.auto_map(df.columns)
        assert mapping.is_complete

        # 3. Zastosuj mapowanie
        mapped_df = wizard.apply_mapping(df, mapping)
        assert "sku" in mapped_df.columns
        assert "order_id" in mapped_df.columns

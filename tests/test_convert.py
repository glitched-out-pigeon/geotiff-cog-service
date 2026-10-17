# tests/test_convert.py
from pathlib import Path
import pytest
from rio_cogeo.cogeo import cog_validate

from app.convert import convert_to_cog

FIXTURE = Path(__file__).parent / "fixtures" / "true_color.tif"


@pytest.fixture
def output_path(tmp_path):
    return str(tmp_path / "output_cog.tif")


def test_convert_produces_valid_cog(output_path):
    result = convert_to_cog(str(FIXTURE), output_path)

    valid, errors, warnings = cog_validate(output_path)
    assert valid, f"COG validation failed: errors={errors}, warnings={warnings}"


def test_convert_returns_expected_stats(output_path):
    result = convert_to_cog(str(FIXTURE), output_path)

    assert "bounds" in result
    assert len(result["bounds"]) == 4
    assert result["original_size_mb"] > 0
    assert result["cog_size_mb"] > 0
    assert result["compression_ratio"] > 0


def test_convert_achieves_compression(output_path):
    result = convert_to_cog(str(FIXTURE), output_path)

    # float32 input should be cast to uint8 and get a real size reduction
    assert result["compression_ratio"] > 1.5


def test_output_file_exists(output_path):
    convert_to_cog(str(FIXTURE), output_path)
    assert Path(output_path).exists()
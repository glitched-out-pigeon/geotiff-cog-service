# app/convert.py
from pathlib import Path
import numpy as np
import rasterio
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles


def convert_to_cog(input_path: str, output_path: str) -> dict:
    """Convert a GeoTIFF to a Cloud Optimized GeoTIFF. Returns stats."""
    with rasterio.open(input_path) as src:
        profile = src.profile
        data = src.read()

    # Float imagery (e.g. reflectance 0-1) compresses poorly as-is;
    # casting to uint8 is what actually drives the compression ratio.
    if data.dtype.kind == "f":
        scale = 255 if data.max() <= 1.5 else 1
        data = np.clip(data * scale, 0, 255).astype("uint8")
        profile.update(dtype="uint8")
        tmp_path = str(Path(output_path).with_suffix(".tmp.tif"))
        with rasterio.open(tmp_path, "w", **profile) as dst:
            dst.write(data)
        src_for_cog = tmp_path
    else:
        src_for_cog = input_path

    dst_profile = cog_profiles.get("deflate")
    dst_profile.update(predictor=2)

    cog_translate(
        src_for_cog,
        output_path,
        dst_profile,
        in_memory=False,
        quiet=True,
        overview_level=3,
    )

    if src_for_cog != input_path:
        Path(src_for_cog).unlink()

    with rasterio.open(input_path) as src:
        bounds = src.bounds

    original_size = Path(input_path).stat().st_size
    cog_size = Path(output_path).stat().st_size

    return {
        "bounds": list(bounds),
        "original_size_mb": round(original_size / 1e6, 3),
        "cog_size_mb": round(cog_size / 1e6, 3),
        "compression_ratio": round(original_size / cog_size, 2),
    }
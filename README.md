# GeoTIFF to COG Converter & Viewer

A web service that converts raw GeoTIFF satellite imagery into Cloud
Optimized GeoTIFFs (COG) and serves them as map tiles in a browser viewer.

## What it does

1. Upload a GeoTIFF
2. Backend converts it to a COG (tiled, compressed, with zoom overviews)
   using rio-cogeo/GDAL
3. Metadata (bounds, compression ratio, status) is stored in SQLite
4. The COG is served as XYZ map tiles via titiler
5. The frontend map lets you toggle each converted file on/off as a layer

## Why COG

Raw GeoTIFFs load slowly because the whole file has to be read even to
view a small area or zoomed-out view. COG restructures the file so only
the needed tiles stream in — the same approach used by Google Earth Engine
and Sentinel Hub.

## Tech stack

- **API**: FastAPI
- **Conversion**: rasterio + rio-cogeo (GDAL under the hood)
- **Tile serving**: titiler
- **Database**: SQLite (file metadata only)
- **Frontend**: MapLibre GL JS, single HTML file
- **DevOps**: Docker, GitHub Actions CI (lint + test on push)

## Architecture
Browser --upload/view--> FastAPI API --convert--> rio-cogeo/GDAL
| |
v v
SQLite metadata <---- COG files on disk


## Running locally

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/app/` for the viewer, or
`http://127.0.0.1:8000/docs` for the API.

## Running with Docker

```bash
docker build -t geotiff-cog-service .
docker run -p 8000:8000 geotiff-cog-service
```

## Testing

```bash
pytest tests/ -v
```

## Compression results

Tested on a Sentinel-2 L2A true-color GeoTIFF (Copernicus Data Space
Ecosystem): float32 reflectance data cast to uint8 before COG conversion
achieves a 3.3x size reduction versus the raw float32 input, in addition
to the tiling/overview benefits COG provides regardless of size.

## API endpoints

| Method | Path | Description |
|---|---|---|
| POST | /upload | Upload a GeoTIFF, starts async conversion |
| GET | /status/{layer_id} | Conversion status and stats |
| GET | /layers | List all converted layers |
| GET | /cog/tiles/... | Tile endpoint (titiler) |
| GET | /app/ | Web viewer |

## Data source

Test imagery from the [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/)
(Sentinel-2 L2A), free and open for any use.
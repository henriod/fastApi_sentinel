import geojson
import geopandas as gpd
import numpy as np
import pandas as pd
from fastapi import FastAPI, UploadFile
from geojson import Polygon
from datetime import date
from sentinelhub import (
    CRS,
    BBox,
    DataCollection,
    Geometry,
    SentinelHubStatistical,
)
from config import config

app = FastAPI()
config.save()


@app.get("/")
async def root():
    return {"message": "Hello World"}


"""
Endpoint function to get ndvi statistics when provide with
@start_date
@End_date
@Geojson feature
No Validation yet(check file extension, geojson geometries are valid, crs not wgs84, etc)
We are using a get method here
"""


@app.get("/ndvi_statistical/")
async def get_ndvi_statistics(
    file: UploadFile,
    start_datetime: date = "2020-10-30",
    end_datetime: date = "2020-12-10",
):

    betsiboka_bbox = BBox([46.16, -16.15, 46.51, -15.58], CRS.WGS84)

    rgb_evalscript = """
    //VERSION=3

    function setup() {
    return {
        input: [
        {
            bands: [
            "B02",
            "B03",
            "B04",
            "dataMask"
            ]
        }
        ],
        output: [
        {
            id: "rgb",
            bands: ["R", "G", "B"]
        },
        {
            id: "dataMask",
            bands: 1
        }
        ]
    }
    }

    function evaluatePixel(samples) {
        return {
        rgb: [samples.B04, samples.B03, samples.B02],
        dataMask: [samples.dataMask]
        };
    }
    """

    rgb_request = SentinelHubStatistical(
        aggregation=SentinelHubStatistical.aggregation(
            evalscript=rgb_evalscript,
            time_interval=(start_datetime, end_datetime),
            aggregation_interval="P1D",
            size=(631, 1047),
        ),
        input_data=[
            SentinelHubStatistical.input_data(DataCollection.SENTINEL2_L1C, maxcc=0.8)
        ],
        bbox=betsiboka_bbox,
        config=config,
    )
    rgb_stats = rgb_request.get_data()[0]

    return rgb_stats


"""
Endpoint function to get ndvi statistics when provide with
@start_date
@End_date
@Geojson file
No Validation yet(check file extension, geojson geometries are valid, geojson geometry is either Polygon or multipolygon,crs is wgs84, etc)
We are Using post method due to multipart form submission for security purposes
"""


@app.post("/ndvi_statistical/")
def get_ndvi_statistics_pst(
    file: UploadFile,
    start_datetime: date = "2020-05-30",
    end_datetime: date = "2020-06-07",
):
    yearly_time_interval = start_datetime, end_datetime
    polygons_gdf = gpd.read_file(file.file)
    ndvi_evalscript = """
    //VERSION=3

    function setup() {
    return {
        input: [
        {
            bands: [
            "B04",
            "B08",
            "dataMask"
            ]
        }
        ],
        output: [
        {
            id: "ndvi",
            bands: 1
        },
        {
            id: "dataMask",
            bands: 1
        }
        ]
    }
    }

    function evaluatePixel(samples) {
        return {
        ndvi: [index(samples.B08, samples.B04)],
        dataMask: [samples.dataMask]
        };
    }
    """

    aggregation = SentinelHubStatistical.aggregation(
        evalscript=ndvi_evalscript,
        time_interval=yearly_time_interval,
        aggregation_interval="P1D",
        resolution=(10, 10),
    )

    input_data = SentinelHubStatistical.input_data(DataCollection.SENTINEL2_L2A)

    histogram_calculations = {
        "ndvi": {
            "histograms": {"default": {"nBins": 20, "lowEdge": -1.0, "highEdge": 1.0}}
        }
    }

    geo_shapes = []

    for geo_shape in polygons_gdf.geometry.values:
        geo_shapes.append(geo_shape)

    # Only running for first geo_shape in the array
    request = SentinelHubStatistical(
        aggregation=aggregation,
        input_data=[input_data],
        geometry=Geometry(geo_shapes[0], crs=CRS.WGS84),
        calculations=histogram_calculations,
        config=config,
    )
    return request.get_data()[0]

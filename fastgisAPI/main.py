import geojson
from geojson import Feature, Polygon, MultiPolygon
import geopandas as gpd
from fastapi import FastAPI, UploadFile, HTTPException
from datetime import date
from sentinelhub import (
    CRS,
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
@Geojson feature as string
Validation check if the feature is valid before proceeding 
We are using a get method here
"""


@app.get("/ndvi_statistical/")
async def get_ndvi_statistics(
    geojson_feature: str = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "coordinates": [
                [
                    [12.779091544855845, 42.0539623314115],
                    [12.777959229213792, 42.052661231622324],
                    [12.779972804088118, 42.05126118804466],
                    [12.781509884167576, 42.05193458240959],
                    [12.781760652469302, 42.05393907756118],
                    [12.779091544855845, 42.0539623314115],
                ]
            ],
            "type": "Polygon",
        },
    },
    start_datetime: date = "2020-10-30",
    end_datetime: date = "2020-12-10",
):
    # Load added string as geojson
    try:
        geojson_object = geojson.loads(geojson_feature)
        # Check if the data is a valid geojson
        if geojson_object.is_valid:
            # prepare a Geometry object to be used by sentinel hub librabry
            feature = Geometry(geojson_object["geometry"], crs=CRS.WGS84)
            date_range = start_datetime, end_datetime
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
                time_interval=date_range,
                aggregation_interval="P1D",
                resolution=(10, 10),
            )

            input_data = SentinelHubStatistical.input_data(DataCollection.SENTINEL2_L2A)

            histogram_calculations = {
                "ndvi": {
                    "histograms": {
                        "default": {"nBins": 20, "lowEdge": -1.0, "highEdge": 1.0}
                    }
                }
            }

            request = SentinelHubStatistical(
                aggregation=aggregation,
                input_data=[input_data],
                geometry=feature,
                calculations=histogram_calculations,
                config=config,
            )
            rgb_stats = request.get_data()[0]
            return rgb_stats
        raise HTTPException(
            status_code=404, detail="The Geojson Feature provide is invalid"
        )
    except:
        raise HTTPException(
            status_code=404, detail="The data could not be decoded to geojson"
        )


"""
Endpoint function to get ndvi statistics when provide with
@start_date
@end_date
@Geojson feature as geojson file
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

import json
import geojson
from geojson import Feature, Polygon, MultiPolygon
import geopandas as gpd
from fastapi import FastAPI, UploadFile, HTTPException
from datetime import date
from sentinelhub import CRS, DataCollection, Geometry, SentinelHubStatistical, BBox
from config import config

app = FastAPI()
config.save()
if config.sh_client_id == "" or config.sh_client_secret == "":
    print(
        "Warning! To use Sentinel Hub services, please provide the credentials (client ID and client secret)."
    )


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
                    [74.068086, 18.33446],
                    [74.069344, 18.338355],
                    [74.067003, 18.338482],
                    [74.064839, 18.337239],
                    [74.064653, 18.336789],
                    [74.06388, 18.335184],
                    [74.068086, 18.33446],
                ]
            ],
            "type": "Polygon",
        },
    },
    start_datetime: date = "2020-10-30",
    end_datetime: date = "2020-12-10",
):
    # Load added string as geojson
    bbox = BBox(
        [
            [36.398822317698006, -0.6942581416901561],
            [36.407679926367024, -0.6942581416901561],
        ],
        crs=CRS.WGS84,
    )
    try:
        geojson_object = geojson.loads(geojson_feature)
        # Check if the data is a valid geojson
    except:
        raise HTTPException(
            status_code=404, detail="The data could not be decoded to geojson"
        )
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

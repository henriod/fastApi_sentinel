from fastapi import FastAPI
from sentinelhub import WmsRequest, MimeType, CRS, BBox

app = FastAPI()


@app.post("/ndvi")
def get_ndvi(
    start_date: str,
    end_date: str,
    feature: dict = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "coordinates": [
                [
                    [12.852656984297596, 42.39010455390968],
                    [12.852656984297596, 42.38773099740453],
                    [12.8571264546014, 42.38773099740453],
                    [12.8571264546014, 42.39010455390968],
                    [12.852656984297596, 42.39010455390968],
                ]
            ],
            "type": "Polygon",
        },
    },
):
    bbox = BBox(feature["geometry"]["coordinates"], crs=CRS.WGS84)
    wms_request = WmsRequest(
        layer="TRUE-COLOR-S2-L1C",
        bbox=bbox,
        time=(start_date, end_date),
        width=512,
        height=856,
        instance_id="38286c97-9d47-4e96-b114-f2cb8342c67e",
    )
    ndvi_image = wms_request.get_data(data_folder=None, save_data=False)
    ndvi_statistics = ndvi_image.get_statistics()
    return ndvi_statistics


"""
In this example, the get_ndvi function takes a GeoJSON feature, represented as a dictionary, and two strings representing the start and end dates for the date range. It then uses the BBox class from the Sentinel Hub package to create a bounding box object from the coordinates in the GeoJSON feature.

Next, it creates a WmsRequest object, which is used to request data from the Sentinel Hub API. The WmsRequest object is configured with the desired layer, bounding box, date range, and other parameters.

The WmsRequest object is then used to retrieve the NDVI data for the specified region and time period. The data is returned as an Image object, which can be used to calculate statistics for the NDVI values. The Image object's get_statistics method is called to calculate the statistics, and the result is returned from the get_ndvi function.

You will need to replace YOUR_SENTINEL_HUB_INSTANCE_ID in the code above with your own Sentinel Hub instance ID.

I hope this helps! Let me know if you have any other questions.
"""

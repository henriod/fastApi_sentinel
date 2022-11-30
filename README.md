# FastAPI Function For NDVI statistics

This a repo to test the skill of integrating The sentinelhub Python package with FastAPI to get statistics from ndvi data

## Installation

Create and activate python virtual environment then,

```bash
pip install -r requirements.tx
```

Create a '.env' file in the fastgisAPI/ directory and populate with correct sentinel hub cridentials

```sh
INSTANCE_ID=<your id>
SH_CLIENT_ID=<your sh client id>
SH_CLIENT_SECRET=<your sh client secret>
```

## Usage

To run the application

```bash
uvicorn main:app --reload
```

Then visit http://127.0.0.1:8000/docs \
and test the end-points

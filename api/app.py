import uvicorn
import os
import jsonref
import json

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.encoders import jsonable_encoder
import motor.motor_asyncio
from dotenv import load_dotenv

description = """
PatientConnect API helps developers for hospital management
systems to introduce capability to query and share patient visit data
from other facilities thus minimizing siloing of medical information.

It has two main routes

# Users

Developers will be able to:

* **Sign up their hospitals**
* **Log in to the api**

# Patients

Developers will be able to:

* **Search for a patient's previous visits**
* **Post a patient's current visit**
"""

app = FastAPI()
load_dotenv(os.path.join((os.path.dirname(__file__)), '.env'))

client  = motor.motor_asyncio.AsyncIOMotorClient(os.environ.get("MONGO_URI"))
db = client[str(os.environ.get("DATABASE"))]

from .users import user_routes
from .patients import patient_routes

app.include_router(user_routes.router, tags=['users'])
app.include_router(patient_routes.patient_router, tags=['patients'])
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="PatientConnect API",
        description=description,
        summary="Share medical information seamlessly",
        version="0.0.1",
        contact={
            "name": "Gaceri Gikonyo",
            "email": "patientconnect24@gmail.com",
        },
        license_info={
            "name": "Apache 2.0",
            "identifier": "MIT",
        },
        routes=app.routes,
    )
    if "components" in openapi_schema:
        dereferenced_schema = jsonref.loads(json.dumps(openapi_schema), lazy_load=False)
        openapi_schema["components"] = jsonable_encoder(dereferenced_schema["components"])
        for schema_name in openapi_schema["components"]["schemas"].copy().keys():
            schema = openapi_schema["components"]["schemas"][schema_name]
            hide = schema.get("hidden", False)
            if hide:
                # print(f"Removing {schema_name} as it is hidden")
                del openapi_schema["components"]["schemas"][schema_name]
                continue
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

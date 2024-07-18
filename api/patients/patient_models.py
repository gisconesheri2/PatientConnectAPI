from pydantic import BaseModel, ConfigDict, field_serializer, EmailStr, Field, field_validator
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated, Literal
from typing import List, Optional
from decimal import Decimal

from bson import ObjectId

import email_validator

email_validator.TEST_ENVIRONMENT = True

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]

class VisitSearch(BaseModel):
    """
    Model for searching for patients within the app
    """
    id_number: int
    name: str
    is_child: bool
    parent_name: Optional[str] = Field(validate_default=True, default=None)

    @field_validator('parent_name')
    @classmethod
    def get_parent_name(cls, parent_name, values):
        print(values.data)
        print(parent_name)
        if values.data['is_child'] is True and (parent_name is None or parent_name == 'null'):
            raise ValueError('Must supply a parent name for a child')
        return parent_name
    
    # store name and patient_name in title case
    @field_serializer('name', 'parent_name')
    def serialize_name(self, name: str, _info):
        return name.title()
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "id_number": 12341234,
                "name": "John doe",
                "is_child": "true",
                "parent_name": "Jane Doe"
            }
        },
    )

class PatientBio(BaseModel):
    """
    Model for a patient's bio details
    """
    name: str
    age: float = Field(gt=0.0, lt=120.0)
    gender: Literal['male', 'female']

    # store name and gender in title case
    @field_serializer('name')
    def serialize_name(self, name: str, _info):
        return name.title()
    
    class Config:
        json_schema_extra = {"hidden": True}

class PatientVitals(BaseModel):
    """
    Model for a patient's vitals during a specific visit
    """
    blood_pressure: str
    weight: float
    temperature: float

    class Config:
        json_schema_extra = {"hidden": True}

class TestReport(BaseModel):
    """
    Model for reporting lab tests and investigation reports
    """
    test_name: str
    test_results: str

    class Config:
        json_schema_extra = {"hidden": True}

class MedicationDetails(BaseModel):
    """
    Model for reporting medication prescribed on the visit
    """
    medication_name: str
    medication_dosage: int
    medication_frequency: int
    medication_duration: int
    medication_instructions: str | None = None

    class Config:
        json_schema_extra = {"hidden": True}

class VisitDetails(BaseModel):
    """
    Model collating and presenting all the information that pertains to
    a single visit
    """
    facility_name: Optional[str] = None
    facility_type: Optional[str] = None
    visit_date: Optional[str] = None
    patient_bio: PatientBio
    visit_vitals: PatientVitals
    visit_clinical_notes: str
    visit_labs: Optional[List[TestReport]]
    visit_investigations: Optional[List[TestReport]]
    visit_medication: Optional[List[MedicationDetails]]

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "hidden": True,
            "example": {
                "facility_name": "Test Hospital",
                "visit_date": "Tue 16 Jul 2024, 03:51PM",
                "patient_bio": {
                    "name": "Jane Doe",
                    "age": 0.1,
                    "gender": "male",
                    },
                "visit_vitals": {
                    "blood_pressure": "127/87",
                    "weight": 10.3,
                    "temperature": 36.2
                },
                "visit_clinical_notes": "Patient presented with ...",
                "visit_labs": [
                    {"test_name": "test one", "test_results": "test one results"},
                    {"test_name": "test two", "test_results": "test two results"}
                ],
                "visit_investigations": [
                    {"test_name": "investigation one", "test_results": "investigation one result"},
                    {"test_name": "investigation two results", "test_results": "investigation two results"}
                ],
                "visit_medication": [
                    {
                        "medication_name": "medication name, strength, dosage form",
                        "medication_dosage": 2,
                        "medication_frequency": 3,
                        "medication_duration": 5,
                        "medication_instructions": "special instruction"  
                    },
                    {
                        "medication_name": "medication name, strength, dosage form",
                        "medication_dosage": 1,
                        "medication_frequency": 1,
                        "medication_duration": 30
                    }
                ]
            }
        },
    )

class VisitResponse(BaseModel):
  """
  Model to set response validation for /patients/visit route
  """
  visits: List[VisitDetails | None]

class VisitUpload(BaseModel):
    """
    Model to validate data posted to the  patients/visit route
    """
    patient_search: VisitSearch
    visit_details: VisitDetails

class Child(BaseModel):
    """
    Model to represent pediatric patients
    """
    name: str
    visits: Optional[List[VisitDetails]] = []

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "name": "John doe",
                "visits": []
            }
        },
    )

class Patient(BaseModel):
    """
    Model to represent an adult patient
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    id_number: int
    name: str
    dependents: Optional[List[Child]] = []
    visits: Optional[List[VisitDetails]] = []

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "id_number": 1234124,
                "name": "John doe",
                "dependents": [],
                "visits": []
            }
        },
    )

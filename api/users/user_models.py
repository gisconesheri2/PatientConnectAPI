from pydantic import BaseModel, ConfigDict, field_serializer, EmailStr, Field
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated
from typing import Optional

import email_validator

email_validator.TEST_ENVIRONMENT = True

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]

class UserRegistration(BaseModel):
    """Schema to validate JSON data submitted to register a user"""

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: EmailStr = Field(...)
    password: str = Field(...)
    facility_name: str = Field(...)
    facility_type: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "email": "test@example.com",
                "password": "password",
                "facility_name": "Test Hospital"
            }
        },
    )

    # store facility_name and facility_type in title case
    @field_serializer('facility_name')
    def serialize_name(self, name: str, _info):
        return name.title()
    
class User(BaseModel):
    """Pydantic schema to store authenticated user details"""
    email: str
    facility_name: str
    facility_type: str

    # store facility_name and facility_type in title case
    @field_serializer('facility_name', 'facility_type')
    def serialize_name(self, name: str, _info):
        return name.title()
    
    class Config:
        json_schema_extra = {"hidden": True}

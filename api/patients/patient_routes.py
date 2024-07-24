from typing import Annotated, List

from fastapi import Body, Depends, APIRouter
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

from ..app import db
from .patient_models import Patient, Child, VisitSearch,\
    VisitUpload, VisitDetails, VisitResponse
from ..users.user_models import User

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
patient_router = APIRouter()
patients_collection = db[os.environ.get("PATIENT_COLLECTION")]

from ..dependencies.authenticate import get_current_active_user

@patient_router.post('/patients/search',
    summary="Search for a patient's previous visits",
    response_model=VisitResponse)
async def get_patient(
        current_user: Annotated[User, Depends(get_current_active_user)],
        patient: VisitSearch = Body(...),) -> dict[str, List[VisitDetails]]:
    """Search for patient in the database to get previous visits.
    Previous visits posted by the current facility will not be shown
    You need to supply the following details:

        "visit_search": {
            "id_number": INTEGER,
            "is_child": STRING ("true" or "false"),
            "name": STRING,
            "parent_name": STRING (Optional, only required if is_child is "true")
            }

    Returns:

        An empty array if patient is not registered or has no visits recorded
        An ARRAY of visit details objects in the format
            {
                "facility_name": STRING ("facility the patient visited"),
                "visit_date": STRING,
                "patient_bio": {
                    "age": FLOAT,
                    "gender": STRING ("male" or "female"),
                    "name": STRING
                },
                "visit_vitals": {
                    "blood_pressure": STRING (format: "systolic/diastolic"),
                    "temperature": FLOAT,
                    "weight": FLOAT
                },
                "visit_clinical_notes": STRING,
                "visit_investigations": ARRAY of OBJECTS (Optional),  // See details below
                "visit_labs": ARRAY of OBJECTS (Optional),             // See details below
                "visit_medication": ARRAY of OBJECTS (Optional),     // See details below
            }
        Note:
            facility_name is the facility tied to the visit
            visit_date is derived from naive datetime object with strftime format: "%a %d %b %Y, %I:%M%p"

        Details of Optional fields:
            visit_investigations:
                This array contains objects representing test results from various investigations.
                Each object has the following properties:
                    test_name: STRING - Name of the investigation performed (e.g., "chest xray").
                    test_results: STRING - Description of the test results.
            visit_labs:
                This array contains objects representing laboratory test results.
                Each object has the following properties:
                    test_name: STRING - Name of the laboratory test performed (e.g., "blood glucose").
                    test_results: STRING - Description of the test results.
            visit_medication:
                This array contains objects representing medications prescribed during the visit.
                Each object has the following properties:
                    medication_name: STRING - Name of the medication prescribed.
                    medication_dosage: INTEGER - Dosage of the medication.
                    medication_frequency: INTEGER - Frequency of medication administration (e.g., how many times per day).
                    medication_duration: INTEGER - Duration of medication prescription (e.g., number of days).
                    medication_instructions: STRING (Optional) - Special instructions for taking the medication.
        """
    if patient.is_child:
        patient_db = await patients_collection.find_one(
            filter={'id_number': patient.id_number},
            projection={'dependents': 1, '_id': 0})
        if patient_db is not None:
            for child in patient_db['dependents']:
                name1_parts = set(name.lower() for name in child['name'].split())
                name2_parts = set(name.lower() for name in patient.name.split())
                if name1_parts == name2_parts:
                    other_facility_visits = []
                    for visit in child['visits']:
                        if visit['facility_name'] != current_user.facility_name:
                            other_facility_visits.append(visit)
                    print('visits for a child retrived')
                    return {'visits': other_facility_visits}
    else:
        patient_db = await patients_collection.find_one(
            filter={'id_number': patient.id_number},
            projection={'visits': 1, '_id': 0})
        other_facility_visits = []
        if patient_db is not None:
            for visit in patient_db['visits']:
                if visit['facility_name'] != current_user.facility_name:
                    other_facility_visits.append(visit)
            print('visits for an adult retrieved')
            return {'visits': other_facility_visits}
    print('visits for a non existent patient')
    return {'visits': []}


@patient_router.post('/patients/visit',
    summary="Post a patient's current visit",
    status_code=201)
async def add_visit(
        current_user: Annotated[User, Depends(get_current_active_user)],
        visit: VisitUpload = Body(...),):
    """
    Post a patient's visit in the database. You need to supply a JSON object:

        {
            "patient_search": {
                "id_number": INTEGER,
                "is_child": STRING ("true" or "false"),
                "name": STRING,
                "parent_name": STRING (Optional, only required if is_child is "true")
            },
            "visit_details": {
                "patient_bio": {
                    "age": FLOAT,
                    "gender": STRING ("male" or "female"),
                    "name": STRING
                },
                "visit_vitals": {
                    "blood_pressure": STRING (format: "systolic/diastolic"),
                    "temperature": FLOAT,
                    "weight": FLOAT
                },
                "visit_clinical_notes": STRING,
                "visit_investigations": ARRAY of OBJECTS (Optional),  // See details below
                "visit_labs": ARRAY of OBJECTS (Optional),             // See details below
                "visit_medication": ARRAY of OBJECTS (Optional),     // See details below
            }
        }

        Notes:

            * All fields are mandatory unless explicitly marked as optional.
            * id_number is the national identity card number.
            * age should be a decimal value representing the patient's age (e.g., 3.2 for 3 years and 2 months).
            * blood_pressure should be formatted as "systolic/diastolic" (e.g., "127/87").
            * visit_investigations, visit_labs, and visit_medication are optional arrays. You can include them if you have relevant test results or medication information to submit.

        Details of Optional Fields:  
            visit_investigations:
                This array contains objects representing test results from various investigations.
                Each object should have the following properties:
                    test_name: STRING - Name of the investigation performed (e.g., "chest xray").
                    test_results: STRING - Description of the test results.
            visit_labs:
                This array contains objects representing laboratory test results.
                Each object should have the following properties:
                    test_name: STRING - Name of the laboratory test performed (e.g., "blood glucose").
                    test_results: STRING - Description of the test results.
            visit_medication:
                This array contains objects representing medications prescribed during the visit.
                Each object should have the following properties:
                    medication_name: STRING - Name of the medication prescribed.
                    medication_dosage: INTEGER - Dosage of the medication.
                    medication_frequency: INTEGER - Frequency of medication administration (e.g., how many times per day).
                    medication_duration: INTEGER - Duration of medication prescription (e.g., number of days).
                    medication_instructions: STRING (Optional) - Special instructions for taking the medication.

    Returns:  

        Success:
            StatusCode: 201
            Message: {'status': 'visit posted successfully'}
        Failure:
            StatusCode: ERR_CODE
            Message: description of the issue.
    """

    patient = visit.patient_search
    visit_details = visit.visit_details
    visit_details.facility_name = current_user.facility_name
    visit_details.facility_type = current_user.facility_type
    visit_details.visit_date = datetime.now().strftime("%a %d %b %Y, %I:%M%p") 

    if patient.is_child:
        update_child = False
        parent_db = await patients_collection.find_one(
            filter={'id_number': patient.id_number},
            projection={'id_number': 1, '_id': 0})
        # check if parent exists in the database, if not add them plus child
        if not parent_db:
            child = Child(name=patient.name,
                          visits=[visit_details])
            parent = Patient(
                id_number=patient.id_number,
                name=patient.parent_name,
                dependents=[child]
                )
            await patients_collection.insert_one(parent.model_dump())
            print("inserted new child and parent")
            update_child = True
        else:
        #parent is in the database
            parent_dependents= await patients_collection.find_one(
            filter={'id_number': patient.id_number},
            projection={'dependents': 1, '_id': 0})
            #check if there are any dependents,if not create a new Child and add them
            if len(parent_dependents['dependents']) == 0:
                child = Child(name=patient.name,
                          visits=[visit_details])
                await patients_collection.update_one(
                    filter={'id_number': patient.id_number},
                    update={ '$push': { 'dependents': child.model_dump() } }
                )
                print("inserted new child for parents with no dependents")
                update_child = True
            else:
                # if dependant available, find the correct one and update their visits array
                for child in parent_dependents['dependents']:
                    name1_parts = set(name.lower() for name in child['name'].split())
                    name2_parts = set(name.lower() for name in patient.name.split())
                    if name1_parts == name2_parts:
                        await patients_collection.update_one(
                            filter={'id_number': patient.id_number, 'dependents.name': child['name']},
                            update={ '$push': {
                                'dependents.$.visits': visit_details.model_dump()}})
                        print("updated old child visit records")
                        update_child = True
                        break
        # if parent exists and child is new, add a new child
        if not update_child:
            child =  Child(name=patient.name,
                           visits=[visit_details])
            await patients_collection.update_one(
                            filter={'id_number': patient.id_number},
                            update={ '$push': {
                                'dependents': child.model_dump()}})
            print("inserted a new child to a parent with children")
    else:
        # update details for an adult patient
        patient_db = await patients_collection.find_one(
            filter={'id_number': patient.id_number},
            projection={'id_number': 1, '_id': 0})
        # check if patient exists in the database, if not add them
        if not patient_db:
            patient = Patient(name=patient.name,
                              id_number=patient.id_number,
                              visits=[visit_details])
            await patients_collection.insert_one(patient.model_dump())
            print("inserted new parent without children")
        else:
            await patients_collection.update_one(
                filter={'id_number': patient.id_number},
                update={ '$push': {
                                'visits': visit_details.model_dump()}})
            print("updated old parent without children")
    return {'status': 'Visit posted successfully'}

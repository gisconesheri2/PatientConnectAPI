
# PATIENTCONNECT API

PatientConnect API helps developers for hospital management
systems to introduce capability to query and share patient visit data
from other facilities thus minimizing siloing of medical information.

It has two main routes

## Users

Developers will be able to:

* **Sign up their hospitals**
* **Log in to the api**

## Patients

Developers will be able to:

* **Search for a patient's previous visits**
* **Post a patient's current visit**

## USER REGISTRATION

To register for the service, you can do this:

```python
import requests

user = {
    'email': '<test@test.com>',
    'password': 'test',
    'facility_name': 'Test Hospital', #Must be exact name registered by regulatory authority including the town if used in registration eg Test Pharmacy (Nairobi)
}

# send a post request

r = requests.post('<https://api.patientconnect.tech/users/register>', json=user)

```

## USER LOGIN

```python

user = {
    'username': '<test344@test.com>',
    'password': 'test',
}

r_login = requests.post('<https://api.patientconnect.tech/users/login>', data=user)

# will return a JSON Object with an access token
access_token = r_login.json()['access_token']

# create an Authorization header with the access token
headers = {"Authorization":f"Bearer {access_token}"}

```

The access token is valid for 24 hours. The developer can set up a scheduled task to get a fresh access token daily. The token should be sent with an Authorization header as shown above. This header should be included in when accessing the _/patients_ routes.

## SEARCH FOR PATIENT VISITS

There are two formats to search for patients depending on age.

### Pediatric Patients

For pediatric patients, you have to include the parent's ID number and name in the query object and set the _is_child_ property to true.
For example:

```python
# include the Authorization header with the access token generated during login
headers = {"Authorization":f"Bearer {access_token}"}

# create a patient query object
pediatric_patient = {
  "id_number": 12341234, # parent's ID number
  "name": "John doe",
  "is_child": True,
  "parent_name": "Jane Doe"
}

# fire off a search
patient_visits = requests.post('<https://api.patientconnect.tech/patients/search>', headers=headers, json=pediatric_patient)

# get the list of patient visits
visit_list = patient_visits.json()['visits']
```

### Adult Patients

For adult patients, set the is_child property to false and just include the name and ID number properties.
For example:

```python
# include the Authorization header with the access token generated during login
headers = {"Authorization":f"Bearer {access_token}"}

# create a patient query object
adult_patient = {
  "id_number": 12341234,
  "name": "John doe",
  "is_child": false,
}

# fire off a search
patient_visits = requests.post('<https://api.patientconnect.tech/patients/search>', headers=headers, json=adult_patient)

# get the list of patient visits
visit_list = patient_visits.json()['visits']
```

The returned visits object is similar in both cases. More info on this object can be found in the [docs](https://api.patientconnect.tech/docs)

## POST PATIENT VISIT

To post a patient visit, you need to include a patient search parameter whose details mirror what you send when searching for a patient visits depending on age, see here for [pediatric patients](#pediatric-patients) and [adult patients](#adult-patients)

For instance to post a child's visit:

```python
# include the Authorization header with the access token generated during login
headers = {"Authorization":f"Bearer {access_token}"}

# create an object to post the patient's current visit
child_visit = {
  "patient_search": {
    "id_number": 12341234,
    "is_child": "true",
    "name": "John doe",
    "parent_name": "Jane Doe"
  },
  "visit_details": {
    "patient_bio": {
      "age": 0.1,
      "gender": "male",
      "name": "Jane Doe"
    },
    "visit_clinical_notes": "Patient presented with ...",
    "visit_date": "Tue 16 Jul 2024, 03:51PM",
    "visit_investigations": [
      {
        "test_name": "investigation one",
        "test_results": "investigation one result"
      },
      {
        "test_name": "investigation two results",
        "test_results": "investigation two results"
      }
    ],
    "visit_labs": [
      {
        "test_name": "test one",
        "test_results": "test one results"
      },
      {
        "test_name": "test two",
        "test_results": "test two results"
      }
    ],
    "visit_medication": [
      {
        "medication_dosage": 2,
        "medication_duration": 5,
        "medication_frequency": 3,
        "medication_instructions": "special instruction",
        "medication_name": "medication name, strength, dosage form"
      },
      {
        "medication_dosage": 1,
        "medication_duration": 30,
        "medication_frequency": 1,
        "medication_name": "medication name, strength, dosage form"
      }
    ],
    "visit_vitals": {
      "blood_pressure": "127/87",
      "temperature": 36.2,
      "weight": 10.3
    }
  }
}

# post the visit
patient_visits = requests.post('<https://api.patientconnect.tech/patients/visit>', headers=headers, json=child_patient)
```

More info on the data needed to post a visit can be found in the [docs](https://api.patientconnect.tech/docs)

## FUTURE CONSIDERATIONS

1. Implement a pagination system for visit search results based on number of records needed as well as a filter by date feature.
2. Pull healthcare facility registration data from KMPDC (Currently only using data from PPB) to widen scope of potential users.
3. Scale up deployment

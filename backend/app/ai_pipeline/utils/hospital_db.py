from app.ai_pipeline.models.pipeline import HospitalCandidate


MOCK_HOSPITALS = [
    HospitalCandidate(
        id="HOSP001",
        name="Apollo Trauma Center",
        latitude=12.9724,
        longitude=77.5958,
        trauma_level=1,
        available_beds=12,
        ventilators=7,
    ),
    HospitalCandidate(
        id="HOSP002",
        name="City General Emergency Hospital",
        latitude=12.9826,
        longitude=77.6016,
        trauma_level=2,
        available_beds=18,
        ventilators=3,
    ),
    HospitalCandidate(
        id="HOSP003",
        name="Metro SuperSpecialty Hospital",
        latitude=12.9916,
        longitude=77.6246,
        trauma_level=1,
        available_beds=4,
        ventilators=10,
    ),
    HospitalCandidate(
        id="HOSP004",
        name="St. Jude Urgent Care",
        latitude=12.9616,
        longitude=77.5846,
        trauma_level=3,
        available_beds=8,
        ventilators=1,
    ),
]

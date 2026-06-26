# JeevanSetu

JeevanSetu is an accident detection and emergency response system with a Flutter frontend, FastAPI backend, live tracking, notifications, SOS dispatch, hospital recommendation, volunteer discovery, and an AI pipeline for transforming raw sensor data into emergency decisions.

## Backend AI Pipeline

The AI pipeline lives in `backend/app/ai_pipeline` and is integrated under the existing FastAPI `/api/ai` router.

```text
backend/app/ai_pipeline/
  accident_detection/       Rule-based accident engine, ML-ready boundary
  api_routes/               FastAPI pipeline endpoints
  feature_extraction/       Sensor feature calculations
  hospital_recommendation/  Trauma/ETA/distance/availability ranking
  models/                   Pydantic request/response schemas
  response_builder/         Final AI response assembly
  severity_prediction/      Minor/moderate/critical scoring
  user_verification/        15-second incident verification request
  utils/                    Geo helpers and mock hospital database
  validation/               Sensor data validation and cleaning
```

## Pipeline Flow

1. Accept accelerometer, gyroscope, GPS, speed, and timestamp data.
2. Validate coordinates, speed, required sensor fields, and timestamps.
3. Extract impact force, speed drop, acceleration magnitude, gyroscope magnitude, orientation change, and response delay.
4. Detect accident probability with rule-based logic.
5. Create a 15-second user verification request.
6. Predict severity as `minor`, `moderate`, or `critical`.
7. Rank hospitals using:

```text
Score = 0.40 * Trauma Capability + 0.30 * ETA + 0.20 * Distance + 0.10 * Availability
```

8. Build the final response payload.
9. Escalate through existing backend services for accident reporting, SOS, notifications, live tracking, dashboard persistence, and nearby volunteers.

## Endpoints

All endpoints require the existing bearer token auth.

```text
POST /api/ai/pipeline/process
POST /api/ai/pipeline/{incident_id}/verify
POST /api/ai/pipeline/{incident_id}/escalate
GET  /api/ai/pipeline/{incident_id}
```

The legacy severity endpoint is still available:

```text
POST /api/ai/severity
```

## Sample Request

```json
{
  "sensor_data": {
    "accelerometer": { "x": 8.0, "y": 2.0, "z": 1.0 },
    "gyroscope": { "x": 4.0, "y": 1.5, "z": 0.5 },
    "gps": { "latitude": 12.971598, "longitude": 77.594566, "accuracy_m": 4.5 },
    "speed": 12.0,
    "previous_speed": 82.0,
    "timestamp": "2026-06-25T16:30:00Z",
    "previous_orientation": { "x": 0.0, "y": 0.0, "z": 0.0 },
    "current_orientation": { "x": 45.0, "y": 10.0, "z": 5.0 },
    "device_id": "device-001"
  },
  "response_delay": 15.0,
  "auto_escalate": false
}
```

## Sample Response

```json
{
  "response": {
    "incident_id": "INC001",
    "accident": true,
    "confidence": 0.99,
    "severity": "critical",
    "score": 78,
    "hospital": "Apollo Trauma Center",
    "eta": "1 min",
    "verification": {
      "incident_id": "INC001",
      "message": "Possible accident detected. Confirm you are safe within 15 seconds to cancel escalation.",
      "expires_at": "2026-06-25T16:30:15Z",
      "timeout_seconds": 15
    }
  }
}
```

To cancel a false alarm:

```json
POST /api/ai/pipeline/INC001/verify
{ "safe": true, "response_delay": 4.2 }
```

To continue emergency workflow:

```json
POST /api/ai/pipeline/INC001/verify
{ "safe": false, "response_delay": 15.0 }
```

After the timer expires, the frontend can call:

```text
POST /api/ai/pipeline/INC001/escalate
```

## Development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest tests/test_ai_pipeline.py
```

Run the Flutter app in demo mode:

```bash
cd jeevansetu_app
flutter pub get
flutter run
```

Run the Flutter app against the backend AI pipeline:

```bash
flutter run \
  --dart-define=JEEVANSETU_API_BASE_URL=http://localhost:8000/api \
  --dart-define=JEEVANSETU_AUTH_TOKEN=<ACCESS_TOKEN>
```

Without `JEEVANSETU_AUTH_TOKEN`, the emergency flow keeps using the local demo fallback. With a valid backend token, the accident alert flow calls `POST /api/ai/pipeline/process`, then confirms safety or escalates through `POST /api/ai/pipeline/{incident_id}/verify`.

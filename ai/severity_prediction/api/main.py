from fastapi import FastAPI, HTTPException
import joblib
import os
import pandas as pd
from contextlib import asynccontextmanager

from ai.severity_prediction.api.schemas import SeverityPredictionRequest, SeverityPredictionResponse
import sys

# Ensure parent directory and workspace root are in path
workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(workspace_root)
severity_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(severity_dir)

from ai.severity_prediction.severity_features import engineer_features
from ai.hospital_recommendation.hospital_recommender import HospitalRecommender

# Global variables to hold the loaded model and label encoder
model = None
label_encoder = None
hospital_recommender = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, label_encoder, hospital_recommender
    base_dir = r"c:\Users\HP\JeevanSetuN"
    model_path = os.path.join(base_dir, "ai", "severity_prediction", "best_severity_model.joblib")
    le_path = os.path.join(base_dir, "ai", "severity_prediction", "data", "label_encoder.joblib")
    
    try:
        model = joblib.load(model_path)
        label_encoder = joblib.load(le_path)
        hospital_recommender = HospitalRecommender()
        print("Model, Label Encoder, and Hospital Recommender loaded successfully.")
    except Exception as e:
        print(f"Warning: Could not load model on startup. Ensure it is trained first. Error: {e}")
        
    yield
    # Cleanup code here if needed
    
app = FastAPI(title="JeevanSetu Severity Prediction API", lifespan=lifespan)

@app.post("/predict-severity", response_model=SeverityPredictionResponse)
async def predict_severity(request: SeverityPredictionRequest):
    if model is None or label_encoder is None:
        raise HTTPException(status_code=503, detail="Model is not loaded. Train the model first.")
        
    # Convert request to DataFrame (simulating a single row)
    input_data = {
        'AGE': request.age,
        'VE_TOTAL': request.ve_total,
        'HOUR': request.hour,
        'LGT_COND': request.lgt_cond,
        'WEATHER': request.weather,
        'VSURCOND': request.vsurcond,
        'MAN_COLL': request.man_coll,
        'HARM_EV': request.harm_ev,
        'BODY_TYP': request.body_typ,
        'IMPACT1': request.impact1,
        'ROLLOVER': request.rollover,
        'SEAT_POS': request.seat_pos,
        'REST_USE': request.rest_use
    }
    
    df = pd.DataFrame([input_data])
    
    # Engineer features (applies subsetting and default filling if necessary)
    df_processed = engineer_features(df)
    
    try:
        # Predict class
        pred_idx = model.predict(df_processed)[0]
        predicted_class = label_encoder.inverse_transform([pred_idx])[0]
        
        # Predict probability
        probs = model.predict_proba(df_processed)[0]
        # Max probability across classes
        max_prob = max(probs)
        
        # Format response
        severity_lower = predicted_class.lower() # "critical", "moderate", "minor"
        score = int(max_prob * 100)
        
        # Get Hospital Recommendation
        top_hospitals = []
        if hospital_recommender is not None:
            try:
                # Get top 3 hospitals
                ranked = hospital_recommender.rank(request.latitude, request.longitude, severity_lower)
                for h in ranked[:3]:
                    top_hospitals.append({
                        "hospital_id": h.hospital_id,
                        "hospital_name": h.hospital_name,
                        "distance_km": h.distance_km,
                        "eta_minutes": h.eta_minutes,
                        "ranking_score": h.ranking_score
                    })
            except Exception as e:
                print(f"Hospital recommender error: {e}")
        
        return SeverityPredictionResponse(
            severity=severity_lower, 
            score=score,
            recommended_hospitals=top_hospitals
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)

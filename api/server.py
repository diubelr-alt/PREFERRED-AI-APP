from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class SurveyData(BaseModel):
    project_name: str
    length_ft: float
    width_ft: float
    depth_in: float
    tons: float

@app.get("/")
def root():
    return {"status":"online"}

@app.post("/survey")
def save_survey(data: SurveyData):
    return {
        "saved": True,
        "project": data.project_name,
        "tons": data.tons
    }

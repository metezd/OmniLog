from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="OmniLog API",
    description="Video Game & TV Series Tracking API",
    version="1.0.0"
)

# Frontend uygulamasının çalışacağı adresler
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Tarayıcının frontend isteklerini engellemesini önleyen middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "OmniLog Backend is working!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
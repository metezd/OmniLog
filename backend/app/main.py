from fastapi import FastAPI

app = FastAPI(
    title = "OmniLog API",
    description = "Video Game & TV Series Tracking API",
    version = "1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "OmniLog Backend is working!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
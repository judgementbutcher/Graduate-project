from fastapi import FastAPI

app = FastAPI(title="Emotion-Driven RPG API")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

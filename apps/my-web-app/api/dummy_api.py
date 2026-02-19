from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/estimate")
def estimate(text: str = Query("")):
    return {"tokens": 123, "model": "dummy", "len": len(text)}

# ✅ Alias endpoint the docs are showing
@app.get("/estimate_tokens")
def estimate_tokens(text: str = Query("")):
    return {"tokens": 123, "model": "dummy", "len": len(text)}

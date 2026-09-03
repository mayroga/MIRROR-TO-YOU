import uvicorn
from mirror_engine import app

if __name__ == "__main__":
    uvicorn.run("mirror_engine:app", host="0.0.0.0", port=8000, reload=True)

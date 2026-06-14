import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("okegawa_gomi_api:app", host="0.0.0.0", port=port)

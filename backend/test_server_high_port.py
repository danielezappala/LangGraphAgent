from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello from high port 30000!"}

if __name__ == "__main__":
    uvicorn.run("test_server_high_port:app", host="0.0.0.0", port=30000, reload=True)

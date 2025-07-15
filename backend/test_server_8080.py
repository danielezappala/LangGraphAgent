from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello from port 8080!"}

if __name__ == "__main__":
    uvicorn.run("test_server_8080:app", host="0.0.0.0", port=8080, reload=True)

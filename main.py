from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()


@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/Hello")
def page():
    return {"message":"Just Do It!"}
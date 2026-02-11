from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.createpost import router as createpost
from fastapi.templating import Jinja2Templates
import os
import uvicorn

app = FastAPI(title="Carousel Backend")



app.add_middleware(
  CORSMiddleware,
   allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Templates folder
templates = Jinja2Templates(directory="templates")



app.include_router(createpost , prefix="/createpost")

# Root route for Railway health check
@app.get("/")
async def root():
    return {"message": "Backend is live!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Railway sets this dynamically
    uvicorn.run("main:app", host="0.0.0.0", port=port)
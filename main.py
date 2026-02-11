from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from routes.createpost import router as createpost
from fastapi.templating import Jinja2Templates






app = FastAPI()

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


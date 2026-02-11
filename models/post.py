from pydantic import BaseModel, Field
from typing import List, Union, Literal
from typing_extensions import Annotated


class UploadPost(BaseModel):
    title: str = Field(..., min_length=3, max_length=60)
    description: str = Field(..., min_length=3, max_length=150)
    imageUrl: str
    noOfPages: int = Field(..., ge=1, le=10)
    accName: str = Field(..., min_length=3, max_length=20)
    accUsername: str = Field(..., pattern=r"^\S+$")




class ContentPage(BaseModel):
    page_no: int = Field(..., ge=1, le=8)
    heading: str = Field(..., max_length=200)
    chunk1: str = Field(..., max_length=150)
    chunk2: str = Field(..., max_length=150)
    chunk3: str = Field(..., max_length=150)
    chunk4: str = Field(..., max_length=150)


class ConclusionSlide(BaseModel):
    type: Literal["conclusion"]
    title: str = Field(..., max_length=80)
    line1: str = Field(..., max_length=150)
    line2: str = Field(..., max_length=150)
    action: str = Field(..., max_length=150)


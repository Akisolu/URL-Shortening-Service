from fastapi import FastAPI, status
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from fastapi.responses import RedirectResponse

from controller import URLController

app = FastAPI()

# This class validate if a URL is valid using Pydantic's HttpUrl type. 
# If the URL is not valid, it will raise a ValidationError.
class URLInput(BaseModel):
    url: HttpUrl
    shortCode: str | None = None

# This class is used to define the output model for the shortened URL.
class URLOutput(BaseModel):
    id: int
    url: str
    shortCode: str
    createdAt: datetime
    updatedAt: datetime

# This class is used to define the output model for the shortened URL with statistics.
class URLOutputStats(URLOutput):
    accessCount: int


@app.post("/shorten", response_model=URLOutput, status_code=status.HTTP_201_CREATED)
async def create_shorten_url(url: URLInput):    
    repository = URLController()

    # Return a JSON response with the shortened URL details
    return repository.create_shorten_url(url.url, url.shortCode)

        

@app.get("/shorten/{shortCode}", response_model=URLOutput, status_code=status.HTTP_200_OK)
async def get_short_code_info(shortCode: str):
    repository = URLController()

    # This endpoint only reads metadata. Counting a click here inflates the
    # metric, because the click is already counted when the redirect happens.
    return repository.get_shorten_url(shortCode)
        

@app.put("/shorten/{shortCode}", response_model=URLOutput, status_code=status.HTTP_200_OK)
async def update_shorten_url(shortCode: str, url: URLInput): 
    repository = URLController()

    return repository.update_shorten_url(shortCode, url.url, url.shortCode)
    

@app.delete("/shorten/{shortCode}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shorten_url(shortCode: str):
    repository = URLController()
    repository.delete_shorten_url(shortCode)
    return None


@app.get("/shorten/{shortCode}/stats", response_model=URLOutputStats, status_code=status.HTTP_200_OK)
async def get_shorten_url_stats(shortCode: str):
    repository = URLController()

    return repository.get_shorten_url_stats(shortCode)

@app.get("/{shortCode}")
async def redirect(shortCode: str):
    repository = URLController()
    url = repository.access_url(shortCode)
    
    return RedirectResponse(
        url, 
        status_code=status.HTTP_302_FOUND
    )

@app.get("/", status_code=status.HTTP_200_OK)
async def health():
    return {"status": "online"}
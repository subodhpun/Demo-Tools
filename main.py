from fastapi import FastAPI
import logging
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from tools.chat_app import router as chat_router
from tools.watermark_generator import router as watermark_router


# Create an instance of the FastAPI class
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#serve static files like js, css etc
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 template engine
templates = Jinja2Templates(directory="templates")


# Include the watermark router
app.include_router(watermark_router)


# Define a path operation to serve the index.html
@app.get("/")
async def get_index(request: Request):
    return templates.TemplateResponse("watermark_generator/index.html", {"request": request})

# @app.get("/admin")
# async def get_admin(request: Request):
#     return templates.TemplateResponse("admin/index.html", {"request": request})


# # Include the chat routes from chatapp.py
# app.include_router(chat_router)  # This includes the WebSocket routes
# app.include_router(watermark_router)



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Log that the server is starting
    logger.info("Starting server...")

    # Run the FastAPI app with Uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8005)
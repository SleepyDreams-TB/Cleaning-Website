from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from fastapi import FastAPI, Form
from typing import Union
from bson import json_util
import json

# Initialize FastAPI
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Which origins are allowed. "*" = all.
    allow_credentials=True,     # If cookies/authorization headers are allowed in cross-site requests.
    allow_methods=["*"],        # Which HTTP methods (GET, POST, PUT, DELETE, etc.) are allowed.
    allow_headers=["*"],        # Which request headers are allowed.
)


# MongoDB setup
client = MongoClient('mongodb+srv://SleepyDreams:saRqSb7xoc1cI1DO@kingburgercluster.ktvavv3.mongodb.net/?retryWrites=true&w=majority')
db = client["cleaning_website"]
products = db["products"]

@app.get("/")
def root():
    return {"message": "Welcome to the Products API"}

@app.post("/products/create/")
async def create_product(
    name: str = Form(...),
    price: float = Form(...),
    description: Union[str, None] = Form(None),
    category: int = Form(0),
    image_url: Union[str, None] = Form(None)
):
    try:
        result = products.insert_one({
            "name": name,
            "price": price,
            "description": description,
            "category": category,
            "image_url": image_url
        })
        return {"message": "Product created successfully", "id": str(result.inserted_id)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/products/")
async def get_all_products():
    try:
        # Fetch all products from MongoDB
        all_products = list(products.find({}))
        # Convert ObjectId to string for JSON serialization (BSON to JSON to Py dict)
        return json.loads(json_util.dumps(all_products))
    except Exception as e:
        return {"error": str(e)}

@app.get("/products/{id}")
async def get_product(id: str):
    try:
        from bson.objectid import ObjectId
        product = products.find_one({"_id": ObjectId(id)})
        if product:
            return json.loads(json_util.dumps(product))
        return {"message": "Product not found"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("productsDB:app", host="127.0.0.1", port=8000, reload=True)
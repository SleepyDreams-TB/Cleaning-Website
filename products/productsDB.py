from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from fastapi import FastAPI, Form
from typing import Union
from bson import json_util
import json
from bson.objectid import ObjectId
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
        all_products = []
        
        for product in products.find():
            product["_id"] = str(product["_id"])
            all_products.append(product)
        return all_products
    except Exception as e:
        return {"error": str(e)}

@app.get("/products/{id}")
async def get_product(id: str):
    try:
        product = products.find_one({"_id": ObjectId(id)})
        if product:
            product["_id"] = str(product["_id"])
        return {"message": "Product not found"}
    except Exception as e:
        return {"error": str(e)}

@app.put("/products/update/{id}")
async def update_product(
    id: str,
    name: Union[str, None] = Form(None),
    price: Union[float, None] = Form(None),
    description: Union[str, None] = Form(None),
    category: Union[int, None] = Form(None),
    image_url: Union[str, None] = Form(None)
):
    try:
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if price is not None:
            update_data["price"] = price
        if description is not None:
            update_data["description"] = description
        if category is not None:
            update_data["category"] = category
        if image_url is not None:
            update_data["image_url"] = image_url
        
        result = products.update_one({"_id": ObjectId(id)}, {"$set": update_data})
        
        if result.matched_count:
            return {"message": "Product updated successfully"}
        return {"message": "Product not found"}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/products/delete/{id}")
async def delete_product(id: str):
    try:
        result = products.delete_one({"_id": ObjectId(id)})
        if result.deleted_count:
            return {"message": "Product deleted successfully"}
        return {"message": "Product not found"}
    except Exception as e:
        return {"error": str(e)}
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("productsDB:app", host="127.0.0.1", port=8000, reload=True)
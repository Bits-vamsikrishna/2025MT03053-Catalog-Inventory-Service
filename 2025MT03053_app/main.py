from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import List



# Database Setup (SQLite - Database-per-Service Pattern)
DATABASE_URL = "sqlite:///./inventory.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()



class ProductModel(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    sku = Column(String, unique=True, nullable=False)
    price = Column(Float, nullable=False)
    stock_qty = Column(Integer, nullable=False, default=0)



Base.metadata.create_all(bind=engine)



# Pydantic Schemas (DTOs for Commands & Queries)
class ProductCreateCommand(BaseModel):
    name: str = Field(..., examples=["Wireless Mechanical Keyboard"])
    sku: str = Field(..., examples=["KB-MECH-01"])
    price: float = Field(..., gt=0, examples=[89.99])
    stock_qty: int = Field(..., ge=0, examples=[50])



class StockReserveCommand(BaseModel):
    quantity: int = Field(..., gt=0, examples=[2])



class ProductResponse(BaseModel):
    id: int
    name: str
    sku: str
    price: float
    stock_qty: int

    class Config:
        from_attributes = True




# FastAPI Application & Dependency Injection
app = FastAPI(
    title="Catalog & Inventory Microservice",
    description="Manages product catalog queries and stock reservation commands.",
    version="1.0.0",
)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.get("/health", tags=["Health"])
def health_check():
    return {"service": "catalog-inventory-service", "status": "UP"}



# COMMAND: createProduct
@app.post("/products", response_model=ProductResponse, status_code=201, tags=["Commands"])
def create_product(payload: ProductCreateCommand, db: Session = Depends(get_db)):
    existing = db.query(ProductModel).filter(ProductModel.sku == payload.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Product with SKU '{payload.sku}' already exists.")

    product = ProductModel(
        name=payload.name,
        sku=payload.sku,
        price=payload.price,
        stock_qty=payload.stock_qty,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product



# QUERY: getProducts
@app.get("/products", response_model=List[ProductResponse], tags=["Queries"])
def get_products(db: Session = Depends(get_db)):
    return db.query(ProductModel).all()



# QUERY: getProductById
@app.get("/products/{product_id}", response_model=ProductResponse, tags=["Queries"])
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product ID {product_id} not found.")
    return product



# COMMAND: reserveStock (Called synchronously by Order-Service)
@app.put("/products/{product_id}/reserve", response_model=ProductResponse, tags=["Commands"])
def reserve_stock(product_id: int, payload: StockReserveCommand, db: Session = Depends(get_db)):
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product ID {product_id} not found.")

    if product.stock_qty < payload.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock for '{product.name}'. Requested: {payload.quantity}, Available: {product.stock_qty}",
        )

    product.stock_qty -= payload.quantity
    db.commit()
    db.refresh(product)
    return product



# COMMAND: deleteProduct (Delete a single product by ID)
@app.delete("/products/{product_id}", status_code=200, tags=["Commands"])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product ID {product_id} not found.")
    
    db.delete(product)
    db.commit()
    return {"message": f"Product '{product.name}' (ID: {product_id}) deleted successfully."}



# COMMAND: clearAllProducts (Wipe all products to start fresh)
@app.delete("/products", status_code=200, tags=["Commands"])
def clear_all_products(db: Session = Depends(get_db)):
    deleted_count = db.query(ProductModel).delete()
    db.commit()
    return {"message": f"Cleared {deleted_count} products from inventory."}
from pydantic import BaseModel, Field, HttpUrl


class Book(BaseModel):
    title: str = Field(min_length=1)
    category: str
    price_gbp: float = Field(ge=0)
    rating: int = Field(ge=1, le=5)
    in_stock: bool
    stock_count: int = Field(ge=0)
    upc: str = Field(min_length=1)
    product_url: HttpUrl
    image_url: HttpUrl


class Quote(BaseModel):
    text: str = Field(min_length=1)
    author: str = Field(min_length=1)
    tags: list[str] = []

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

class StoreChain(str, Enum):
    WALMART = "Walmart"
    TARGET = "Target"
    HEB = "HEB"
    KROGER = "Kroger"
    COSTCO = "Costco"
    ALDI = "Aldi"
    WHOLE_FOODS = "Whole Foods"
    SAFEWAY = "Safeway"

class Store(BaseModel):
    """Represents a physical store location."""
    id: str
    name: str
    chain: StoreChain
    address: str
    city: str
    state: str
    zip_code: str
    latitude: float
    longitude: float
    phone: Optional[str] = None
    hours: Optional[Dict[str, str]] = None
    distance_miles: Optional[float] = None
    is_open: Optional[bool] = None
    
    @property
    def full_address(self) -> str:
        """Return the full address as a formatted string."""
        return f"{self.address}, {self.city}, {self.state} {self.zip_code}"
    
    @property
    def display_name(self) -> str:
        """Return a display-friendly store name with location."""
        return f"{self.chain} - {self.city}"

class Product(BaseModel):
    """Represents a product available at a store."""
    id: str
    name: str
    brand: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    upc: Optional[str] = None
    
    # Price information
    price: float
    original_price: Optional[float] = None
    unit_price: Optional[float] = None
    unit: Optional[str] = None  # e.g., "per lb", "per oz", "each"
    
    # Store information
    store_id: str
    store_name: str
    
    # Deal information
    is_on_sale: bool = False
    sale_ends: Optional[datetime] = None
    discount_percent: Optional[float] = None
    
    @property
    def display_price(self) -> str:
        """Return a formatted price string."""
        if self.unit_price and self.unit:
            return f"${self.price:.2f} (${self.unit_price:.2f}/{self.unit})"
        return f"${self.price:.2f}"
    
    @property
    def discount_info(self) -> Optional[str]:
        """Return discount information if on sale."""
        if not self.is_on_sale:
            return None
            
        discount_info = []
        if self.discount_percent:
            discount_info.append(f"{self.discount_percent:.0f}% off")
        if self.original_price:
            discount_info.append(f"was ${self.original_price:.2f}")
        if self.sale_ends:
            discount_info.append(f"ends {self.sale_ends.strftime('%m/%d/%Y')}")
            
        return " • ".join(discount_info) if discount_info else None

class Deal(Product):
    """Represents a special deal or promotion on a product."""
    deal_type: str  # e.g., "weekly_special", "clearance", "bogo"
    deal_description: Optional[str] = None
    
    @validator('deal_type')
    def validate_deal_type(cls, v):
        valid_types = ["weekly_special", "clearance", "bogo", "coupon", "member_only"]
        if v not in valid_types:
            raise ValueError(f"Invalid deal type. Must be one of: {', '.join(valid_types)}")
        return v

class PriceAlert(BaseModel):
    """Represents a user's price alert for a product."""
    id: str
    product_id: str
    product_name: str
    target_price: float
    current_price: float
    is_active: bool = True
    created_at: datetime
    last_triggered: Optional[datetime] = None
    
    @property
    def price_difference(self) -> float:
        """Return the difference between target and current price."""
        return self.current_price - self.target_price
    
    @property
    def price_difference_percent(self) -> float:
        """Return the percentage difference between target and current price."""
        if self.current_price == 0:
            return 0
        return ((self.current_price - self.target_price) / self.current_price) * 100

class SearchResult(BaseModel):
    """Represents the result of a product search."""
    products: List[Product]
    total_results: int
    page: int
    page_size: int
    query: str
    filters: Dict[str, Any] = {}
    
    @property
    def has_more(self) -> bool:
        """Return True if there are more results available."""
        return (self.page * self.page_size) < self.total_results

class PriceHistoryPoint(BaseModel):
    """Represents a single data point in a product's price history."""
    date: datetime
    price: float
    is_sale: bool = False
    store_id: Optional[str] = None
    
class ProductDetails(Product):
    """Detailed product information including price history and availability."""
    price_history: List[PriceHistoryPoint] = []
    available_stores: List[Dict[str, Any]] = []  # List of store IDs and current prices
    price_range: Optional[Dict[str, float]] = None  # min, max, avg prices
    
    @property
    def price_trend(self) -> str:
        """Return a simple trend indicator (up, down, stable)."""
        if len(self.price_history) < 2:
            return "stable"
            
        recent = self.price_history[-1].price
        previous = self.price_history[-2].price
        
        if recent > previous:
            return "up"
        elif recent < previous:
            return "down"
        return "stable"

class UserPreferences(BaseModel):
    """User preferences for the application."""
    default_zip_code: str
    default_radius_miles: int = 10
    preferred_stores: List[str] = []
    notification_preferences: Dict[str, bool] = {
        "email": True,
        "push": True,
        "sms": False
    }
    theme: str = "light"
    
    @validator('default_radius_miles')
    def validate_radius(cls, v):
        if v < 1 or v > 50:
            raise ValueError("Radius must be between 1 and 50 miles")
        return v

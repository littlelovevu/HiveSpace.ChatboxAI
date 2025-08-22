"""
Viết thành một tool để về sau sử dụng gắn vào AI Agent
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field
import random
import os
import json


class ProductSearchInput(BaseModel):
    input: str = Field(description="Nội dung cần tìm kiếm về thông tin sản phẩm trong cơ sở dữ liệu để cập nhật thêm thông tin trả lời.")


@tool("product_search", args_schema=ProductSearchInput, return_direct=True)
def product_search(input: str):
    """
    Tìm kiếm thông tin sản phẩm trong cơ sở dữ liệu dựa vào nội dung người dùng cung cấp.
    """
    # Danh mục sản phẩm
    categories = [
        "Electronics", "Computers", "Mobile", "Audio", "Gaming", "Photography", 
        "Home & Garden", "Kitchen", "Furniture", "Fashion", "Sports", "Books", 
        "Automotive", "Health", "Beauty", "Toys", "Office", "Outdoor", "Art", "Food"
    ]
    
    # Dữ liệu sản phẩm mẫu
    products = [
        # Electronics (1-10)
        {"id": 1, "name": "Laptop Dell XPS 13", "price": 1500, "category": "Electronics", "in_stock": True, "brand": "Dell", "rating": 4.8},
        {"id": 2, "name": "iPhone 15 Pro", "price": 1200, "category": "Electronics", "in_stock": False, "brand": "Apple", "rating": 4.9},
        {"id": 3, "name": "Samsung Galaxy S24", "price": 1100, "category": "Electronics", "in_stock": True, "brand": "Samsung", "rating": 4.7},
        {"id": 4, "name": "MacBook Air M2", "price": 1300, "category": "Electronics", "in_stock": True, "brand": "Apple", "rating": 4.9},
        {"id": 5, "name": "iPad Pro 12.9", "price": 900, "category": "Electronics", "in_stock": True, "brand": "Apple", "rating": 4.8},
        {"id": 6, "name": "Sony WH-1000XM5", "price": 400, "category": "Electronics", "in_stock": False, "brand": "Sony", "rating": 4.9},
        {"id": 7, "name": "DJI Mini 3 Pro", "price": 800, "category": "Electronics", "in_stock": True, "brand": "DJI", "rating": 4.8},
        {"id": 8, "name": "GoPro Hero 11", "price": 500, "category": "Electronics", "in_stock": True, "brand": "GoPro", "rating": 4.7},
        {"id": 9, "name": "Nintendo Switch OLED", "price": 350, "category": "Electronics", "in_stock": True, "brand": "Nintendo", "rating": 4.8},
        {"id": 10, "name": "PlayStation 5", "price": 500, "category": "Electronics", "in_stock": False, "brand": "Sony", "rating": 4.9},
        
        # Computers (11-20)
        {"id": 11, "name": "Gaming PC RTX 4080", "price": 2500, "category": "Computers", "in_stock": True, "brand": "Custom", "rating": 4.9},
        {"id": 12, "name": "iMac 27-inch", "price": 1800, "category": "Computers", "in_stock": True, "brand": "Apple", "rating": 4.8},
        {"id": 13, "name": "Lenovo ThinkPad X1", "price": 1600, "category": "Computers", "in_stock": True, "brand": "Lenovo", "rating": 4.7},
        {"id": 14, "name": "HP Spectre x360", "price": 1400, "category": "Computers", "in_stock": True, "brand": "HP", "rating": 4.6},
        {"id": 15, "name": "ASUS ROG Strix", "price": 2200, "category": "Computers", "in_stock": True, "brand": "ASUS", "rating": 4.8},
        {"id": 16, "name": "Mac Mini M2", "price": 700, "category": "Computers", "in_stock": True, "brand": "Apple", "rating": 4.7},
        {"id": 17, "name": "Dell Precision 5570", "price": 2800, "category": "Computers", "in_stock": True, "brand": "Dell", "rating": 4.8},
        {"id": 18, "name": "MSI Creator Z16", "price": 1900, "category": "Computers", "in_stock": True, "brand": "MSI", "rating": 4.7},
        {"id": 19, "name": "Razer Blade 15", "price": 2400, "category": "Computers", "in_stock": False, "brand": "Razer", "rating": 4.8},
        {"id": 20, "name": "Alienware x17", "price": 3000, "category": "Computers", "in_stock": True, "brand": "Alienware", "rating": 4.9},
        
        # Mobile (21-30)
        {"id": 21, "name": "Google Pixel 8", "price": 700, "category": "Mobile", "in_stock": True, "brand": "Google", "rating": 4.7},
        {"id": 22, "name": "OnePlus 12", "price": 800, "category": "Mobile", "in_stock": True, "brand": "OnePlus", "rating": 4.6},
        {"id": 23, "name": "Xiaomi 14 Ultra", "price": 900, "category": "Mobile", "in_stock": True, "brand": "Xiaomi", "rating": 4.5},
        {"id": 24, "name": "Nothing Phone 2", "price": 600, "category": "Mobile", "in_stock": True, "brand": "Nothing", "rating": 4.4},
        {"id": 25, "name": "ASUS ROG Phone 8", "price": 1000, "category": "Mobile", "in_stock": True, "brand": "ASUS", "rating": 4.7},
        {"id": 26, "name": "Samsung Galaxy Z Fold 5", "price": 1800, "category": "Mobile", "in_stock": True, "brand": "Samsung", "rating": 4.8},
        {"id": 27, "name": "iPhone 15 Plus", "price": 900, "category": "Mobile", "in_stock": True, "brand": "Apple", "rating": 4.8},
        {"id": 28, "name": "Motorola Edge 40", "price": 500, "category": "Mobile", "in_stock": True, "brand": "Motorola", "rating": 4.3},
        {"id": 29, "name": "Realme GT Neo 5", "price": 400, "category": "Mobile", "in_stock": True, "brand": "Realme", "rating": 4.4},
        {"id": 30, "name": "Vivo X100 Pro", "price": 850, "category": "Mobile", "in_stock": True, "brand": "Vivo", "rating": 4.6},
        
        # Audio (31-40)
        {"id": 31, "name": "AirPods Pro 2", "price": 250, "category": "Audio", "in_stock": True, "brand": "Apple", "rating": 4.8},
        {"id": 32, "name": "Bose QuietComfort 45", "price": 350, "category": "Audio", "in_stock": True, "brand": "Bose", "rating": 4.7},
        {"id": 33, "name": "Sennheiser HD 660S", "price": 500, "category": "Audio", "in_stock": True, "brand": "Sennheiser", "rating": 4.8},
        {"id": 34, "name": "Audio-Technica ATH-M50x", "price": 150, "category": "Audio", "in_stock": True, "brand": "Audio-Technica", "rating": 4.6},
        {"id": 35, "name": "JBL Charge 5", "price": 180, "category": "Audio", "in_stock": True, "brand": "JBL", "rating": 4.5},
        {"id": 36, "name": "Ultimate Ears Boom 3", "price": 130, "category": "Audio", "in_stock": True, "brand": "Ultimate Ears", "rating": 4.4},
        {"id": 37, "name": "Shure SM7B", "price": 400, "category": "Audio", "in_stock": True, "brand": "Shure", "rating": 4.9},
        {"id": 38, "name": "Focal Utopia", "price": 4000, "category": "Audio", "in_stock": False, "brand": "Focal", "rating": 4.9},
        {"id": 39, "name": "Audeze LCD-4", "price": 4000, "category": "Audio", "in_stock": True, "brand": "Audeze", "rating": 4.8},
        {"id": 40, "name": "Campfire Audio Andromeda", "price": 1100, "category": "Audio", "in_stock": True, "brand": "Campfire Audio", "rating": 4.7},
        
        # Gaming (41-50)
        {"id": 41, "name": "Xbox Series X", "price": 500, "category": "Gaming", "in_stock": True, "brand": "Microsoft", "rating": 4.8},
        {"id": 42, "name": "Nintendo Switch Lite", "price": 200, "category": "Gaming", "in_stock": True, "brand": "Nintendo", "rating": 4.6},
        {"id": 43, "name": "Steam Deck OLED", "price": 550, "category": "Gaming", "in_stock": True, "brand": "Valve", "rating": 4.7},
        {"id": 44, "name": "Logitech G Pro X", "price": 130, "category": "Gaming", "in_stock": True, "brand": "Logitech", "rating": 4.5},
        {"id": 45, "name": "Razer DeathAdder V3", "price": 70, "category": "Gaming", "in_stock": True, "brand": "Razer", "rating": 4.6},
        {"id": 46, "name": "Corsair K100 RGB", "price": 230, "category": "Gaming", "in_stock": True, "brand": "Corsair", "rating": 4.7},
        {"id": 47, "name": "HyperX Cloud Alpha", "price": 100, "category": "Gaming", "in_stock": True, "brand": "HyperX", "rating": 4.5},
        {"id": 48, "name": "BenQ ZOWIE XL2546K", "price": 400, "category": "Gaming", "in_stock": True, "brand": "BenQ", "rating": 4.6},
        {"id": 49, "name": "Elgato Stream Deck", "price": 150, "category": "Gaming", "in_stock": True, "brand": "Elgato", "rating": 4.7},
        {"id": 50, "name": "Astro A50", "price": 300, "category": "Gaming", "in_stock": True, "brand": "Astro", "rating": 4.6},
        
        # Photography (51-60)
        {"id": 51, "name": "Canon EOS R5", "price": 3900, "category": "Photography", "in_stock": True, "brand": "Canon", "rating": 4.9},
        {"id": 52, "name": "Sony A7 IV", "price": 2500, "category": "Photography", "in_stock": True, "brand": "Sony", "rating": 4.8},
        {"id": 53, "name": "Nikon Z6 II", "price": 2000, "category": "Photography", "in_stock": True, "brand": "Nikon", "rating": 4.7},
        {"id": 54, "name": "Fujifilm X-T5", "price": 1700, "category": "Photography", "in_stock": True, "brand": "Fujifilm", "rating": 4.8},
        {"id": 55, "name": "Leica M11", "price": 9000, "category": "Photography", "in_stock": False, "brand": "Leica", "rating": 4.9},
        {"id": 56, "name": "Sigma fp L", "price": 2500, "category": "Photography", "in_stock": True, "brand": "Sigma", "rating": 4.6},
        {"id": 57, "name": "Panasonic Lumix S5", "price": 2000, "category": "Photography", "in_stock": True, "brand": "Panasonic", "rating": 4.7},
        {"id": 58, "name": "Olympus OM-1", "price": 2200, "category": "Photography", "in_stock": True, "brand": "Olympus", "rating": 4.7},
        {"id": 59, "name": "Hasselblad X2D", "price": 8200, "category": "Photography", "in_stock": True, "brand": "Hasselblad", "rating": 4.9},
        {"id": 60, "name": "Pentax K-3 III", "price": 1900, "category": "Photography", "in_stock": True, "brand": "Pentax", "rating": 4.6},
        
        # Home & Garden (61-70)
        {"id": 61, "name": "Philips Hue Starter Kit", "price": 200, "category": "Home & Garden", "in_stock": True, "brand": "Philips", "rating": 4.6},
        {"id": 62, "name": "Ring Video Doorbell", "price": 100, "category": "Home & Garden", "in_stock": True, "brand": "Ring", "rating": 4.5},
        {"id": 63, "name": "Nest Learning Thermostat", "price": 250, "category": "Home & Garden", "in_stock": True, "brand": "Nest", "rating": 4.7},
        {"id": 64, "name": "Roomba i7+", "price": 800, "category": "Home & Garden", "in_stock": True, "brand": "iRobot", "rating": 4.6},
        {"id": 65, "name": "Dyson V15 Detect", "price": 700, "category": "Home & Garden", "in_stock": True, "brand": "Dyson", "rating": 4.8},
        {"id": 66, "name": "Weber Genesis II", "price": 800, "category": "Home & Garden", "in_stock": True, "brand": "Weber", "rating": 4.7},
        {"id": 67, "name": "DeWalt 20V Max", "price": 300, "category": "Home & Garden", "in_stock": True, "brand": "DeWalt", "rating": 4.6},
        {"id": 68, "name": "Black & Decker 20V", "price": 150, "category": "Home & Garden", "in_stock": True, "brand": "Black & Decker", "rating": 4.4},
        {"id": 69, "name": "Milwaukee M18", "price": 400, "category": "Home & Garden", "in_stock": True, "brand": "Milwaukee", "rating": 4.7},
        {"id": 70, "name": "Ryobi 18V One+", "price": 200, "category": "Home & Garden", "in_stock": True, "brand": "Ryobi", "rating": 4.5},
        
        # Kitchen (71-80)
        {"id": 71, "name": "KitchenAid Stand Mixer", "price": 400, "category": "Kitchen", "in_stock": True, "brand": "KitchenAid", "rating": 4.8},
        {"id": 72, "name": "Vitamix 5200", "price": 450, "category": "Kitchen", "in_stock": True, "brand": "Vitamix", "rating": 4.9},
        {"id": 73, "name": "Breville BES870XL", "price": 700, "category": "Kitchen", "in_stock": True, "brand": "Breville", "rating": 4.7},
        {"id": 74, "name": "Cuisinart Food Processor", "price": 200, "category": "Kitchen", "in_stock": True, "brand": "Cuisinart", "rating": 4.6},
        {"id": 75, "name": "Ninja Foodi 9-in-1", "price": 200, "category": "Kitchen", "in_stock": True, "brand": "Ninja", "rating": 4.5},
        {"id": 76, "name": "Instant Pot Duo", "price": 100, "category": "Kitchen", "in_stock": True, "brand": "Instant Pot", "rating": 4.7},
        {"id": 77, "name": "Le Creuset Dutch Oven", "price": 350, "category": "Kitchen", "in_stock": True, "brand": "Le Creuset", "rating": 4.8},
        {"id": 78, "name": "All-Clad D3 Pan Set", "price": 500, "category": "Kitchen", "in_stock": True, "brand": "All-Clad", "rating": 4.7},
        {"id": 79, "name": "Wusthof Classic Knife", "price": 150, "category": "Kitchen", "in_stock": True, "brand": "Wusthof", "rating": 4.8},
        {"id": 80, "name": "Microplane Grater", "price": 15, "category": "Kitchen", "in_stock": True, "brand": "Microplane", "rating": 4.6},
        
        # Furniture (81-90)
        {"id": 81, "name": "Herman Miller Aeron", "price": 1500, "category": "Furniture", "in_stock": True, "brand": "Herman Miller", "rating": 4.9},
        {"id": 82, "name": "Steelcase Leap V2", "price": 1200, "category": "Furniture", "in_stock": True, "brand": "Steelcase", "rating": 4.8},
        {"id": 83, "name": "IKEA Markus", "price": 200, "category": "Furniture", "in_stock": True, "brand": "IKEA", "rating": 4.4},
        {"id": 84, "name": "West Elm Sofa", "price": 1200, "category": "Furniture", "in_stock": True, "brand": "West Elm", "rating": 4.6},
        {"id": 85, "name": "Crate & Barrel Table", "price": 800, "category": "Furniture", "in_stock": True, "brand": "Crate & Barrel", "rating": 4.5},
        {"id": 86, "name": "Pottery Barn Bed", "price": 1500, "category": "Furniture", "in_stock": True, "brand": "Pottery Barn", "rating": 4.6},
        {"id": 87, "name": "Restoration Hardware", "price": 3000, "category": "Furniture", "in_stock": True, "brand": "Restoration Hardware", "rating": 4.7},
        {"id": 88, "name": "Wayfair Desk", "price": 300, "category": "Furniture", "in_stock": True, "brand": "Wayfair", "rating": 4.3},
        {"id": 89, "name": "Ashley Furniture", "price": 600, "category": "Furniture", "in_stock": True, "brand": "Ashley", "rating": 4.4},
        {"id": 90, "name": "La-Z-Boy Recliner", "price": 800, "category": "Furniture", "in_stock": True, "brand": "La-Z-Boy", "rating": 4.5},
        
        # Fashion (91-100)
        {"id": 91, "name": "Nike Air Max 270", "price": 150, "category": "Fashion", "in_stock": True, "brand": "Nike", "rating": 4.6},
        {"id": 92, "name": "Adidas Ultraboost 22", "price": 180, "category": "Fashion", "in_stock": True, "brand": "Adidas", "rating": 4.7},
        {"id": 93, "name": "Apple Watch Series 9", "price": 400, "category": "Fashion", "in_stock": True, "brand": "Apple", "rating": 4.8},
        {"id": 94, "name": "Fossil Gen 6", "price": 300, "category": "Fashion", "in_stock": True, "brand": "Fossil", "rating": 4.5},
        {"id": 95, "name": "Ray-Ban Aviator", "price": 200, "category": "Fashion", "in_stock": True, "brand": "Ray-Ban", "rating": 4.7},
        {"id": 96, "name": "Oakley Holbrook", "price": 150, "category": "Fashion", "in_stock": True, "brand": "Oakley", "rating": 4.6},
        {"id": 97, "name": "Tissot T-Touch", "price": 1200, "category": "Fashion", "in_stock": True, "brand": "Tissot", "rating": 4.7},
        {"id": 98, "name": "Seiko Prospex", "price": 400, "category": "Fashion", "in_stock": True, "brand": "Seiko", "rating": 4.6},
        {"id": 99, "name": "Casio G-Shock", "price": 100, "category": "Fashion", "in_stock": True, "brand": "Casio", "rating": 4.5},
        {"id": 100, "name": "Swatch Originals", "price": 80, "category": "Fashion", "in_stock": True, "brand": "Swatch", "rating": 4.4}
    ]

    # Nạp thêm sản phẩm đã được import qua file .txt (nếu có)
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        products_path = os.path.join(base_dir, "apis", "database", "products.json")
        if os.path.exists(products_path):
            with open(products_path, "r", encoding="utf-8") as f:
                imported = json.load(f)
                if isinstance(imported, list):
                    products.extend(imported)
    except Exception:
        # Im lặng nếu không thể nạp, tool vẫn hoạt động với dữ liệu mẫu
        pass
    
    # Tìm kiếm sản phẩm dựa trên input
    input_lower = input.lower()
    matched_products = []
    
    for product in products:
        # Tìm kiếm theo tên, danh mục, thương hiệu
        if (input_lower in product["name"].lower() or 
            input_lower in product["category"].lower() or 
            input_lower in product["brand"].lower()):
            matched_products.append(product)
    
    # Nếu không tìm thấy, trả về tất cả sản phẩm
    if not matched_products:
        return {
            "message": f"Không tìm thấy sản phẩm phù hợp với '{input}'. Dưới đây là tất cả sản phẩm:",
            "products": products,
            "total": len(products),
            "categories": categories
        }
    
    return {
        "message": f"Tìm thấy {len(matched_products)} sản phẩm phù hợp với '{input}':",
        "products": matched_products,
        "total": len(matched_products),
        "search_query": input
    }



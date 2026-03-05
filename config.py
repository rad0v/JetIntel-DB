import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB
MONGO_URL = os.getenv("MONGO_URL")

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "jetintel-super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Cloudinary
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

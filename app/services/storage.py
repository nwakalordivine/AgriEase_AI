import os
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

class CloudinaryStorage:
    @staticmethod
    def save_file(file_obj: UploadFile):
        # file_obj.file is a SpooledTemporaryFile – pass to cloudinary
        upload_result = cloudinary.uploader.upload(file_obj.file, folder="agri_ai")
        return upload_result["secure_url"]

def get_storage_provider():
    return CloudinaryStorage()

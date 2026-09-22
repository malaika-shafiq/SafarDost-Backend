import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
import cloudinary
import cloudinary.uploader

router = APIRouter(prefix="/media", tags=["Media Storage Engine"])

# 🚀 INITIALIZE THE CLOUD STORAGE BUCKET NATIVELY ON RUNTIME STARTUP:
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_image_to_cloud(file: UploadFile = File(...)):
    """
    DECOUPLED MEDIA CAPTURE INTERFACE: Consumes multi-part file streams,
    uploads them to a secure cloud bucket, and returns a unique public HTTPS URL reference.
    """
    # 1. Enforce strict asset validation barriers
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validation Failure: File stream must be an explicit image type layout (png, jpeg, jpg)."
        )

    try:
        # 2. Stream the raw byte file data directly up to the Cloud content network
        upload_result = cloudinary.uploader.upload(
            file.file,
            folder="safar_dost_assets"  # Groups your user uploads cleanly into a dedicated folder bucket
        )

        # 3. Extract the clean, persistent public CDN hyperlink token string parameter
        secure_url = upload_result.get("secure_url")
        if not secure_url:
            raise ValueError("Cloud gateway failed to return an accessible secure asset target.")

        return {
            "success": True,
            "message": "File streamed and stored successfully in the cloud bucket grid.",
            "image_url": secure_url
        }

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cloud Storage Delivery Failure: {str(error)}"
        )

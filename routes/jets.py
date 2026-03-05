from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from database import jet_collection
from models.jet import JetCreate, JetUpdate
from middleware.auth import get_current_user, require_role
from typing import List
import cloudinary
import cloudinary.uploader
from config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET

# Configure Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

router = APIRouter(tags=["Jets"])


# ─────────────────────────────────────────────
# PUBLIC ROUTES (no auth required)
# ─────────────────────────────────────────────

@router.get("/jets")
async def get_all_jets():
    """Get all jets — accessible to everyone."""
    jets = await jet_collection.find().to_list(length=None)
    for jet in jets:
        jet["_id"] = str(jet["_id"])
    return jets


@router.get("/jets/{jet_id}")
async def get_jet_by_id(jet_id: str):
    """Get a single jet by its slug ID (e.g. 'gulfstream-g650er')."""
    jet = await jet_collection.find_one({"id": jet_id})
    if not jet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jet '{jet_id}' not found",
        )
    jet["_id"] = str(jet["_id"])
    return jet


# ─────────────────────────────────────────────
# ADMIN ROUTES (require admin role)
# ─────────────────────────────────────────────

@router.post("/admin/jets", status_code=status.HTTP_201_CREATED)
async def create_jet(
    jet_data: JetCreate,
    admin: dict = Depends(require_role("admin")),
):
    """Add a new jet to the database. Admin only."""
    # Check if jet with same slug ID already exists
    existing = await jet_collection.find_one({"id": jet_data.id})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Jet with ID '{jet_data.id}' already exists",
        )

    new_jet = jet_data.model_dump()
    result = await jet_collection.insert_one(new_jet)
    new_jet["_id"] = str(result.inserted_id)

    return {"message": "Jet created successfully", "jet": new_jet}


@router.put("/admin/jets/{jet_id}")
async def update_jet(
    jet_id: str,
    jet_data: JetUpdate,
    admin: dict = Depends(require_role("admin")),
):
    """Update an existing jet by its slug ID. Admin only."""
    # Only include fields that were actually provided (not None)
    update_fields = {k: v for k, v in jet_data.model_dump().items() if v is not None}

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    result = await jet_collection.update_one(
        {"id": jet_id},
        {"$set": update_fields},
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jet '{jet_id}' not found",
        )

    updated_jet = await jet_collection.find_one({"id": jet_id})
    updated_jet["_id"] = str(updated_jet["_id"])

    return {"message": "Jet updated successfully", "jet": updated_jet}


@router.post("/admin/jets/upload-image")
async def upload_jet_image(
    file: UploadFile = File(...),
    admin: dict = Depends(require_role("admin")),
):
    """Upload a jet image to Cloudinary. Admin only."""
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )
    
    try:
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file.file,
            folder="jetintel/jets",  # Organize uploads in a folder
            resource_type="image",
            allowed_formats=["jpg", "jpeg", "png", "webp"],
        )
        
        # Return the secure URL
        return {
            "message": "Image uploaded successfully",
            "url": result["secure_url"],
            "public_id": result["public_id"],
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}",
        )


@router.delete("/admin/jets/{jet_id}")
async def delete_jet(
    jet_id: str,
    admin: dict = Depends(require_role("admin")),
):
    """Delete a jet by its slug ID. Admin only."""
    result = await jet_collection.delete_one({"id": jet_id})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jet '{jet_id}' not found",
        )

    return {"message": f"Jet '{jet_id}' deleted successfully"}


@router.post("/admin/jets/bulk-upload", status_code=status.HTTP_201_CREATED)
async def bulk_upload_jets(
    jets_data: List[JetCreate],
    admin: dict = Depends(require_role("admin")),
):
    """
    Bulk upload multiple jets at once. Admin only.
    
    Accepts an array of jet objects. Will skip jets with duplicate IDs
    and report them in the response.
    """
    if not jets_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No jets provided for upload",
        )
    
    created_jets = []
    skipped_jets = []
    errors = []
    
    for jet_data in jets_data:
        try:
            # Check if jet already exists
            existing = await jet_collection.find_one({"id": jet_data.id})
            if existing:
                skipped_jets.append({
                    "id": jet_data.id,
                    "reason": "Jet with this ID already exists"
                })
                continue
            
            # Insert the jet
            new_jet = jet_data.model_dump()
            result = await jet_collection.insert_one(new_jet)
            new_jet["_id"] = str(result.inserted_id)
            created_jets.append(new_jet)
            
        except Exception as e:
            errors.append({
                "id": jet_data.id,
                "error": str(e)
            })
    
    return {
        "message": f"Bulk upload completed",
        "summary": {
            "total_provided": len(jets_data),
            "created": len(created_jets),
            "skipped": len(skipped_jets),
            "errors": len(errors),
        },
        "created_jets": created_jets,
        "skipped_jets": skipped_jets,
        "errors": errors,
    }

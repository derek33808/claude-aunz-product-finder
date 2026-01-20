"""Reports API routes - Report generation and management."""

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import secrets
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks

from app.database import get_db
from app.models.schemas import (
    ReportCreate,
    ReportResponse,
    ReportProgress,
    ShareLinkCreate,
    ShareLinkResponse,
)
from app.services.report_generator import ReportGenerator

router = APIRouter()


@router.post("/generate", response_model=ReportProgress)
async def generate_report(
    report_data: ReportCreate,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
):
    """
    Generate a new product selection report.
    
    - **report_type**: quick, full, comparison, or monitor
    - **target_type**: product, keyword, or category
    - **target_value**: The ID, keyword, or category name to analyze
    """
    # Create report record
    report_id = str(uuid4())
    title = report_data.title or f"{report_data.target_type.title()} Report - {report_data.target_value}"
    
    report = {
        "id": report_id,
        "title": title,
        "report_type": report_data.report_type,
        "status": "pending",
        "progress": 0,
        "target_type": report_data.target_type,
        "target_value": report_data.target_value,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    db.table("reports").insert(report).execute()
    
    # Start generation in background
    generator = ReportGenerator(db)
    background_tasks.add_task(
        generator.generate_report,
        report_id=report_id,
        report_type=report_data.report_type,
        target_type=report_data.target_type,
        target_value=report_data.target_value,
        options=report_data.options or {},
    )
    
    return ReportProgress(
        id=UUID(report_id),
        status="pending",
        progress=0,
        current_step="Initializing...",
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    db=Depends(get_db),
):
    """Get report by ID."""
    result = db.table("reports").select("*").eq("id", str(report_id)).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return result.data[0]


@router.get("/{report_id}/status", response_model=ReportProgress)
async def get_report_status(
    report_id: UUID,
    db=Depends(get_db),
):
    """Get report generation status."""
    result = db.table("reports")\
        .select("id, status, progress")\
        .eq("id", str(report_id))\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Report not found")
    
    data = result.data[0]
    
    # Map progress to current step
    progress = data.get("progress", 0)
    step_map = {
        0: "Initializing...",
        10: "Fetching product data...",
        30: "Analyzing Google Trends...",
        50: "Analyzing competition...",
        70: "Calculating profit estimates...",
        85: "Generating report files...",
        100: "Completed",
    }
    
    current_step = "Processing..."
    for threshold, step in sorted(step_map.items()):
        if progress >= threshold:
            current_step = step
    
    return ReportProgress(
        id=UUID(data["id"]),
        status=data["status"],
        progress=progress,
        current_step=current_step,
    )


@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    report_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    """List all reports with optional filters."""
    query = db.table("reports").select("*")
    
    if report_type:
        query = query.eq("report_type", report_type)
    if status:
        query = query.eq("status", status)
    
    # Pagination
    offset = (page - 1) * page_size
    query = query.order("created_at", desc=True).range(offset, offset + page_size - 1)
    
    result = query.execute()
    return result.data


@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID,
    format: str = Query("pdf", regex="^(pdf|excel)$"),
    db=Depends(get_db),
):
    """Get download URL for report file."""
    result = db.table("reports")\
        .select("pdf_path, excel_path")\
        .eq("id", str(report_id))\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Report not found")
    
    data = result.data[0]
    file_path = data.get(f"{format}_path")
    
    if not file_path:
        raise HTTPException(
            status_code=404, 
            detail=f"{format.upper()} file not available for this report"
        )
    
    # Generate signed URL from Supabase Storage
    # For now, return the path directly
    return {"download_url": file_path, "format": format}


@router.post("/{report_id}/share", response_model=ShareLinkResponse)
async def create_share_link(
    report_id: UUID,
    share_data: ShareLinkCreate,
    db=Depends(get_db),
):
    """Create a shareable link for the report."""
    # Check report exists
    result = db.table("reports").select("id").eq("id", str(report_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Generate share token
    share_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=share_data.expires_in_days)
    
    # Update report with share info
    update_data = {
        "share_token": share_token,
        "share_expires_at": expires_at.isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    db.table("reports").update(update_data).eq("id", str(report_id)).execute()
    
    # Construct share URL (frontend URL)
    share_url = f"/reports/shared/{share_token}"
    
    return ShareLinkResponse(
        share_url=share_url,
        expires_at=expires_at,
        has_password=share_data.password is not None,
    )


@router.get("/shared/{share_token}", response_model=ReportResponse)
async def get_shared_report(
    share_token: str,
    password: Optional[str] = None,
    db=Depends(get_db),
):
    """Access a shared report by token."""
    result = db.table("reports")\
        .select("*")\
        .eq("share_token", share_token)\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Shared report not found")
    
    report = result.data[0]
    
    # Check expiration
    if report.get("share_expires_at"):
        expires_at = datetime.fromisoformat(report["share_expires_at"].replace("Z", "+00:00"))
        if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
            raise HTTPException(status_code=410, detail="Share link has expired")
    
    return report


@router.delete("/{report_id}")
async def delete_report(
    report_id: UUID,
    db=Depends(get_db),
):
    """Delete a report."""
    result = db.table("reports").delete().eq("id", str(report_id)).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {"message": "Report deleted successfully"}

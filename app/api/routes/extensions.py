"""
API Routes for E-way Bill Extensions
Integrated with existing automation system
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
import json
import csv
from pathlib import Path

from app.automation.eway_automation import PlaywrightEwayAutomation
from app.core.session_manager import get_session_manager
from app.core.logging import logger, log_operation
from app.core.config import settings

router = APIRouter()

# Request Models
class SingleExtensionRequest(BaseModel):
    ewb_number: str
    new_destination: str
    transport_mode: str = "Road"
    vehicle_number: Optional[str] = ""

class CSVExtensionRequest(BaseModel):
    csv_data: List[Dict[str, str]]

class AutoExtendRequest(BaseModel):
    days_threshold: int = 1
    default_destination: str

class ExtensionStatusRequest(BaseModel):
    operation_id: Optional[str] = None

# Response Models
class ExtensionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    operation_id: Optional[str] = None

@router.get("/status")
async def extension_system_status():
    """
    Get extension system status and capabilities
    """
    try:
        log_operation("EXTENSION_STATUS", "Checking extension system status")
        
        # Check if there's an active session
        session_manager = get_session_manager()
        sessions = session_manager.list_sessions()
        active_sessions = [s for s in sessions if not s.is_expired()]
        
        status = {
            "extension_system": "operational",
            "timestamp": datetime.now().isoformat(),
            "active_sessions": len(active_sessions),
            "features": {
                "single_extension": True,
                "csv_bulk_extension": True,
                "auto_extend_expiring": True,
                "session_integration": True,
                "history_tracking": True
            },
            "supported_transport_modes": ["Road", "Rail", "Air", "Ship"],
            "endpoints": {
                "single_extension": "/api/extensions/single",
                "csv_extension": "/api/extensions/csv",
                "auto_extend": "/api/extensions/auto-extend",
                "history": "/api/extensions/history"
            }
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Extension status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.post("/single", response_model=ExtensionResponse)
async def extend_single_eway_bill(request: SingleExtensionRequest):
    """
    Extend a single E-way bill
    Option 1: Manual single extension
    """
    try:
        log_operation("SINGLE_EXTENSION", f"Extending EWB: {request.ewb_number}")
        
        # Check for active session
        session_manager = get_session_manager()
        sessions = session_manager.list_sessions()
        active_sessions = [s for s in sessions if not s.is_expired()]
        
        if not active_sessions:
            raise HTTPException(
                status_code=400, 
                detail="No active session found. Please login first."
            )
        
        # Use existing automation with session
        automation = PlaywrightEwayAutomation()
        
        # Load the latest session
        latest_session = max(active_sessions, key=lambda x: x.created_at)
        session_result = await automation.load_saved_session(latest_session.session_id)
        
        if not session_result["success"]:
            raise HTTPException(
                status_code=400,
                detail="Failed to load session. Please login again."
            )
        
        # Perform extension
        result = await automation.extend_single_eway_bill(
            ewb_number=request.ewb_number,
            new_destination=request.new_destination,
            transport_mode=request.transport_mode,
            vehicle_number=request.vehicle_number
        )
        
        # Close browser if not in debug mode
        if not settings.debug:
            await automation.close_browser()
        
        return ExtensionResponse(
            success=result.success,
            message=result.message,
            data=result.data,
            operation_id=f"single_{request.ewb_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Single extension API failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Extension failed: {str(e)}")

@router.post("/csv")
async def extend_from_csv(file: UploadFile = File(...)):
    """
    Extend multiple E-way bills from CSV upload
    Option 2: CSV bulk processing
    """
    try:
        log_operation("CSV_EXTENSION", f"Processing CSV file: {file.filename}")
        
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        # Check for active session
        session_manager = get_session_manager()
        sessions = session_manager.list_sessions()
        active_sessions = [s for s in sessions if not s.is_expired()]
        
        if not active_sessions:
            raise HTTPException(
                status_code=400,
                detail="No active session found. Please login first."
            )
        
        # Save uploaded file temporarily
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(exist_ok=True)
        
        file_path = upload_dir / f"csv_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Use existing automation with session
        automation = PlaywrightEwayAutomation()
        
        # Load the latest session
        latest_session = max(active_sessions, key=lambda x: x.created_at)
        session_result = await automation.load_saved_session(latest_session.session_id)
        
        if not session_result["success"]:
            raise HTTPException(
                status_code=400,
                detail="Failed to load session. Please login again."
            )
        
        # Process CSV
        result = await automation.extend_from_csv_file(str(file_path))
        
        # Clean up uploaded file
        try:
            file_path.unlink()
        except:
            pass
        
        # Close browser if not in debug mode
        if not settings.debug:
            await automation.close_browser()
        
        return ExtensionResponse(
            success=result.success,
            message=result.message,
            data=result.data,
            operation_id=f"csv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV extension API failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CSV processing failed: {str(e)}")

@router.post("/csv-data")
async def extend_from_csv_data(request: CSVExtensionRequest):
    """
    Extend multiple E-way bills from JSON data
    Alternative to file upload
    """
    try:
        log_operation("CSV_DATA_EXTENSION", f"Processing {len(request.csv_data)} records")
        
        # Check for active session
        session_manager = get_session_manager()
        sessions = session_manager.list_sessions()
        active_sessions = [s for s in sessions if not s.is_expired()]
        
        if not active_sessions:
            raise HTTPException(
                status_code=400,
                detail="No active session found. Please login first."
            )
        
        # Validate data structure
        if not request.csv_data:
            raise HTTPException(status_code=400, detail="No data provided")
        
        required_fields = ['ewb_number', 'new_destination']
        first_record = request.csv_data[0]
        missing_fields = [field for field in required_fields if field not in first_record]
        
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {missing_fields}"
            )
        
        # Create temporary CSV file
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(exist_ok=True)
        
        csv_path = upload_dir / f"data_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Write JSON data to CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            if request.csv_data:
                fieldnames = request.csv_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(request.csv_data)
        
        # Use existing automation with session
        automation = PlaywrightEwayAutomation()
        
        # Load the latest session
        latest_session = max(active_sessions, key=lambda x: x.created_at)
        session_result = await automation.load_saved_session(latest_session.session_id)
        
        if not session_result["success"]:
            raise HTTPException(
                status_code=400,
                detail="Failed to load session. Please login again."
            )
        
        # Process CSV
        result = await automation.extend_from_csv_file(str(csv_path))
        
        # Clean up temporary file
        try:
            csv_path.unlink()
        except:
            pass
        
        # Close browser if not in debug mode
        if not settings.debug:
            await automation.close_browser()
        
        return ExtensionResponse(
            success=result.success,
            message=result.message,
            data=result.data,
            operation_id=f"csv_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV data extension API failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Data processing failed: {str(e)}")

@router.post("/auto-extend", response_model=ExtensionResponse)
async def auto_extend_expiring_bills(request: AutoExtendRequest):
    """
    Auto-extend expiring E-way bills
    Option 3: Download report, filter expiring, and extend
    """
    try:
        log_operation("AUTO_EXTEND", f"Auto-extending bills expiring within {request.days_threshold} days")
        
        # Check for active session
        session_manager = get_session_manager()
        sessions = session_manager.list_sessions()
        active_sessions = [s for s in sessions if not s.is_expired()]
        
        if not active_sessions:
            raise HTTPException(
                status_code=400,
                detail="No active session found. Please login first."
            )
        
        # Use existing automation with session
        automation = PlaywrightEwayAutomation()
        
        # Load the latest session
        latest_session = max(active_sessions, key=lambda x: x.created_at)
        session_result = await automation.load_saved_session(latest_session.session_id)
        
        if not session_result["success"]:
            raise HTTPException(
                status_code=400,
                detail="Failed to load session. Please login again."
            )
        
        # Perform auto-extension
        result = await automation.auto_extend_expiring_bills(
            days_threshold=request.days_threshold,
            default_destination=request.default_destination
        )
        
        # Close browser if not in debug mode
        if not settings.debug:
            await automation.close_browser()
        
        return ExtensionResponse(
            success=result.success,
            message=result.message,
            data=result.data,
            operation_id=f"auto_extend_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auto-extend API failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Auto-extend failed: {str(e)}")

@router.get("/history")
async def get_extension_history(limit: int = 10):
    """
    Get extension operation history
    """
    try:
        log_operation("EXTENSION_HISTORY", "Retrieving extension history")
        
        # Look for result files in data directory
        data_dir = Path("data")
        if not data_dir.exists():
            return {
                "success": True,
                "message": "No extension history found",
                "history": []
            }
        
        # Find extension result files
        result_files = list(data_dir.glob("*extension_results_*.json"))
        
        if not result_files:
            return {
                "success": True,
                "message": "No extension history found",
                "history": []
            }
        
        # Sort by creation time (newest first)
        result_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        history = []
        for result_file in result_files[:limit]:
            try:
                with open(result_file, 'r') as f:
                    data = json.load(f)
                
                # Get file stats
                stat = result_file.stat()
                
                history.append({
                    "filename": result_file.name,
                    "timestamp": data.get("timestamp", ""),
                    "type": "csv" if "csv" in result_file.name else "auto" if "auto" in result_file.name else "single",
                    "total_records": data.get("total_records", data.get("total_expiring", 0)),
                    "successful": data.get("successful", 0),
                    "failed": data.get("failed", 0),
                    "file_size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
                
            except Exception as e:
                logger.warning(f"Could not read result file {result_file}: {str(e)}")
                continue
        
        return {
            "success": True,
            "message": f"Found {len(history)} extension operations",
            "history": history,
            "total_files": len(result_files)
        }
        
    except Exception as e:
        logger.error(f"Extension history API failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")

@router.get("/history/{filename}")
async def get_extension_details(filename: str):
    """
    Get detailed results for a specific extension operation
    """
    try:
        log_operation("EXTENSION_DETAILS", f"Retrieving details for: {filename}")
        
        # Validate filename
        if not filename.endswith('.json') or '..' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        data_dir = Path("data")
        result_file = data_dir / filename
        
        if not result_file.exists():
            raise HTTPException(status_code=404, detail="Extension result not found")
        
        # Read and return the detailed results
        with open(result_file, 'r') as f:
            data = json.load(f)
        
        return {
            "success": True,
            "message": "Extension details retrieved",
            "details": data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extension details API failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Details retrieval failed: {str(e)}")

@router.delete("/history/{filename}")
async def delete_extension_result(filename: str):
    """
    Delete a specific extension result file
    """
    try:
        log_operation("DELETE_EXTENSION_RESULT", f"Deleting: {filename}")
        
        # Validate filename
        if not filename.endswith('.json') or '..' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        data_dir = Path("data")
        result_file = data_dir / filename
        
        if not result_file.exists():
            raise HTTPException(status_code=404, detail="Extension result not found")
        
        # Delete the file
        result_file.unlink()
        
        return {
            "success": True,
            "message": f"Extension result {filename} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete extension result API failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.get("/templates/csv")
async def get_csv_template():
    """
    Get CSV template for bulk extension
    """
    try:
        template = {
            "format": "CSV",
            "required_columns": ["ewb_number", "new_destination"],
            "optional_columns": ["transport_mode", "vehicle_number"],
            "example": [
                {
                    "ewb_number": "391234567890",
                    "new_destination": "New Delhi",
                    "transport_mode": "Road",
                    "vehicle_number": "DL01AB1234"
                },
                {
                    "ewb_number": "391234567891",
                    "new_destination": "Mumbai",
                    "transport_mode": "Rail",
                    "vehicle_number": ""
                }
            ],
            "notes": [
                "ewb_number: E-way bill number to extend",
                "new_destination: New destination for the E-way bill",
                "transport_mode: Road, Rail, Air, or Ship (default: Road)",
                "vehicle_number: Required for Road transport, optional for others"
            ]
        }
        
        return {
            "success": True,
            "message": "CSV template retrieved",
            "template": template
        }
        
    except Exception as e:
        logger.error(f"CSV template API failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Template retrieval failed: {str(e)}")
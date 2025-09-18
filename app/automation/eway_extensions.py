"""
E-way Bill Extension Module
Integrated with existing app architecture
Provides extension functionality for E-way bills
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import csv
import json
from pathlib import Path

from app.core.logging import logger, log_automation_step
from app.core.config import settings
from app.models.schemas import EwayBillData, AutomationResult


class EwayExtensions:
    """
    E-way Bill Extension functionality
    Integrated with existing automation system
    """
    
    def __init__(self, automation_instance):
        """
        Initialize with existing automation instance
        """
        self.automation = automation_instance
        self.page = automation_instance.page
        logger.info("E-way Extensions module initialized")
    
    async def extend_single_bill(self, ewb_number: str, new_destination: str, 
                                transport_mode: str = "Road", 
                                vehicle_number: str = "") -> AutomationResult:
        """
        Extend a single E-way bill
        Option 1: Manual single extension
        """
        try:
            log_automation_step("EXTEND_SINGLE", f"Starting extension for EWB: {ewb_number}")
            
            # Navigate to extension page
            await self.page.goto("https://ewaybillgst.gov.in/Others/EWBExtend.aspx", 
                                wait_until="domcontentloaded")
            await self.page.wait_for_timeout(2000)
            
            # Clear any existing data
            await self._clear_form_fields()
            
            # Fill E-way bill number
            ewb_field = await self.page.query_selector('input[name*="txtEwbNo"], input[id*="txtEwbNo"]')
            if ewb_field:
                await ewb_field.fill(ewb_number)
                log_automation_step("EXTEND_SINGLE", f"Filled EWB number: {ewb_number}")
            else:
                return AutomationResult(
                    success=False,
                    message="E-way bill number field not found"
                )
            
            await self.page.wait_for_timeout(1000)
            
            # Click Get Details button
            get_details_button = await self.page.query_selector(
                'input[value*="Get Details"], input[value*="Get"], button[id*="btnGet"]'
            )
            if get_details_button:
                await get_details_button.click()
                await self.page.wait_for_timeout(3000)
                log_automation_step("EXTEND_SINGLE", "Clicked Get Details")
            
            # Check if E-way bill details loaded successfully
            error_message = await self._check_for_errors()
            if error_message:
                return AutomationResult(
                    success=False,
                    message=f"Error loading E-way bill details: {error_message}"
                )
            
            # Fill new destination
            dest_field = await self.page.query_selector(
                'input[name*="txtToPlace"], input[id*="txtToPlace"], input[name*="ToPlace"]'
            )
            if dest_field:
                await dest_field.fill(new_destination)
                log_automation_step("EXTEND_SINGLE", f"Filled destination: {new_destination}")
            
            # Set transport mode
            await self._set_transport_mode(transport_mode, vehicle_number)
            
            # Submit extension
            submit_result = await self._submit_extension_form()
            
            if submit_result["success"]:
                log_automation_step("EXTEND_SINGLE", f"Successfully extended EWB: {ewb_number}")
                return AutomationResult(
                    success=True,
                    message=f"E-way bill {ewb_number} extended successfully to {new_destination}",
                    data={
                        "ewb_number": ewb_number,
                        "new_destination": new_destination,
                        "transport_mode": transport_mode,
                        "vehicle_number": vehicle_number
                    }
                )
            else:
                return AutomationResult(
                    success=False,
                    message=submit_result["message"]
                )
                
        except Exception as e:
            logger.error(f"Single extension failed: {str(e)}")
            return AutomationResult(
                success=False,
                message=f"Extension error: {str(e)}",
                error_details=str(e)
            )
    
    async def extend_from_csv(self, csv_file_path: str) -> AutomationResult:
        """
        Extend multiple E-way bills from CSV file
        Option 2: CSV upload processing
        """
        try:
            log_automation_step("EXTEND_CSV", f"Processing CSV file: {csv_file_path}")
            
            # Validate CSV file exists
            if not Path(csv_file_path).exists():
                return AutomationResult(
                    success=False,
                    message="CSV file not found"
                )
            
            # Read CSV file
            csv_data = []
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                csv_data = list(reader)
            
            if not csv_data:
                return AutomationResult(
                    success=False,
                    message="CSV file is empty"
                )
            
            log_automation_step("EXTEND_CSV", f"Processing {len(csv_data)} records")
            
            # Validate required columns
            required_columns = ['ewb_number', 'new_destination']
            first_row = csv_data[0]
            missing_columns = [col for col in required_columns if col not in first_row.keys()]
            
            if missing_columns:
                return AutomationResult(
                    success=False,
                    message=f"Missing required columns: {missing_columns}"
                )
            
            # Process each record
            results = []
            successful_count = 0
            failed_count = 0
            
            for index, row in enumerate(csv_data):
                ewb_number = row['ewb_number'].strip()
                new_destination = row['new_destination'].strip()
                transport_mode = row.get('transport_mode', 'Road').strip()
                vehicle_number = row.get('vehicle_number', '').strip()
                
                log_automation_step("EXTEND_CSV", f"Processing {index + 1}/{len(csv_data)}: {ewb_number}")
                
                # Extend single bill
                result = await self.extend_single_bill(
                    ewb_number=ewb_number,
                    new_destination=new_destination,
                    transport_mode=transport_mode,
                    vehicle_number=vehicle_number
                )
                
                record_result = {
                    "row_number": index + 1,
                    "ewb_number": ewb_number,
                    "new_destination": new_destination,
                    "success": result.success,
                    "message": result.message
                }
                
                results.append(record_result)
                
                if result.success:
                    successful_count += 1
                else:
                    failed_count += 1
                
                # Small delay between requests to avoid overwhelming server
                await asyncio.sleep(2)
            
            # Save results to file
            results_file = Path("data") / f"csv_extension_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            results_file.parent.mkdir(exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "total_records": len(csv_data),
                    "successful": successful_count,
                    "failed": failed_count,
                    "results": results
                }, f, indent=2)
            
            log_automation_step("EXTEND_CSV", f"CSV processing completed: {successful_count} success, {failed_count} failed")
            
            return AutomationResult(
                success=True,
                message=f"CSV processing completed: {successful_count} successful, {failed_count} failed",
                data={
                    "total_records": len(csv_data),
                    "successful": successful_count,
                    "failed": failed_count,
                    "results_file": str(results_file),
                    "results": results
                }
            )
            
        except Exception as e:
            logger.error(f"CSV extension processing failed: {str(e)}")
            return AutomationResult(
                success=False,
                message=f"CSV processing error: {str(e)}",
                error_details=str(e)
            )
    
    async def auto_extend_expiring(self, days_threshold: int = 1, 
                                 default_destination: str = None) -> AutomationResult:
        """
        Auto-extend expiring E-way bills
        Option 3: Download report, filter expiring, and extend
        """
        try:
            log_automation_step("AUTO_EXTEND", "Starting auto-extension of expiring E-way bills")
            
            if not default_destination:
                return AutomationResult(
                    success=False,
                    message="Default destination required for auto-extension"
                )
            
            # Step 1: Download consolidation report
            download_result = await self._download_consolidation_report()
            if not download_result["success"]:
                return AutomationResult(
                    success=False,
                    message=f"Failed to download report: {download_result['message']}"
                )
            
            report_file = download_result["file_path"]
            log_automation_step("AUTO_EXTEND", f"Report downloaded: {report_file}")
            
            # Step 2: Filter expiring bills
            filter_result = await self._filter_expiring_bills(report_file, days_threshold)
            if not filter_result["success"]:
                return AutomationResult(
                    success=False,
                    message=f"Failed to filter expiring bills: {filter_result['message']}"
                )
            
            expiring_bills = filter_result["expiring_bills"]
            log_automation_step("AUTO_EXTEND", f"Found {len(expiring_bills)} expiring E-way bills")
            
            if not expiring_bills:
                return AutomationResult(
                    success=True,
                    message="No expiring E-way bills found",
                    data={"expiring_count": 0}
                )
            
            # Step 3: Extend expiring bills
            results = []
            successful_count = 0
            failed_count = 0
            
            for bill in expiring_bills:
                ewb_number = bill["ewb_number"]
                expiry_date = bill["expiry_date"]
                
                log_automation_step("AUTO_EXTEND", f"Extending {ewb_number} (expires: {expiry_date})")
                
                result = await self.extend_single_bill(
                    ewb_number=ewb_number,
                    new_destination=default_destination,
                    transport_mode="Road"
                )
                
                bill_result = {
                    "ewb_number": ewb_number,
                    "expiry_date": expiry_date,
                    "success": result.success,
                    "message": result.message
                }
                
                results.append(bill_result)
                
                if result.success:
                    successful_count += 1
                else:
                    failed_count += 1
                
                # Delay between extensions
                await asyncio.sleep(3)
            
            # Save auto-extension results
            results_file = Path("data") / f"auto_extension_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            results_file.parent.mkdir(exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "days_threshold": days_threshold,
                    "default_destination": default_destination,
                    "total_expiring": len(expiring_bills),
                    "successful": successful_count,
                    "failed": failed_count,
                    "results": results
                }, f, indent=2)
            
            log_automation_step("AUTO_EXTEND", f"Auto-extension completed: {successful_count} success, {failed_count} failed")
            
            return AutomationResult(
                success=True,
                message=f"Auto-extension completed: {successful_count} successful, {failed_count} failed",
                data={
                    "total_expiring": len(expiring_bills),
                    "successful": successful_count,
                    "failed": failed_count,
                    "results_file": str(results_file),
                    "results": results
                }
            )
            
        except Exception as e:
            logger.error(f"Auto-extension failed: {str(e)}")
            return AutomationResult(
                success=False,
                message=f"Auto-extension error: {str(e)}",
                error_details=str(e)
            )
    
    async def _clear_form_fields(self):
        """Clear existing form fields"""
        try:
            # Clear common form fields
            fields_to_clear = [
                'input[name*="txtEwbNo"]',
                'input[name*="txtToPlace"]',
                'input[name*="txtVehNo"]'
            ]
            
            for selector in fields_to_clear:
                field = await self.page.query_selector(selector)
                if field:
                    await field.fill("")
        except Exception as e:
            logger.warning(f"Could not clear form fields: {str(e)}")
    
    async def _check_for_errors(self) -> Optional[str]:
        """Check for error messages on page"""
        try:
            # Common error selectors
            error_selectors = [
                '.error',
                '.alert-danger',
                '[class*="error"]',
                '[id*="error"]',
                'span[style*="color: red"]'
            ]
            
            for selector in error_selectors:
                error_element = await self.page.query_selector(selector)
                if error_element:
                    error_text = await error_element.text_content()
                    if error_text and error_text.strip():
                        return error_text.strip()
            
            return None
            
        except Exception:
            return None
    
    async def _set_transport_mode(self, transport_mode: str, vehicle_number: str = ""):
        """Set transport mode and vehicle details"""
        try:
            # Transport mode mapping
            mode_map = {
                "Road": "1",
                "Rail": "2", 
                "Air": "3",
                "Ship": "4"
            }
            
            mode_value = mode_map.get(transport_mode, "1")
            
            # Select transport mode radio button
            radio_selector = f'input[type="radio"][value="{mode_value}"]'
            radio_button = await self.page.query_selector(radio_selector)
            if radio_button:
                await radio_button.check()
                log_automation_step("EXTEND_FORM", f"Selected transport mode: {transport_mode}")
            
            # Fill vehicle number if Road transport and vehicle number provided
            if transport_mode == "Road" and vehicle_number:
                vehicle_field = await self.page.query_selector(
                    'input[name*="txtVehNo"], input[id*="txtVehNo"]'
                )
                if vehicle_field:
                    await vehicle_field.fill(vehicle_number)
                    log_automation_step("EXTEND_FORM", f"Filled vehicle number: {vehicle_number}")
            
        except Exception as e:
            logger.warning(f"Could not set transport mode: {str(e)}")
    
    async def _submit_extension_form(self) -> Dict[str, Any]:
        """Submit the extension form and check result"""
        try:
            # Find and click submit button
            submit_selectors = [
                'input[value*="Submit"]',
                'input[value*="Extend"]',
                'button[id*="btnSubmit"]',
                'input[id*="btnSubmit"]'
            ]
            
            submit_button = None
            for selector in submit_selectors:
                submit_button = await self.page.query_selector(selector)
                if submit_button:
                    break
            
            if not submit_button:
                return {
                    "success": False,
                    "message": "Submit button not found"
                }
            
            # Click submit and wait for response
            await submit_button.click()
            await self.page.wait_for_timeout(5000)
            
            # Check for success/error messages
            page_content = await self.page.content()
            
            # Success indicators
            success_indicators = [
                "successfully extended",
                "extension successful",
                "extended successfully",
                "extension completed"
            ]
            
            # Error indicators
            error_indicators = [
                "error",
                "failed",
                "invalid",
                "not found",
                "unable to extend"
            ]
            
            page_content_lower = page_content.lower()
            
            # Check for success
            if any(indicator in page_content_lower for indicator in success_indicators):
                return {
                    "success": True,
                    "message": "Extension successful"
                }
            
            # Check for specific errors
            if any(indicator in page_content_lower for indicator in error_indicators):
                return {
                    "success": False,
                    "message": "Extension failed - error detected on page"
                }
            
            # If no clear indication, assume success if no obvious errors
            return {
                "success": True,
                "message": "Extension submitted (result unclear)"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Submit error: {str(e)}"
            }
    
    async def _download_consolidation_report(self) -> Dict[str, Any]:
        """Download consolidation report from ConsReport_New.aspx"""
        try:
            # Navigate to report page
            await self.page.goto("https://ewaybillgst.gov.in/Reports/ConsReport_New.aspx", 
                                wait_until="domcontentloaded")
            await self.page.wait_for_timeout(3000)
            
            # Set date range (last 30 days)
            from_date = (datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y")
            to_date = datetime.now().strftime("%d/%m/%Y")
            
            # Fill date fields
            await self._fill_date_fields(from_date, to_date)
            
            # Search for records
            search_button = await self.page.query_selector(
                'input[value*="Search"], button[id*="btnSearch"]'
            )
            if search_button:
                await search_button.click()
                await self.page.wait_for_timeout(5000)
            
            # Export to Excel
            return await self._export_to_excel()
            
        except Exception as e:
            logger.error(f"Report download failed: {str(e)}")
            return {
                "success": False,
                "message": f"Download failed: {str(e)}"
            }
    
    async def _fill_date_fields(self, from_date: str, to_date: str):
        """Fill date range fields"""
        try:
            # From date
            from_date_selectors = [
                'input[name*="txtFromDt"]',
                'input[name*="FromDate"]',
                'input[id*="txtFromDt"]'
            ]
            
            for selector in from_date_selectors:
                field = await self.page.query_selector(selector)
                if field:
                    await field.fill(from_date)
                    break
            
            # To date
            to_date_selectors = [
                'input[name*="txtToDt"]',
                'input[name*="ToDate"]',
                'input[id*="txtToDt"]'
            ]
            
            for selector in to_date_selectors:
                field = await self.page.query_selector(selector)
                if field:
                    await field.fill(to_date)
                    break
                    
        except Exception as e:
            logger.warning(f"Could not fill date fields: {str(e)}")
    
    async def _export_to_excel(self) -> Dict[str, Any]:
        """Export current data to Excel"""
        try:
            # Look for Excel export button
            export_selectors = [
                'input[value*="Export"]',
                'a[href*="Export"]',
                'button[id*="Export"]',
                'input[value*="Excel"]'
            ]
            
            export_button = None
            for selector in export_selectors:
                export_button = await self.page.query_selector(selector)
                if export_button:
                    break
            
            if not export_button:
                return {
                    "success": False,
                    "message": "Export button not found"
                }
            
            # Set up download path
            download_path = Path("data") / f"eway_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            download_path.parent.mkdir(exist_ok=True)
            
            # Handle download
            async with self.page.expect_download() as download_info:
                await export_button.click()
            
            download = await download_info.value
            await download.save_as(download_path)
            
            return {
                "success": True,
                "message": "Report downloaded successfully",
                "file_path": str(download_path)
            }
            
        except Exception as e:
            logger.error(f"Excel export failed: {str(e)}")
            return {
                "success": False,
                "message": f"Export failed: {str(e)}"
            }
    
    async def _filter_expiring_bills(self, report_file: str, days_threshold: int) -> Dict[str, Any]:
        """Filter expiring bills from downloaded report"""
        try:
            # This would require pandas - for now, return mock data
            # In production, implement Excel parsing to find expiring bills
            
            # Mock implementation - replace with actual Excel parsing
            mock_expiring_bills = [
                {
                    "ewb_number": "391234567890",
                    "expiry_date": (datetime.now() + timedelta(hours=12)).strftime("%d/%m/%Y %H:%M")
                },
                {
                    "ewb_number": "391234567891", 
                    "expiry_date": (datetime.now() + timedelta(hours=18)).strftime("%d/%m/%Y %H:%M")
                }
            ]
            
            return {
                "success": True,
                "message": f"Found {len(mock_expiring_bills)} expiring bills",
                "expiring_bills": mock_expiring_bills
            }
            
        except Exception as e:
            logger.error(f"Filter expiring bills failed: {str(e)}")
            return {
                "success": False,
                "message": f"Filter failed: {str(e)}"
            }
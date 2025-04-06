import httpx
import os
from datetime import datetime
from typing import List, Optional, Dict, Any, BinaryIO


class ReceiptApiClient:
    """Service for interacting with the Receipt Analyzer API."""
    
    def __init__(
            self,
            base_url: str = None,
            timeout: float = 60.0,
            verify_ssl: bool = True):
        """
        Initialize the Receipt API Service.
        
        Args:
            base_url: Base URL for the Receipt Analyzer API. If not provided, 
                    will try to get from environment variable.
            timeout: Request timeout in seconds.
            verify_ssl: Whether to verify SSL certificates. Set to False for self-signed certs.
        """
        self.base_url = base_url or os.environ.get("RECEIPT_API_URL", "http://localhost:5000")
            
        self.client = httpx.AsyncClient(
            base_url=self.base_url, 
            timeout=timeout,
            verify=verify_ssl
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(
            self,
            exc_type,
            exc_val,
            exc_tb):
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle API response with proper error handling.
        
        Args:
            response: The httpx response object.
            
        Returns:
            Parsed JSON response or text content if not JSON.
            
        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        response.raise_for_status()
        
        try:
            return response.json()
        except ValueError:
            # If not JSON, return the text content as a dict
            return {"message": response.text, "status_code": response.status_code}
    
    async def get_version(self) -> Dict[str, Any]:
        """
        Get the API version.
        
        Returns:
            The version information from the API.
        
        Raises:
            httpx.HTTPStatusError: If the request fails.
            ValueError: If response is not valid JSON.
        """
        response = await self.client.get("/version")
        return await self._handle_response(response)
    
    async def upload_receipts(
            self,
            files: List[BinaryIO]) -> Dict[str, Any]:
        """
        Upload receipt files to the API for analysis.
        
        Args:
            files: List of file-like objects to upload.
        
        Returns:
            Response from the API as a dictionary.
        
        Raises:
            httpx.HTTPStatusError: If the request fails.
            ValueError: If response is not valid JSON.
        """
        files_dict = {f"file{i}": file for i, file in enumerate(files)}
        
        response = await self.client.post(
            "/bills",
            files=files_dict
        )
        return await self._handle_response(response)
    
    async def send_report_by_email(
            self,
            start_date: datetime,
            end_date: datetime, 
            email: str = None) -> Dict[str, Any]:
        """
        Request a report to be sent by email for a specific date range.
        
        Args:
            start_date: Start date for the report.
            end_date: End date for the report.
            email: Optional email address to send the report to.
            If not provided, will use the default email associated with the account.
        
        Returns:
            Response from the API as a dictionary.
        
        Raises:
            httpx.HTTPStatusError: If the request fails.
            ValueError: If response is not valid JSON.
        """
        payload = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat()
        }
        
        if email:
            payload["email"] = email
        
        response = await self.client.post(
            "/reports",
            json=payload
        )
        return await self._handle_response(response)
        
    async def get_receipts(
                self,
                start_date: Optional[datetime] = None, 
                end_date: Optional[datetime] = None,
                page: int = 1, 
                page_size: int = 20) -> Dict[str, Any]:
        """
        Get receipts within a date range with pagination.
        
        Args:
            start_date: Optional start date filter.
            end_date: Optional end date filter.
            page: Page number (starting from 1).
            page_size: Number of items per page.
            
        Returns:
            Paginated list of receipts.
            
        Raises:
            httpx.HTTPStatusError: If the request fails.
            ValueError: If response is not valid JSON.
        """
        params = {
            "page": page,
            "pageSize": page_size
        }
        
        if start_date:
            params["startDate"] = start_date.isoformat()
        if end_date:
            params["endDate"] = end_date.isoformat()
            
        response = await self.client.get("/bills", params=params)
        return await self._handle_response(response)
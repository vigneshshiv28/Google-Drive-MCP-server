import os
from typing import Any, Dict, Union
import httpx
from mcp.server.fastmcp import FastMCP
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import asyncio
import logging
import json


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def success_response(data: Any) -> Dict[str, Any]:
    return {
        "status": "success",
        "data": data
    }

def error_response(message: str, code: int = 500) -> Dict[str, Any]:
    return {
        "status": "error",
        "error": {
            "message": message,
            "code": code
        }
    }

class GoogleDriveAgent:
    SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

    def __init__(self):
        self.service = self._authenticate_gdrive()
        self.mcp = FastMCP("gdrive")
        self._register_tools()

    def _authenticate_gdrive(self):
        creds = None
        if os.path.exists("token.json"):
            logging.info("Loading existing credentials from token.json")
            creds = Credentials.from_authorized_user_file("token.json", self.SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logging.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                logging.info("Creating new credentials")
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", self.SCOPES)
                creds = flow.run_local_server(port=0)

            with open("token.json", "w") as token:
                token.write(creds.to_json())
        logging.info("Authenticated with Google Drive API")
        return build("drive", "v3", credentials=creds)

    def _register_tools(self):

        self.mcp.tool()(self.list_files)

    async def list_files(
        self,
        page_size: int = 10,
        page_token: str = None
    ) -> Dict[str, Any]:

        logging.info(f"Listing Google Drive files with page_size={page_size}, page_token={page_token}")
        
        params = {
            "pageSize": page_size,
            "fields": "nextPageToken, files(id, name, mimeType)",
        }

        if page_token:
            params["pageToken"] = page_token

        try:
            results = self.service.files().list(**params).execute()
            items = results.get("files", [])
            next_page_token = results.get("nextPageToken")
            
            logging.info(f"Found {len(items)} files")

            files = []
            for item in items:
                files.append({
                    "id": item["id"],
                    "name": item["name"],
                    "mimeType": item["mimeType"]
                })

            return success_response({
                "files": files,
                "nextPageToken": next_page_token,
                "totalFiles": len(files)
            })
            
        except HttpError as error:
            logging.error(f"Google Drive API error: {error.resp.status} - {error.content.decode()}")
            return error_response(
                message=f"Google Drive API error: {error.content.decode()}",
                code=error.resp.status
            )
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return error_response(message=f"An unexpected error occurred: {e}")

    def run(self):
        logging.info("Starting MCP server for GoogleDriveAgent")
        self.mcp.run()

if __name__ == "__main__":
    agent = GoogleDriveAgent()
    agent.run()






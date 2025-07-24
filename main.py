import os
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
import io
import asyncio
import logging
from utils.query_builder import build_query_string
from typing import List, Optional



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

class GoogleDriverMCP:
    SCOPES = ['https://www.googleapis.com/auth/drive'] 

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
        self.mcp.tool()(self.search_files)
        self.mcp.tool()(self.create_folder)
        self.mcp.tool()(self.create_folder_in_parent)
        self.mcp.tool()(self.create_file)
        self.mcp.tool()(self.upload_file_in_parent)
        self.mcp.tool()(self.move_file_to_folder)
        self.mcp.tool()(self.delete_file_or_folder)
        self.mcp.tool()(self.permanently_delete_file_or_folder)
        self.mcp.tool()(self.restore_file_or_folder)

    def list_files(
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
        
    def search_files(
        self,
        name: Optional[str] = None,
        exact_name: bool = False,
        mime_type: Optional[str] = None,
        contains_text: Optional[str] = None,
        modified_after: Optional[str] = None,
        modified_before: Optional[str] = None,
        parent_folder_id: Optional[str] = None,
        starred: Optional[bool] = None,
        trashed: bool = False,
        shared_with_me: Optional[bool] = None,
        owner_email: Optional[str] = None,
        folders_only: bool = False,
        exclude_folders: bool = False,
        limit: int = 20,
        fields: List[str] = None
    ) -> Dict[str, Any]:

        
        if fields is None:
            fields = ["id", "name", "mimeType", "modifiedTime"]
        
        logging.info(f"Searching Google Drive files with parameters")
        
        try:
            query_string = build_query_string(
                name=name,
                mime_type=mime_type,
                contains_text=contains_text,
                modified_after=modified_after,
                modified_before=modified_before,
                parent_folder_id=parent_folder_id,
                starred=starred,
                trashed=trashed,
                shared_with_me=shared_with_me,
                owner_email=owner_email,
                exact_name=exact_name,
                folders_only=folders_only,
                exclude_folders=exclude_folders
            )
            logging.info(f"Built query: {query_string}")
            
            fields_str = f"nextPageToken, files({', '.join(fields)})"
            
            files = []
            page_token = None
            
            while len(files) < limit:
                page_size = min(100, limit - len(files)) 
                
                request_params = {
                    "spaces": "drive",
                    "fields": fields_str,
                    "pageSize": page_size,
                }
                
                if page_token:
                    request_params["pageToken"] = page_token
                
                if query_string.strip():
                    request_params["q"] = query_string
                
                logging.info(f"Making API request with params: {request_params}")
                response = self.service.files().list(**request_params).execute()
                
                batch_files = response.get("files", [])
                files.extend(batch_files)
                
                page_token = response.get("nextPageToken")
                if not page_token or len(batch_files) == 0:
                    break
            
            files = files[:limit]
            
            logging.info(f"Found {len(files)} files matching search criteria")
            
            formatted_files = []
            for file in files:
                file_data = {}
                for field in fields:
                    if field in file:
                        file_data[field] = file[field]
                formatted_files.append(file_data)
            
            return success_response({
                "files": formatted_files,
                "totalFiles": len(formatted_files),
                "queryUsed": query_string if query_string.strip() else "No query (list all files)",
                "searchParameters": {
                    "name": name,
                    "mime_type": mime_type,
                    "contains_text": contains_text,
                    "modified_after": modified_after,
                    "modified_before": modified_before,
                    "starred": starred,
                    "folders_only": folders_only,
                    "exclude_folders": exclude_folders,
                    "limit": limit
                }
            })
            
        except HttpError as error:
            logging.error(f"Google Drive API error: {error.resp.status} - {error.content.decode()}")
            error_message = f"Google Drive API error: {error.content.decode()}"
            if error.resp.status == 400:
                error_message += " (This might be due to an invalid query string. Please check your search parameters.)"
            return error_response(
                message=error_message,
                code=error.resp.status
            )
        except Exception as e:
            logging.error(f"An unexpected error occurred during search: {e}")
            return error_response(message=f"An unexpected error occurred: {e}")
        
    def create_folder(
            self,
            name: str,
    )-> Dict[str, Any]:
        logging.info(f"Creating a new folder with name: {name}")

        folder_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        try: 
            folder = self.service.files().create(body=folder_metadata, fields="id").execute()

            logging.info(f"Folder created with ID: {folder['id']}")

            return success_response({
                "id": folder["id"],
                "name": name,
                "mimeType": "application/vnd.google-apps.folder"
            })
        except HttpError as error:
            logging.error(f"Google Drive API error: {error.resp.status} - {error.content.decode()}")
            return error_response(
                message=f"Google Drive API error: {error.content.decode()}",
                code=error.resp.status
            )
        except Exception as e:
            logging.error(f"An unexpected error occurred during creating folder: {e}")
            return error_response(message=f"An unexpected error occurred: {e}")
        
    def create_folder_in_parent(
            self,
            name: str,
            parent_folder_id: str
    ) -> Dict[str, Any]:
        logging.info(f"Creating folder '{name}' in parent folder with ID: {parent_folder_id}")

        folder_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_folder_id] 
        }
        try:
            folder = self.service.files().create(body=folder_metadata, fields="id, name, mimeType, parents").execute()

            logging.info(f"Folder '{name}' created with ID: {folder['id']} in parent {parent_folder_id}")

            return success_response({
                "id": folder["id"],
                "name": folder["name"],
                "mimeType": folder["mimeType"],
                "parents": folder.get("parents")
            })
        except HttpError as error:
            logging.error(f"Google Drive API error when creating folder in parent: {error.resp.status} - {error.content.decode()}")
            return error_response(
                message=f"Google Drive API error: {error.content.decode()}",
                code=error.resp.status
            )
        except Exception as e:
            logging.error(f"An unexpected error occurred during folder creation in parent: {e}")
            return error_response(message=f"An unexpected error occurred: {e}")

    def create_file(
            self,
            name: str = "Untitled",
            mime_type: str = "application/vnd.google-apps.document",
    ) -> Dict[str, Any]:
        logging.info(f"Creating a new file with name: {name} and mime_type: {mime_type}")

        file_metadata = {
            "name": name,
            "mimeType": mime_type,
        }
        try:
            file = self.service.files().create(body=file_metadata, fields="id, name, mimeType").execute()

            logging.info(f"File created with ID: {file['id']}")

            return success_response({
                "id": file["id"],
                "name": file["name"],
                "mimeType": file["mimeType"]
            })
        except HttpError as error:
            logging.error(f"Google Drive API error: {error.resp.status} - {error.content.decode()}")
            return error_response(
                message=f"Google Drive API error: {error.content.decode()}",
                code=error.resp.status
            )
        except Exception as e:
            logging.error(f"An unexpected error occurred during creating file: {e}")
            return error_response(message=f"An unexpected error occurred: {e}")
        
    def upload_file_in_parent(
        self,
        content: bytes, 
        name: str,
        mime_type: str,
        parent_folder_id: str = None
    ) -> Dict[str, Any]:

        logging.info(f"Uploading file '{name}' ({mime_type}) with provided content to parent folder ID: {parent_folder_id}")

        file_metadata = {
            "name": name,
        }

        if parent_folder_id:
            file_metadata["parents"] = [parent_folder_id]

        try:
 

            file_content_bytes = content
            media_stream = io.BytesIO(file_content_bytes)
            
            media = MediaIoBaseUpload(media_stream, mimetype=mime_type, resumable=True)

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id, name, mimeType, parents, size" 
            ).execute()

            logging.info(f"File '{name}' created with ID: {file['id']} in parent {parent_folder_id}")

            return success_response({
                "id": file["id"],
                "name": file["name"],
                "mimeType": file["mimeType"],
                "parents": file.get("parents"),
                "size": file.get("size")
            })
        except HttpError as error:
            logging.error(f"Google Drive API error when uploading file : {error.resp.status} - {error.content.decode()}")
            return error_response(
                message=f"Google Drive API error: {error.content.decode()}",
                code=error.resp.status
            )
        except Exception as e:
            logging.error(f"An unexpected error occurred during file upload : {e}")
            return error_response(message=f"An unexpected error occurred: {e}")
        
    def move_file_to_folder(
            self,
            file_id: str,
            parent_folder_id: str
    ) -> Dict[str, Any]:
        logging.info(f"Moving file with ID: {file_id} to parent folder with ID: {parent_folder_id}")
        if not file_id or not parent_folder_id:
            logging.error("File ID and parent folder ID must be provided")
            raise ValueError("File ID and parent folder ID must be provided")
        try:
            file = self.service.files().get(fileId=file_id, fields="parents").execute()
            previous_parents = ",".join(file.get("parents", []))

            self.service.files().update(
                fileId=file_id,
                addParents=parent_folder_id,
                removeParents=previous_parents,
                fields="id, parents"
            ).execute()

            logging.info(f"File {file_id} moved to folder {parent_folder_id}")

            return success_response({
                "id": file_id,
                "parents": [parent_folder_id]
            })
        except HttpError as error:
            logging.error(f"Google Drive API error when moving file: {error.resp.status} - {error.content.decode()}")
            return error_response(
                message=f"Google Drive API error: {error.content.decode()}",
                code=error.resp.status
            )
        except Exception as e:
            logging.error(f"An unexpected error occurred during moving file: {e}")
            return error_response(message=f"An unexpected error occurred: {e}")
    
    def delete_file_or_folder(
            self, 
            file_id: str, 
            is_shared_drive_file: bool = False
    ) -> Dict[str, Any]:

        logging.info(f"Trashing file/folder with ID: {file_id}")

        if not file_id:
            logging.error("File ID must be provided to trash.")
            raise ValueError("File ID must be provided.")

        try:
            body_value = {'trashed': True}
            request = self.service.files().update(
                fileId=file_id,
                body=body_value,
                fields="id, trashed, explicitlyTrashed" 
            )
            if is_shared_drive_file:
                request.supportsAllDrives(True) 

            response = request.execute()

            logging.info(f"File/folder {file_id} trashed successfully. Trashed status: {response.get('trashed')}")
            return success_response({
                "id": response.get("id"),
                "trashed": response.get("trashed"),
                "explicitlyTrashed": response.get("explicitlyTrashed")
            })
        except HttpError as error:
            logging.error(f"Google Drive API error when delete file: {error.resp.status} - {error.content.decode()}")
            if error.resp.status == 403 and "insufficientFilePermissions" in error.content.decode():
                return error_response(
                    message=f"Insufficient permissions to trash file {file_id}. Only the owner can trash a file.",
                    code=403
                )
            return error_response(
                message=f"Google Drive API error: {error.content.decode()}",
                code=error.resp.status
            )
        except Exception as e:
            logging.error(f"An unexpected error occurred during deleting file {file_id}: {e}")
            return error_response(message=f"An unexpected error occurred: {e}")
        
    def permanently_delete_file_or_folder(
            self, 
            file_id: str, 
            is_shared_drive_file: bool = False
    ) -> Dict[str, Any]:

        logging.info(f"Permanently deleting file/folder with ID: {file_id}")

        if not file_id:
            logging.error("File ID must be provided to permanently delete.")
            raise ValueError("File ID must be provided.")

        try:
            request = self.service.files().delete(fileId=file_id)
            if is_shared_drive_file:
                request.supportsAllDrives(True) 

            request.execute()

            logging.info(f"File/folder {file_id} permanently deleted successfully.")
            return success_response(message=f"File/folder {file_id} permanently deleted.")
        except HttpError as error:
            logging.error(f"Google Drive API error when permanently deleting file: {error.resp.status} - {error.content.decode()}")
            if error.resp.status == 403:
                return error_response(
                    message=f"Insufficient permissions to permanently delete file {file_id}. Organizer role is often required for shared drive items.",
                    code=403
                )
            return error_response(
                message=f"Google Drive API error: {error.content.decode()}",
                code=error.resp.status
            )
        except Exception as e:
            logging.error(f"An unexpected error occurred during permanent deletion of file {file_id}: {e}")
            return error_response(message=f"An unexpected error occurred: {e}")
    
    def restore_file_or_folder(
            self, 
            file_id: str, 
            is_shared_drive_file: bool = False
    ) -> Dict[str, Any]:

        logging.info(f"Restoring file/folder with ID: {file_id} from trash")

        if not file_id:
            logging.error("File ID must be provided to restore.")
            raise ValueError("File ID must be provided.")

        try:
            body_value = {'trashed': False}
            request = self.service.files().update(
                fileId=file_id,
                body=body_value,
                fields="id, trashed" 
            )
            if is_shared_drive_file:
                request.supportsAllDrives(True) 

            response = request.execute()

            logging.info(f"File/folder {file_id} restored successfully. Trashed status: {response.get('trashed')}")
            return success_response({
                "id": response.get("id"),
                "trashed": response.get("trashed")
            })
        except HttpError as error:
            logging.error(f"Google Drive API error when restoring file: {error.resp.status} - {error.content.decode()}")
            return error_response(
                message=f"Google Drive API error: {error.content.decode()}",
                code=error.resp.status
            )
        except Exception as e:
            logging.error(f"An unexpected error occurred during restoring file {file_id}: {e}")
            return error_response(message=f"An unexpected error occurred: {e}")
        
    
    def run(self):
        logging.info("Starting MCP server for GoogleDriveAgent")
        self.mcp.run()

if __name__ == "__main__":
    agent = GoogleDriverMCP()
    agent.run()






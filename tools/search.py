from utils.query_builder import build_query_string
from utils.response_handler import success_response, error_response
from googleapiclient.errors import HttpError
import logging

def list_files(service):
    def list_files(page_size: int = 10, page_token: str = None):
        logging.info(f"Listing Google Drive files with page_size={page_size}, page_token={page_token}")
        params = {"pageSize": page_size, "fields": "nextPageToken, files(id, name, mimeType)"}
        if page_token:
            params["pageToken"] = page_token
        try:
            results = service.files().list(**params).execute()
            items = results.get("files", [])
            next_page_token = results.get("nextPageToken")
            logging.info(f"Found {len(items)} files")
            return success_response({
                "files": items,
                "nextPageToken": next_page_token,
                "totalFiles": len(items)
            })
        except HttpError as e:
            logging.error(f"Google Drive API error: {e.resp.status} - {e.content.decode()}")
            return error_response(f"Google Drive API error: {e.content.decode()}", e.resp.status)
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return error_response(f"An unexpected error occurred: {e}")
    return list_files

def search_files(service):
    def search_files(
        name=None, exact_name=False, mime_type=None, contains_text=None,
        modified_after=None, modified_before=None, parent_folder_id=None,
        starred=None, trashed=False, shared_with_me=None, owner_email=None,
        folders_only=False, exclude_folders=False, limit=20, fields=None
    ):
        if fields is None:
            fields = ["id", "name", "mimeType", "modifiedTime"]

        logging.info(f"Searching Google Drive files with parameters")
        try:
            query_string = build_query_string(
                name=name, mime_type=mime_type, contains_text=contains_text,
                modified_after=modified_after, modified_before=modified_before,
                parent_folder_id=parent_folder_id, starred=starred, trashed=trashed,
                shared_with_me=shared_with_me, owner_email=owner_email,
                exact_name=exact_name, folders_only=folders_only, exclude_folders=exclude_folders
            )
            logging.info(f"Built query: {query_string}")
            fields_str = f"nextPageToken, files({', '.join(fields)})"
            files_list = []
            page_token = None

            while len(files_list) < limit:
                page_size = min(100, limit - len(files_list))
                request_params = {
                    "spaces": "drive", "fields": fields_str, "pageSize": page_size
                }
                if page_token:
                    request_params["pageToken"] = page_token
                if query_string.strip():
                    request_params["q"] = query_string

                response = service.files().list(**request_params).execute()
                batch = response.get("files", [])
                files_list.extend(batch)
                page_token = response.get("nextPageToken")
                if not page_token or not batch:
                    break

            formatted = [{k: f[k] for k in fields if k in f} for f in files_list[:limit]]

            logging.info(f"Found {len(formatted)} files matching search criteria")
            return success_response({
                "files": formatted,
                "totalFiles": len(formatted),
                "queryUsed": query_string or "No query (list all files)"
            })
        except HttpError as e:
            logging.error(f"Google Drive API error: {e.resp.status} - {e.content.decode()}")
            return error_response(f"Google Drive API error: {e.content.decode()}", e.resp.status)
        except Exception as e:
            logging.error(f"An unexpected error occurred during search: {e}")
            return error_response(f"An unexpected error occurred: {e}")
    return search_files
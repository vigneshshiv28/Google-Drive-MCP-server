from utils.response_handler import success_response, error_response
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
import logging
import io


def create_file(service):
    def create_file(name: str = "Untitled", mime_type: str = "application/vnd.google-apps.document"):
        logging.info(f"Creating a new file with name: {name} and mime_type: {mime_type}")
        try:
            metadata = {"name": name, "mimeType": mime_type}
            file = service.files().create(body=metadata, fields="id, name, mimeType").execute()
            logging.info(f"File created with ID: {file['id']}")
            return success_response(file)
        except HttpError as e:
            logging.error(f"Google Drive API error: {e.resp.status} - {e.content.decode()}")
            return error_response(f"Google Drive API error: {e.content.decode()}", e.resp.status)
        except Exception as e:
            logging.error(f"An unexpected error occurred during creating file: {e}")
            return error_response(f"An unexpected error occurred: {e}")
    return create_file


def upload_file_in_parent(service):
    def upload_file_in_parent(content: bytes, name: str, mime_type: str, parent_folder_id: str = None):
        logging.info(f"Uploading file '{name}' ({mime_type}) with provided content to parent folder ID: {parent_folder_id}")
        try:
            metadata = {"name": name}
            if parent_folder_id:
                metadata["parents"] = [parent_folder_id]
            media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=True)
            file = service.files().create(
                body=metadata, media_body=media, fields="id, name, mimeType, parents, size"
            ).execute()
            logging.info(f"File '{name}' created with ID: {file['id']} in parent {parent_folder_id}")
            return success_response(file)
        except HttpError as e:
            logging.error(f"Google Drive API error when uploading file : {e.resp.status} - {e.content.decode()}")
            return error_response(f"Google Drive API error: {e.content.decode()}", e.resp.status)
        except Exception as e:
            logging.error(f"An unexpected error occurred during file upload : {e}")
            return error_response(f"An unexpected error occurred: {e}")
    return upload_file_in_parent


def move_file_to_folder(service):
    def move_file_to_folder(file_id: str, parent_folder_id: str):
        logging.info(f"Moving file with ID: {file_id} to parent folder with ID: {parent_folder_id}")
        try:
            file = service.files().get(fileId=file_id, fields="parents").execute()
            previous_parents = ",".join(file.get("parents", []))
            service.files().update(
                fileId=file_id,
                addParents=parent_folder_id,
                removeParents=previous_parents,
                fields="id, parents"
            ).execute()
            logging.info(f"File {file_id} moved to folder {parent_folder_id}")
            return success_response({"id": file_id, "parents": [parent_folder_id]})
        except HttpError as e:
            logging.error(f"Google Drive API error when moving file: {e.resp.status} - {e.content.decode()}")
            return error_response(f"Google Drive API error: {e.content.decode()}", e.resp.status)
        except Exception as e:
            logging.error(f"An unexpected error occurred during moving file: {e}")
            return error_response(f"An unexpected error occurred: {e}")
    return move_file_to_folder


def delete_file_or_folder(service):
    def delete_file_or_folder(file_id: str, is_shared_drive_file: bool = False):
        logging.info(f"Trashing file/folder with ID: {file_id}")
        try:
            request = service.files().update(fileId=file_id, body={"trashed": True}, fields="id, trashed, explicitlyTrashed")
            if is_shared_drive_file:
                request.supportsAllDrives(True)
            response = request.execute()
            logging.info(f"File/folder {file_id} trashed successfully. Trashed status: {response.get('trashed')}")
            return success_response(response)
        except HttpError as e:
            logging.error(f"Google Drive API error when delete file: {e.resp.status} - {e.content.decode()}")
            return error_response(f"Google Drive API error: {e.content.decode()}", e.resp.status)
        except Exception as e:
            logging.error(f"An unexpected error occurred during deleting file {file_id}: {e}")
            return error_response(f"An unexpected error occurred: {e}")
    return delete_file_or_folder

def permanently_delete_file_or_folder(service):
    def permanently_delete_file_or_folder(file_id: str, is_shared_drive_file: bool = False):
        logging.info(f"Permanently deleting file/folder with ID: {file_id}")
        try:
            request = service.files().delete(fileId=file_id)
            if is_shared_drive_file:
                request.supportsAllDrives(True)
            request.execute()
            logging.info(f"File/folder {file_id} permanently deleted successfully.")
            return success_response({"message": f"File/folder {file_id} permanently deleted."})
        except HttpError as e:
            logging.error(f"Google Drive API error when permanently deleting file: {e.resp.status} - {e.content.decode()}")
            return error_response(f"Google Drive API error: {e.content.decode()}", e.resp.status)
        except Exception as e:
            logging.error(f"An unexpected error occurred during permanent deletion of file {file_id}: {e}")
            return error_response(f"An unexpected error occurred: {e}")
    return permanently_delete_file_or_folder

def restore_file_or_folder(service):
    def restore_file_or_folder(file_id: str, is_shared_drive_file: bool = False):
        logging.info(f"Restoring file/folder with ID: {file_id} from trash")
        try:
            request = service.files().update(fileId=file_id, body={"trashed": False}, fields="id, trashed")
            if is_shared_drive_file:
                request.supportsAllDrives(True)
            response = request.execute()
            logging.info(f"File/folder {file_id} restored successfully. Trashed status: {response.get('trashed')}")
            return success_response(response)
        except HttpError as e:
            logging.error(f"Google Drive API error when restoring file: {e.resp.status} - {e.content.decode()}")
            return error_response(f"Google Drive API error: {e.content.decode()}", e.resp.status)
        except Exception as e:
            logging.error(f"An unexpected error occurred during restoring file {file_id}: {e}")
            return error_response(f"An unexpected error occurred: {e}")
    return restore_file_or_folder

def create_folder(service):
    def create_folder(name: str):
        logging.info(f"Creating a new folder with name: {name}")
        metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
        try:
            folder = service.files().create(body=metadata, fields="id").execute()
            logging.info(f"Folder created with ID: {folder['id']}")
            return success_response({"id": folder["id"], "name": name, "mimeType": metadata["mimeType"]})
        except HttpError as e:
            logging.error(f"Google Drive API error: {e.resp.status} - {e.content.decode()}")
            return error_response(f"Google Drive API error: {e.content.decode()}", e.resp.status)
        except Exception as e:
            logging.error(f"An unexpected error occurred during creating folder: {e}")
            return error_response(f"An unexpected error occurred: {e}")
    return create_folder


def create_folder_in_parent(service):
    def create_folder_in_parent(name: str, parent_folder_id: str):
        logging.info(f"Creating folder '{name}' in parent folder with ID: {parent_folder_id}")
        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_folder_id]
        }
        try:
            folder = service.files().create(body=metadata, fields="id, name, mimeType, parents").execute()
            logging.info(f"Folder '{name}' created with ID: {folder['id']} in parent {parent_folder_id}")
            return success_response(folder)
        except HttpError as e:
            logging.error(f"Google Drive API error when creating folder in parent: {e.resp.status} - {e.content.decode()}")
            return error_response(f"Google Drive API error: {e.content.decode()}", e.resp.status)
        except Exception as e:
            logging.error(f"An unexpected error occurred during folder creation in parent: {e}")
            return error_response(f"An unexpected error occurred: {e}")
    return create_folder_in_parent
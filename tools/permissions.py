from utils.response_handler import success_response, error_response
from googleapiclient.errors import HttpError
import logging

def add_permission(service):
    def add_permission(file_id: str, email: str, role: str = "reader", permission_type: str = "user"):
        logging.info(f"Adding '{role}' permission for '{email}' ({permission_type}) to file ID: {file_id}")
        permission_body = {
            "type": permission_type,
            "role": role,
            "emailAddress": email
        }
        try:

            permission = service.permissions().create(
                fileId=file_id,
                body=permission_body,
                fields="id, type, role, emailAddress"
            ).execute()
            logging.info(f"Permission created with ID: {permission['id']}")
            return success_response(permission)
        except HttpError as e:
            logging.error(f"Google Drive API error when adding permission: {e.resp.status} - {e.content.decode()}")
            return error_response(f"Google Drive API error: {e.content.decode()}", e.resp.status)
        except Exception as e:
            logging.error(f"An unexpected error occurred during adding permission: {e}")
            return error_response(f"An unexpected error occurred: {e}")
    return add_permission

def list_permissions(service):
    def list_permissions(file_id: str):
        logging.info(f"Listing permissions for file ID: {file_id}")
        try:
            permissions = service.permissions().list(
                fileId=file_id,
                fields="permissions(id, type, role, emailAddress, displayName)"
            ).execute()
            return success_response(permissions)
        except HttpError as e:
            logging.error(f"Google Drive API error when listing permissions: {e.resp.status} - {e.content.decode()}")
            return error_response(f"Google Drive API error: {e.content.decode()}", e.resp.status)
        except Exception as e:
            logging.error(f"An unexpected error occurred during listing permissions: {e}")
            return error_response(f"An unexpected error occurred: {e}")
    return list_permissions

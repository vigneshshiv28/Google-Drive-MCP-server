from typing import Optional, Dict


def build_query_string(
        name: Optional[str] = None,
        mime_type: Optional[str] = None,
        contains_text: Optional[str] = None,
        modified_after: Optional[str] = None,
        modified_before: Optional[str] = None,
        parent_folder_id: Optional[str] = None,
        starred: Optional[bool] = None,
        trashed: Optional[bool] = None,
        shared_with_me: Optional[bool] = None,
        owner_email: Optional[str] = None,
        custom_properties: Optional[Dict[str, str]] = None,
        exact_name: bool = False,
        folders_only: bool = False,
        exclude_folders: bool = False
    ) -> str:
        query_parts = []
        
        if name:
            escaped_name = name.replace("'", "\\'").replace("\\", "\\\\")
            if exact_name:
                query_parts.append(f"name = '{escaped_name}'")
            else:
                query_parts.append(f"name contains '{escaped_name}'")
        
        if mime_type:
            query_parts.append(f"mimeType = '{mime_type}'")
        elif folders_only:
            query_parts.append("mimeType = 'application/vnd.google-apps.folder'")
        elif exclude_folders:
            query_parts.append("mimeType != 'application/vnd.google-apps.folder'")
        
        if contains_text:
            escaped_text = contains_text.replace("'", "\\'").replace("\\", "\\\\")
            if '"' in contains_text:  
                query_parts.append(f"fullText contains '{escaped_text}'")
            else:
                query_parts.append(f"fullText contains '{escaped_text}'")
        
        if modified_after:
            query_parts.append(f"modifiedTime > '{modified_after}'")
        if modified_before:
            query_parts.append(f"modifiedTime < '{modified_before}'")
        if parent_folder_id:
            query_parts.append(f"'{parent_folder_id}' in parents")
        
        if starred is not None:
            query_parts.append(f"starred = {str(starred).lower()}")
        if trashed is not None:
            query_parts.append(f"trashed = {str(trashed).lower()}")
        if shared_with_me is not None and shared_with_me:
            query_parts.append("sharedWithMe")
        if owner_email:
            query_parts.append(f"'{owner_email}' in owners")

        if custom_properties:
            for key, value in custom_properties.items():
                query_parts.append(f"properties has {{ key='{key}' and value='{value}' }}")
        
        return " and ".join(query_parts)
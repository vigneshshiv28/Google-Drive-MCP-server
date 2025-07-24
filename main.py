from mcp.server.fastmcp import FastMCP
from auth import authenticate_drive
from tools import file_and_folder, search, permissions
import logging

class GoogleDriveMCP:
    def __init__(self):
        self.service = authenticate_drive()
        self.mcp = FastMCP("gdrive")
        self._register_all_tools()

    def _register_all_tools(self):
        self.mcp.tool()(file_and_folder.create_file(self.service))
        self.mcp.tool()(file_and_folder.upload_file_in_parent(self.service))
        self.mcp.tool()(file_and_folder.move_file_to_folder(self.service))
        self.mcp.tool()(file_and_folder.create_folder(self.service))
        self.mcp.tool()(file_and_folder.create_folder_in_parent(self.service))
        self.mcp.tool()(file_and_folder.rename_file_or_folder(self.service))
        self.mcp.tool()(file_and_folder.copy_and_paste_file(self.service))
        self.mcp.tool()(file_and_folder.get_file_metadata(self.service))
        self.mcp.tool()(file_and_folder.delete_file_or_folder(self.service))
        self.mcp.tool()(file_and_folder.permanently_delete_file_or_folder(self.service))
        self.mcp.tool()(file_and_folder.restore_file_or_folder(self.service))

        self.mcp.tool()(search.list_files(self.service))
        self.mcp.tool()(search.search_files(self.service))

        self.mcp.tool()(permissions.list_permissions(self.service))
        self.mcp.tool()(permissions.add_permission(self.service))

    def run(self):
        self.mcp.run()

if __name__ == "__main__":
    agent = GoogleDriveMCP()
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting Google Drive MCP agent")
    agent.run()
    

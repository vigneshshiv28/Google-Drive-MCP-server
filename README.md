# Google Drive MCP Agent - Setup Guide & Tool Reference

## Introduction

The Google Drive MCP (Model Context Protocol) agent is a powerful tool that allows AI assistants like Claude to interact directly with your Google Drive. 

## Available Tools

The Google Drive MCP agent provides the following tools.

### File and Folder Management

| Tool | Description |
| :--- | :--- |
| **`create_file`** | Creates a new, blank Google Workspace file (e.g., Google Doc). |
| **`upload_file_in_parent`** | Uploads content from your local machine to a specified Drive folder. |
| **`create_folder`** | Creates a new folder in the root directory ("My Drive"). |
| **`create_folder_in_parent`** | Creates a new folder inside an existing parent folder. |
| **`move_file_to_folder`** | Moves a file or folder to a different location. |
| **`rename_file_or_folder`** | Changes the name of an existing file or folder. |
| **`copy_file`** | Creates a duplicate of a specified file. |

### Trash and Recovery

| Tool | Description |
| :--- | :--- |
| **`delete_file_or_folder`** | Moves a file or folder to the trash (can be restored within 30 days). |
| **`permanently_delete_file_or_folder`** | Permanently deletes a file or folder, bypassing the trash (irreversible). |
| **`restore_file_or_folder`** | Restores a file or folder from the trash back to its original location. |

### Information and Metadata

| Tool | Description |
| :--- | :--- |
| **`get_file_metadata`** | Retrieves detailed information about a file (size, owner, dates, etc.). |

### Search and Discovery

| Tool | Description |
| :--- | :--- |
| **`list_files`** | Browses through all files and folders in your Drive, page by page. |
| **`search_files`** | Performs a powerful, criteria-based search to find specific files or folders. |

### Permissions and Sharing

| Tool | Description |
| :--- | :--- |
| **`list_permissions`** | Shows a list of all users and their access levels for a specific file. |
| **`add_permission`** | Shares a file or folder with a user, granting them a specific role (viewer, editor, etc.). |



## Setup Instructions

### Step 1: Create a Project on Google Cloud Platform

1. Go to the **Google Cloud Console** (https://console.cloud.google.com).
2. If you don't have a project, click on the project selector dropdown at the top of the page and click **"NEW PROJECT"**.
3. Give your project a name (e.g., "Drive Agent Project") and click **"CREATE"**.

### Step 2: Enable the Google Drive API

For your new project to access Google Drive, you must enable the API.

1. Make sure your new project is selected in the top navigation bar.
2. In the search bar at the top, type **"Google Drive API"** and select it from the results.
3. Click the **"ENABLE"** button. If it's already enabled, you can proceed to the next step.

### Step 3: Configure the OAuth Consent Screen

This is the screen that will pop up the first time you run the agent, asking for your permission to access your Drive.

1. In the left-hand navigation menu, go to **APIs & Services > OAuth consent screen**.
2. Choose the **"External"** user type. This allows any Google Account to authorize the app (including your own). Click **"CREATE"**.
3. Fill in the required information:
   - **App name:** "Google Drive Agent" (or a name of your choice).
   - **User support email:** Select your email address.
   - **Developer contact information:** Enter your email address again.
4. Click **"SAVE AND CONTINUE"**.
5. On the **Scopes** page, you don't need to add anything. Click **"SAVE AND CONTINUE"**.
6. On the **Test users** page, click **"+ ADD USERS"**. Enter the email address of the Google account you will use to log in (your own email address). This is crucial for keeping your app in "testing" mode. Add your email and click **"ADD"**.
7. Click **"SAVE AND CONTINUE"**, then **"BACK TO DASHBOARD"**.

### Step 4: Create OAuth 2.0 Credentials

This is the final step where you generate the file that the agent will use to authenticate.

1. In the left-hand navigation menu, go to **APIs & Services > Credentials**.
2. Click **"+ CREATE CREDENTIALS"** at the top and select **"OAuth client ID"**.
3. For **Application type**, select **"Desktop app"**.
4. Give the credential a name (e.g., "Desktop Client 1").
5. Click **"CREATE"**.
6. A pop-up will appear showing your Client ID and Client Secret. **Do not copy these.** Instead, click the **"DOWNLOAD JSON"** button.

### Step 5: Place the Credentials File in Your Project

1. The downloaded file will be named something like `client_secret_xxxxxxxx.json`.
2. **Rename this file to `credentials.json`**. This is important as the authentication script looks for this specific filename.
3. **Place the `credentials.json` file in the root directory of this project.**

Your project directory should now look something like this:

```
/GoogleDriveGPT/
|-- credentials.json
|-- auth.py
|-- file_and_folder.py
|-- main.py
|-- ... (other project files)
```

### Step 6: Connect with MCP Client

1. Go to the config file of any MCP client (For example: Claude Desktop or Cursor).
2. Paste this following configuration in the config file:

```json
{
  "mcpServers": {
    "gdrive": {
      "command": "uv",
      "args": [
        "--directory",
        "<path_to_drive_folder>",
        "run",
        "main.py"
      ]
    }
  }
}
```

Replace `<path_to_drive_folder>` with the absolute path to your Google Drive MCP project directory.

---




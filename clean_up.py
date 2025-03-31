import os
import shutil

def delete_files(folder_path):
    """
    Deletes all files within the specified folder.
    
    Args:
        folder_path (str): Path to the folder whose contents should be deleted.
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Verify the folder exists
        if not os.path.exists(folder_path):
            return False, f"Folder does not exist: {folder_path}"
            
        # Verify it's actually a folder
        if not os.path.isdir(folder_path):
            return False, f"Path is not a folder: {folder_path}"
            
        # Loop through all files and subfolders
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # Remove files and links
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Remove subdirectories and their contents
            except Exception as e:
                return False, f"Failed to delete {file_path}. Error: {str(e)}"
                
        return True, f"Successfully deleted all contents in {folder_path}"
        
    except Exception as e:
        return False, f"An error occurred: {str(e)}"

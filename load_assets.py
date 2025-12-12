def list_files_os(directory_path):
    import os
    """
    Lists all file names in the specified directory using the os module.
    """
    files_list = []
    try:
        # Get all entries in the directory
        entries = os.listdir(directory_path)
        for entry in entries:
            # Create the full path to check if it's a file
            full_path = os.path.join(directory_path, entry)
            if os.path.isfile(full_path):
                files_list.append(entry)
    except FileNotFoundError:
        print(f"Error: The directory '{directory_path}' does not exist.")

    return files_list

# Check if the expected number of files exist in the directory
def check_files_exist():
    # Expected number of files in each directory
    images_expected_count = 4
    cards_expected_count = 2

    images_count = len(list_files_os(r"Images"))
    cards_count = len(list_files_os(r"Images\Cards"))

    if images_count != images_expected_count or cards_count != cards_expected_count:
        print("ERROR: Missing asset files!")
        print(f"Images found: {images_count}, expected: {images_expected_count}")
        print(f"Cards found: {cards_count}, expected: {cards_expected_count}")
        return False
    return True


check_files_exist()
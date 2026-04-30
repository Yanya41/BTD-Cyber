import os
import pygame


#screen
screen = pygame.display.set_mode((1920, 1080))

#folders
image_folder = "Images"

skeleton_name_prefix = "skeleton_frame" #the name for the frames is skeleton_frame_(frame number).png
shielded_skeleton_name_prefix = "shielded_skeleton_frame" #the name for the frames is shielded_skeleton_frame_(frame number).png

def list_files_os(directory_path):
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
    images_expected_count = 6
    cards_expected_count = 2

    images_count = len(list_files_os("Images"))
    cards_count = len(list_files_os(os.path.join("Images", "Cards")))

    if images_count != images_expected_count or cards_count != cards_expected_count:
        print("ERROR: Missing asset files!")
        print(f"Images found: {images_count}, expected: {images_expected_count}")
        print(f"Cards found: {cards_count}, expected: {cards_expected_count}")
        return False
    return True


check_files_exist()

#loading images
def load_image(filename, scale_to=None, alpha=False):
    path = os.path.join(image_folder, filename)
    try:
        image = pygame.image.load(path)

        if alpha:
            image = image.convert_alpha()
        else:
            image = image.convert()

        if scale_to:
            image = pygame.transform.scale(image, scale_to)
        return image
    except FileNotFoundError:
        print(f"ERROR: Image file not found: {path}")
        return None



#loading the skeleton and shielded skeleton frames for animation
skeleton_frames = []
for i in range(2):
    frame_filename = f"{skeleton_name_prefix}_{i}.png"
    frame_image = load_image(frame_filename, scale_to=(60, 60), alpha=True)

    if frame_image:
        # Assuming the skeleton has a black background to remove
        frame_image.set_colorkey((0, 0, 0))
        skeleton_frames.append(frame_image)
    else:
        print(f"Warning: Could not load {frame_filename}. Animation may be incomplete.")

shielded_skeleton_frames = []
for i in range(2):
    frame_filename = f"{shielded_skeleton_name_prefix}_{i}.png"
    frame_image = load_image(frame_filename, scale_to=(60, 60), alpha=True)

    if frame_image:
        # Assuming the skeleton has a black background to remove
        frame_image.set_colorkey((0, 0, 0))
        shielded_skeleton_frames.append(frame_image)
    else:
        print(f"Warning: Could not load {frame_filename}. Animation may be incomplete.")

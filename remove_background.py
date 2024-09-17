import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk  # For the progress bar
import os
from rembg import remove
from PIL import Image, ImageChops, ImageOps
from colorthief import ColorThief
import io
import threading
import time  # For tracking processing time

# Variables to store folder paths
input_folder_path = ""
output_folder_path = ""

# List of supported image formats
SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']


# Function to check if the file is an image
def is_image_file(filename):
    return any(filename.lower().endswith(ext) for ext in SUPPORTED_FORMATS)


# Function to select input folder
def select_input_folder():
    global input_folder_path
    input_folder_path = filedialog.askdirectory()
    input_label.config(text=f"Input Folder: {input_folder_path}")


# Function to select output folder
def select_output_folder():
    global output_folder_path
    output_folder_path = filedialog.askdirectory()
    output_label.config(text=f"Output Folder: {output_folder_path}")


# Function to process a single image
def process_single_image(image_path, output_folder):
    # Open the image
    with open(image_path, "rb") as f:
        img = f.read()

    # Get the mask where the object is located
    result = remove(img)

    # Convert binary data to PIL image
    img_with_alpha = Image.open(io.BytesIO(result))

    # Extract the object (the part with alpha channel not transparent)
    mask = img_with_alpha.split()[-1]  # Alpha channel as mask

    # Save the object separately
    object_img = Image.composite(img_with_alpha, Image.new('RGBA', img_with_alpha.size, (255, 255, 255, 0)), mask)

    # Invert the mask to remove the object from the original image
    inverted_mask = ImageChops.invert(mask)

    # Open the original image
    original_img = Image.open(image_path)

    # Correct the orientation of the original image
    original_img = ImageOps.exif_transpose(original_img)

    # Find the dominant color of the background
    color_thief = ColorThief(image_path)
    dominant_color = color_thief.get_color(quality=1)

    # Apply the mask to remove the object from the original image and fill the area with the dominant color
    background_filled_img = Image.composite(original_img, Image.new('RGB', original_img.size, dominant_color),
                                            inverted_mask)

    # Save the image with the object removed and background filled with dominant color
    temp_output_path = os.path.join(output_folder, f"temp_removed_object_{os.path.basename(image_path)}.png")
    background_filled_img.save(temp_output_path, format='PNG')

    # Now, remove the background of the image with the object removed
    with open(temp_output_path, "rb") as f:
        img = f.read()

    # Remove the background
    final_result = remove(img)

    # Convert binary data to PIL image
    final_img = Image.open(io.BytesIO(final_result))

    # Set transparency mode (optional, adjust based on your needs)
    final_img = final_img.convert('RGBA')  # This sets alpha channel for transparency

    # Now, we overlay the object image onto the final image
    combined_img = Image.alpha_composite(final_img, object_img)

    # Save the final combined image
    combined_output_filename = f"{os.path.basename(image_path)}.png"
    combined_output_path = os.path.join(output_folder, combined_output_filename)
    combined_img.save(combined_output_path, format='PNG')

    # Remove the temporary image
    os.remove(temp_output_path)  # Remove the intermediate image with removed object

    print(f"Processed and saved: {combined_output_filename}")
    return combined_output_filename


# Function to process images in sequence (single-threaded)
def process_images():
    if not input_folder_path or not output_folder_path:
        messagebox.showerror("Error", "Please select both input and output folders.")
        enable_buttons()
        return

    image_files = [f for f in os.listdir(input_folder_path) if is_image_file(f)]
    total_images = len(image_files)

    if total_images == 0:
        messagebox.showinfo("No Images", "No image files found in the input folder.")
        enable_buttons()
        return

    progress_bar['maximum'] = total_images
    progress_bar['value'] = 0

    # Track processing time
    times = []

    # Start overall processing time
    start_total_time = time.time()

    # Process images one by one
    for i, filename in enumerate(image_files, start=1):
        image_path = os.path.join(input_folder_path, filename)
        start_time = time.time()  # Start time of processing for each image

        process_single_image(image_path, output_folder_path)

        end_time = time.time()  # End time for current image
        processing_time = end_time - start_time
        times.append(processing_time)

        # Update progress
        progress_bar['value'] = i

        # Update statistics (average time and estimated remaining time)
        avg_time = sum(times) / len(times)
        remaining_time = avg_time * (total_images - i)
        progress_label.config(
            text=f"Processed {i}/{total_images} images\nEstimated remaining time: {remaining_time:.2f} seconds")

        root.update_idletasks()

    # End overall processing time
    end_total_time = time.time()
    total_time = end_total_time - start_total_time

    # Show total processing time
    messagebox.showinfo("Success",
                        f"All images processed successfully!\nTotal processing time: {total_time:.2f} seconds")
    enable_buttons()


# Function to run the image processing in a separate thread
def start_processing():
    disable_buttons()
    threading.Thread(target=process_images).start()


# Function to disable buttons and change the text of the start button
def disable_buttons():
    input_button.config(state=tk.DISABLED)
    output_button.config(state=tk.DISABLED)
    process_button.config(state=tk.DISABLED, text="Processing...")


# Function to re-enable buttons and reset the start button text
def enable_buttons():
    input_button.config(state=tk.NORMAL)
    output_button.config(state=tk.NORMAL)
    process_button.config(state=tk.NORMAL, text="Start Processing")


# Create GUI
root = tk.Tk()
root.title("Remove Background")

# Labels and buttons
input_label = tk.Label(root, text="Input Folder: Not selected", width=50, anchor="w")
input_label.pack(pady=5)

input_button = tk.Button(root, text="Select Input Folder", command=select_input_folder)
input_button.pack(pady=5)

output_label = tk.Label(root, text="Output Folder: Not selected", width=50, anchor="w")
output_label.pack(pady=5)

output_button = tk.Button(root, text="Select Output Folder", command=select_output_folder)
output_button.pack(pady=5)

process_button = tk.Button(root, text="Start Processing", command=start_processing)
process_button.pack(pady=20)

# Add progress bar
progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=10)

# Add label for processed images and remaining time
progress_label = tk.Label(root, text="Processed 0/0 images\nEstimated remaining time: 0.00 seconds", width=50,
                          anchor="w")
progress_label.pack(pady=5)

# Run the application
root.mainloop()

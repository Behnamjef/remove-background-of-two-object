from rembg import remove
import os
from PIL import Image, ImageChops, ImageOps
from colorthief import ColorThief
import io

# Define the folder containing images
folder_path = "InputImages"
output_dir = "OutputImages"

# Loop through each file in the folder
for filename in os.listdir(folder_path):
    if filename.endswith(".JPG"):
        image_path = os.path.join(folder_path, filename)

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

        # Create output filename for the object
        object_output_filename = f"object_{filename}"

        # Save the object image
        object_output_path = os.path.join(output_dir, f"{object_output_filename}.png")
        object_img.save(object_output_path, format='PNG')

        print(f"Object extracted and saved separately: {object_output_filename}.png")

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
        background_filled_img = Image.composite(original_img, Image.new('RGB', original_img.size, dominant_color), inverted_mask)

        # Save the image with the object removed and background filled with dominant color
        temp_output_path = os.path.join(output_dir, f"temp_removed_object_{filename}.png")
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
        combined_output_filename = f"{filename}.png"
        combined_output_path = os.path.join(output_dir, combined_output_filename)
        combined_img.save(combined_output_path, format='PNG')

        print(f"Final combined image saved as PNG: {combined_output_filename}")

        # Remove the temporary images (object and intermediate images)
        os.remove(object_output_path)  # Remove the object image
        os.remove(temp_output_path)  # Remove the intermediate image with removed object

        print(f"Temporary images removed for: {filename}")

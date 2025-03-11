from PIL import Image
img = Image.open("background.png")
img = img.resize((1920, 1080))  # Adjust size
img.save("resized_background.png")
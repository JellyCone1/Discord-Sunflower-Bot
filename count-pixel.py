from PIL import Image
from os.path import join

img = Image.open(join("S:\\", "User", "SPRITES", "WPlace", "squirtleedited.png")).convert("RGBA")
pixels = img.getdata()

non_transparent = sum(1 for p in pixels if p[3] > 0)  # alpha > 0
print("Non-transparent pixels:", non_transparent)

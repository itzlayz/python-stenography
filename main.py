from base64 import b64encode, b64decode
from PIL import Image as PILImage

import io

MARKERS = {
    "jpg": b"\xFF\xD9",
    "jpeg": b"\xFF\xD9",
    "png": b'\x00\x00\x00\x00IEND\xaeB`\x82'
}

class Image:
    def __init__(self, path: str):
        self.path = path
        self.extension = path.split(".")[-1].lower()

        self.end_marker = MARKERS.get(self.extension)

        if not self.end_marker:
            raise ValueError("Invalid image extension. Supported extensions: png, jpg, jpeg")

    def write_text(self, text: str, overwrite_pixels: bool = False):
        with open(self.path, 'rb') as file:
            image_data = file.read()

        if not image_data.endswith(self.end_marker):
            raise ValueError(f"Invalid image format. The image doesn't end with the {self.extension} marker.")

        if overwrite_pixels:
            self._overwrite_pixels(text)
        else:
            with open(self.path, 'wb') as new_file:
                new_file.write(image_data)
                new_file.write(b64encode(text.encode('utf-8')))

    def _overwrite_pixels(self, text: str):
        with open(self.path, 'rb') as file:
            img = PILImage.open(io.BytesIO(file.read()))

        encoded_text = b64encode(text.encode('utf-8')).decode('utf-8')
        pixels = img.load()

        width, height = img.size
        index = 0

        for y in range(height):
            for x in range(width):
                if index < len(encoded_text):
                    r, g, b = pixels[x, y][:3]
                    new_r = (r & 0xF0) | (ord(encoded_text[index]) >> 4)  
                    new_g = (g & 0xF0) | (ord(encoded_text[index]) & 0x0F) 
                    pixels[x, y] = (new_r, new_g, b)
                    index += 1

        img.save(self.path)

    def extract_text(self, from_pixels: bool = False):
        if from_pixels:
            return self._extract_from_pixels()
        else:
            with open(self.path, 'rb') as file:
                data = file.read()

            iend_index = data.find(self.end_marker)
            if iend_index == -1:
                raise ValueError("Corrupted file, end marker not found...")

            text = data[iend_index + len(self.end_marker):]
            return b64decode(text).decode('utf-8')

    def _extract_from_pixels(self):
        with open(self.path, 'rb') as file:
            img = PILImage.open(io.BytesIO(file.read()))

        pixels = img.load()
        width, height = img.size
        chars = []

        for y in range(height):
            for x in range(width):
                r, g, _ = pixels[x, y][:3]

                ascii = ((r & 0x0F) << 4) | (g & 0x0F)
                
                # we need to get 4 upper bits of red pixel
                # and 4 lower bits of green pixel

                # red = 10100000 & 0xF0 = 10100000  # Upper 4 bits of red pixel
                # green = 00000001 & 0x0F = 00000001  # Lower 4 bits of green pixel

                # then just combine 10100000 and 00000001
                # 10100000 (red) | 00000001 (green) => 01100001

                # int(01100001, 2) => chr(95) => "a" 

                if ascii != 0:
                    chars.append(chr(ascii))
                else:
                    break

        encoded_text = ''.join(chars)
        return b64decode(encoded_text).decode('utf-8')

image = Image("sample.png")
image.write_text("lol kek cheburek", overwrite_pixels=True)

print(image.extract_text(from_pixels=True))

import io

from PIL import ExifTags, Image
from src.utils.image import get_image_metadata


def create_sample_image() -> bytes:
    img = Image.new("RGB", (100, 50), (255, 0, 0))
    exif = Image.Exif()
    exif[ExifTags.Base.ISOSpeedRatings] = 100
    exif[ExifTags.Base.FNumber] = (28, 10)
    exif[ExifTags.Base.ExposureTime] = (1, 125)
    exif[ExifTags.Base.FocalLength] = (50, 1)
    exif[ExifTags.Base.LensModel] = "MyLens"
    exif[ExifTags.Base.DateTimeOriginal] = "2024:07:01 12:34:56"
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", exif=exif)
    return buffer.getvalue()


def test_get_image_metadata():
    img_bytes = create_sample_image()
    meta = get_image_metadata(img_bytes)
    assert meta["width"] == 100
    assert meta["height"] == 50
    assert meta["format"] == "image/jpeg"
    assert meta["file_size"] == len(img_bytes)
    assert "iso" in meta
    assert "aperture" in meta

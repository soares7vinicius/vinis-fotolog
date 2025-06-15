from io import BytesIO

import exifread
import imageio
import pillow_heif
import rawpy
from PIL import Image

SUPPORTED_FORMATS_NORMAL = [
    "jpg",
    "jpeg",
    "png",
    "bmp",
    "gif",
    "tiff",
    "webp",
    "heic",
]

SUPPORTED_FORMATS_RAW = [
    "cr2",
    "cr3",
    "nef",
    "arw",
    "dng",
]

SUPPORTED_FORMATS = SUPPORTED_FORMATS_NORMAL + SUPPORTED_FORMATS_RAW


def is_supported_format(filename: str) -> bool:
    """
    Check if the file format is supported.

    Args:
        filename (str): The name of the file to check.

    Returns:
        bool: True if the format is supported, False otherwise.
    """
    ext = filename.lower().split(".")[-1]
    return ext in SUPPORTED_FORMATS


def any_to_jpeg(image_bytes: bytes, filename_hint: str) -> bytes:
    """
    Convert any image (RAW, common formats) to JPEG.

    Args:
        image_bytes (bytes): The input image in bytes.
        filename_hint (str): A filename or extension hint (e.g., 'photo.CR3').

    Returns:
        bytes: The converted JPEG image in bytes.
    """
    ext = filename_hint.lower().split(".")[-1]
    output = BytesIO()

    if ext in SUPPORTED_FORMATS_RAW:
        with rawpy.imread(BytesIO(image_bytes)) as raw:
            rgb = raw.postprocess()
            imageio.imwrite(output, rgb, format="JPEG")
    elif ext == "heic":
        img = pillow_heif.read_heif(image_bytes)[0].to_pillow()
        img.convert("RGB").save(output, format="JPEG")
    else:
        img = Image.open(BytesIO(image_bytes))
        img.convert("RGB").save(output, format="JPEG")

    return output.getvalue()


def resize_image(image_bytes: bytes, max_size: int = 1024) -> bytes:
    """
    Resize an image to fit within a maximum size while maintaining aspect ratio.

    Args:
        image_bytes (bytes): The input image in bytes.
        max_size (int): The maximum size for the longest dimension.

    Returns:
        bytes: The resized image in bytes.
    """
    img = Image.open(BytesIO(image_bytes))

    if max(img.size) <= max_size:
        return image_bytes

    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    output = BytesIO()
    img.save(output, format="JPEG")

    return output.getvalue()


def get_image_metadata(image_bytes: bytes) -> dict:
    """Return basic and EXIF metadata for an image.

    The function tries to provide commonly useful fields regardless of the
    source format. When available, EXIF information such as ISO, aperture,
    shutter speed, and lens model is also returned.
    """

    metadata = {
        "file_size": len(image_bytes),
    }

    try:
        img = Image.open(BytesIO(image_bytes))
    except Exception:
        return metadata

    metadata.update(
        {
            "format": img.format,
            "mode": img.mode,
            "width": img.width,
            "height": img.height,
        }
    )

    tags = {}
    try:
        tags = exifread.process_file(BytesIO(image_bytes), details=False, strict=False)
    except Exception:
        pass

    def _get_tag(*keys):
        for key in keys:
            if key in tags:
                return str(tags[key])
        return None

    metadata.update(
        {
            "date_time": _get_tag("EXIF DateTimeOriginal", "Image DateTime"),
            "lens": _get_tag("EXIF LensModel", "Image LensModel"),
            "iso": _get_tag("EXIF ISOSpeedRatings"),
            "aperture": _get_tag("EXIF FNumber"),
            "shutter_speed": _get_tag("EXIF ExposureTime"),
            "focal_length": _get_tag("EXIF FocalLength"),
        }
    )

    return metadata


def write_image_to_file(image_bytes: bytes, filename: str) -> None:
    """
    Write image bytes to a file.

    Args:
        image_bytes (bytes): The image data in bytes.
        filename (str): The path where the image will be saved.
    """
    with open(filename, "wb") as f:
        f.write(image_bytes)

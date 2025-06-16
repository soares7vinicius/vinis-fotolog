import logging
from io import BytesIO

import exiv2
import imageio
import pillow_heif
import rawpy
from PIL import Image

logger = logging.getLogger(__name__)

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
    """Return basic and EXIF metadata for an image using ``exiv2``.

    The function extracts common information such as dimensions and
    format. When available, EXIF data like ISO and aperture are also
    returned.
    """

    metadata = {"file_size": len(image_bytes)}

    try:
        img = exiv2.ImageFactory.open(image_bytes)
        img.readMetadata()

        metadata.update(
            {
                "format": img.mimeType(),
                "width": img.pixelWidth(),
                "height": img.pixelHeight(),
            }
        )
    except Exception as exc:  # pragma: no cover - safeguard only
        logger.warning("Failed to read metadata via exiv2: %s", exc)
        try:
            pil_img = Image.open(BytesIO(image_bytes))
            metadata.update(
                {
                    "format": pil_img.format,
                    "width": pil_img.width,
                    "height": pil_img.height,
                }
            )
        except Exception as exc_pil:  # pragma: no cover - unlikely
            logger.warning("Failed to read metadata via Pillow: %s", exc_pil)
            return metadata

    # ``mode`` is not provided by exiv2
    try:
        pil_img = Image.open(BytesIO(image_bytes))
        metadata["mode"] = pil_img.mode
    except Exception:  # pragma: no cover - optional
        metadata["mode"] = None

    try:
        exif = img.exifData()
        clean_value = lambda v: str(v).split(": ", 1)[-1]
        metadata.update(
            {
                "date_time": clean_value(exiv2.easyaccess.dateTimeOriginal(exif)),
                "lens": clean_value(exiv2.easyaccess.lensName(exif)),
                "iso": clean_value(exiv2.easyaccess.isoSpeed(exif)),
                "aperture": clean_value(exiv2.easyaccess.fNumber(exif)),
                "shutter_speed": clean_value(exiv2.easyaccess.shutterSpeedValue(exif)),
                "focal_length": clean_value(exiv2.easyaccess.focalLength(exif)),
            }
        )
    except Exception as exc:  # pragma: no cover - exif may be missing
        logger.debug("EXIF extraction failed: %s", exc)

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

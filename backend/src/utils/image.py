import logging
import os
from io import BytesIO
from uuid import uuid4

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


class ImageProcessor:
    """
    A class to handle image processing tasks such as format conversion,
    resizing, and metadata extraction.
    """

    def __init__(self, image_bytes: bytes, filename_hint: str):
        self.image_bytes = image_bytes
        self.filename_hint = filename_hint
        self.ext = filename_hint.lower().split(".")[-1]

        self.metadata = self._get_metadata()

    def is_supported(self) -> bool:
        return self.ext in SUPPORTED_FORMATS

    def to_jpeg(self, inplace=False) -> bytes:
        """
        Convert the image to JPEG format.

        Args:
            inplace (bool): If True, modifies the original image bytes.
                            If False, returns a new JPEG image in bytes.

        Returns:
            bytes: The converted JPEG image in bytes.
        """
        output = BytesIO()

        if self.ext in SUPPORTED_FORMATS_RAW:
            with rawpy.imread(BytesIO(self.image_bytes)) as raw:
                rgb = raw.postprocess()
                imageio.imwrite(output, rgb, format="JPEG")
        elif self.ext == "heic":
            img = pillow_heif.read_heif(self.image_bytes)[0].to_pillow()
            img.convert("RGB").save(output, format="JPEG")
        else:
            img = Image.open(BytesIO(self.image_bytes))
            img.convert("RGB").save(output, format="JPEG")

        if inplace:
            self.image_bytes = output.getvalue()
            self.ext = "jpg"
            self.filename_hint = f"{self.filename_hint.rsplit('.', 1)[0]}.jpg"
            return self.image_bytes
        return output.getvalue()

    def resize(self, max_size: int = 2048, inplace=False) -> bytes:
        """
        Resize an image to fit within a maximum size while maintaining aspect ratio.

        Args:
            max_size (int): The maximum size for the longest dimension.
            inplace (bool): If True, modifies the original image bytes.
                            If False, returns a new resized image in bytes.

        Returns:
            bytes: The resized image in bytes.
        """
        if self.ext not in SUPPORTED_FORMATS_NORMAL:
            logger.warning(
                "Resize operation is not supported for raw formats: %s", self.ext
            )
            logger.warning(
                "Automatically converting to JPEG first using `to_jpeg(inplace=True)`"
            )
            self.to_jpeg(inplace=True)

        img = Image.open(BytesIO(self.image_bytes))

        if max(img.size) <= max_size:
            return self.image_bytes

        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        output = BytesIO()

        img.save(output, format="JPEG", quality=100, optimize=True)

        if inplace:
            self.image_bytes = output.getvalue()
            self.ext = "jpg"
            self.filename_hint = f"{self.filename_hint.rsplit('.', 1)[0]}.jpg"
            return self.image_bytes

        return output.getvalue()

    def _get_metadata(self) -> dict:
        """Return basic and EXIF metadata for an image using ``exiv2``.

        The function extracts common information such as dimensions and
        format. When available, EXIF data like ISO and aperture are also
        returned.
        """

        metadata = {"file_size": len(self.image_bytes)}

        try:
            img = exiv2.ImageFactory.open(self.image_bytes)
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
                pil_img = Image.open(BytesIO(self.image_bytes))
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
            pil_img = Image.open(BytesIO(self.image_bytes))
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
                    "shutter_speed": clean_value(
                        exiv2.easyaccess.shutterSpeedValue(exif)
                    ),
                    "focal_length": clean_value(exiv2.easyaccess.focalLength(exif)),
                }
            )
        except Exception as exc:  # pragma: no cover - exif may be missing
            logger.debug("EXIF extraction failed: %s", exc)

        return metadata

    def to_file(self, path: str, filename: str = None) -> str:
        """
        Write image bytes to a file.

        Args:
            path (str): The directory where the image will be saved.
            filename (str, optional): The name of the file. If not provided,
                                    a UUID will be generated as the filename.

        Returns:
            str: The filename.
        """
        if not filename:
            filename = f"{uuid4().hex}.{self.ext}"
        if not filename.lower().endswith(f".{self.ext}"):
            filename = f"{filename}.{self.ext}"

        filepath = f"{path}/{filename}"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "wb") as f:
            f.write(self.image_bytes)

        return filename

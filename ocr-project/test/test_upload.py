import logging
import os
import time
from pathlib import Path

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("test_upload.log"),
    ],
)
logger = logging.getLogger("upload_test")


def test_file_upload(
    file_path: str,
    api_url: str = "http://localhost:8000/api/v1/files",
) -> requests.Response | None:
    try:
        file_path = Path(file_path)
        logger.info(f"Uploading file: {file_path.name}")

        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, get_content_type(file_path))}
            response = requests.post(api_url, files=files)

        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response: {response.json()}")
        return response
    except Exception as e:
        logger.error(
            f"Error uploading file {file_path.name}: {e}",
            exc_info=True,
        )
        return None


def get_content_type(file_path: Path) -> str:
    extension = file_path.suffix.lower()
    if extension == ".pdf":
        return "application/pdf"
    if extension in [".png"]:
        return "image/png"
    if extension in [".jpg", ".jpeg"]:
        return "image/jpeg"
    return "application/octet-stream"


def test_multiple_files(
    image_dir: str,
    file_extensions: list[str] = [".pdf", ".png", ".jpg", ".jpeg"],
) -> None:
    image_dir = Path(image_dir)
    if not image_dir.exists() or not image_dir.is_dir():
        logger.error(
            f"Directory {image_dir} does not exist or is not a directory",
        )
        return

    files_to_test = []
    for ext in file_extensions:
        files_to_test.extend(image_dir.glob(f"*{ext}"))

    if not files_to_test:
        logger.warning(
            f"No files with extensions {file_extensions} found in {image_dir}",
        )
        return

    logger.info(f"Found {len(files_to_test)} files to upload:")
    for i, file in enumerate(files_to_test, 1):
        logger.info(f"{i}. {file.name}")

    logger.info("Starting uploads..." + "\n" + "-" * 50)
    for file in files_to_test:
        test_file_upload(file)
        time.sleep(1)

    logger.info("-" * 50 + "\nAll uploads completed!")


if __name__ == "__main__":
    test_images_dir = os.path.join(os.path.dirname(__file__), "test_images")

    if not os.path.exists(test_images_dir):
        os.makedirs(test_images_dir)
        logger.info(f"Created test images directory: {test_images_dir}")
        logger.info(
            "Please place your test files (PDF, PNG, JPG) in this directory",
        )
    else:
        logger.info("Starting test upload process")
        test_multiple_files(test_images_dir)

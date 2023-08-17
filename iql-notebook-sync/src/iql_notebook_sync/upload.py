import shutil
import os
from pathlib import Path
from getpass import getpass
import random
from dataclasses import dataclass
import requests
import sys


@dataclass
class Lesson:
    def __init__(self, lesson_path, lesson_id):
        self.path = Path(lesson_path)
        self.name = self.path.parts[-1]
        self.id = lesson_id
        self.zip_path = None

    # Methods:
    #   - zip
    #   - remove zip

@dataclass
class Database:
    name: str
    url: str

    # Methods:
    #   - Get access token
    #   - Get translation id
    #   - Upload ZIP
    #   - Link ZIP


def get_access_token(database_url):
    """
    Either token is in env variable, or we use login details to get temporary
    access token.
    """
    if os.environ.get("DIRECTUS_TOKEN", None) is not None:
        print("  * Using saved access token...")
        return os.environ.get("DIRECTUS_TOKEN")

    print("  🔑 Log in:")
    response = requests.post(
        f"{database_url}/auth/login",
        json=(
            {"email": input("     > Email: "), "password": getpass("     > Password: ")}
        ),
    )
    if response.status_code != 200:
        print("    Couldn't log in 😕\n    Exiting...")
        sys.exit()

    token = response.json()["data"]["access_token"]
    os.environ["DIRECTUS_TOKEN"] = token
    print("    Saved temporary token for remaining uploads.\n")

    return token


def push_lesson(lesson: Lesson, database: Database):
    """
    Steps:
      1. Get access token from environment variable, or ask for login details
         to get temporary access token
      2. Get the translation ID of the English translation (needed for upload)
      3. Zip the folder containing notebook and images
      4. Upload the zip file to the database
      5. Link the zip file in the database to the lesson
      6. Clean up: delete the zip file from local disk

    Args:
        lesson (Lesson)
        database (Database)
    """
    print(f"Pushing '{lesson.name}' to '{database.name}':")

    # 1. Sort out auth stuff
    auth_header = {"Authorization": f"Bearer {get_access_token(database.url)}"}

    # 2. Get ID of english translation (needed for upload)
    print("  * Finding English translation...")
    response = requests.get(
        f"{database.url}/items/lessons/{lesson.id}"
         "?fields[]=translations.id,translations.languages_code",
        headers=auth_header,
    )

    for translation in response.json()["data"]["translations"]:
        if translation["languages_code"] == "en-US":
            translation_id = translation["id"]
            break
        raise ValueError("No 'en-US' translation found!")

    # 3. Zip file
    print("  * Zipping folder...")
    lesson.zip_path = Path(
        shutil.make_archive(
            lesson.path / f"{random.randint(0, 1_000_000_000)}_{lesson.name}",
            "zip",
            root_dir=lesson.path,
        )
    )

    # 4. Upload .zip
    print(f"  * Uploading `{lesson.zip_path.name}`...")
    with open(lesson.zip_path, "rb") as fileobj:
        response = requests.post(
            database.url + "/files",
            files={"file": (fileobj)},
            data={"filename": lesson.zip_path.stem},
            headers=auth_header,
        )

    temp_file_id = response.json()["data"]["id"]
    if response.status_code != 200:
        raise Exception(
            f"Problem connecting to Directus (error code {response.status_code}."
        )

    print(f"  * Linking upload to lesson {lesson.id}...")
    # 5. Link .zip to content
    response = requests.patch(
        database.url + f"/items/lessons/{lesson.id}",
        json={"translations": [{"id": translation_id, "temporal_file": temp_file_id}]},
        headers=auth_header,
    )
    if response.status_code != 200:
        raise Exception(
            f"Problem connecting to Directus (error code {response.status_code})."
        )

    # 6. Clean up zipped file afterwards
    print(f"  * Cleaning up `{lesson.zip_path.name}`...")
    os.remove(lesson.zip_path)

    print("  ✨ Complete! ✨")

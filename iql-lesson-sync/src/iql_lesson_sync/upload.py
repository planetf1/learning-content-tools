import shutil
import tempfile
import os
from pathlib import Path
from getpass import getpass
import random
import requests
import sys
from yaspin import yaspin
from yaspin.spinners import Spinners


class Lesson:
    def __init__(self, lesson_path, lesson_id):
        self.path = Path(lesson_path)
        self.name = self.path.parts[-1]
        self.id = lesson_id
        self.zip_path = None

    def zip(self):
        self.zip_path = Path(
            shutil.make_archive(
                Path(tempfile.gettempdir(), "iql_lesson_sync", self.name),
                "zip",
                root_dir=self.path,
            )
        )

    def delete_zip(self):
        if self.zip_path and self.zip_path.exists():
            os.remove(self.zip_path)


class Database:
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.auth_header = {"Authorization": f"Bearer {self.get_access_token()}"}

    def get_access_token(self):
        """
        Either token is in env variable, or we use login details to get temporary
        access token.
        """
        if os.environ.get("LEARNING_API_TOKEN", None) is not None:
            print(f'✅ Found token for "{self.name}"')
            return os.environ.get("LEARNING_API_TOKEN")

        print(f'🔑 Log into "{self.name}":')
        response = requests.post(
            f"{self.url}/auth/login",
            json=(
                {
                    "email": input("   Email: "),
                    "password": getpass("   Password: "),
                }
            ),
        )
        if response.status_code != 200:
            print("❌ Couldn't log in 😕")
            sys.exit()

        print(f'✅ Logged into "{self.name}"')
        return response.json()["data"]["access_token"]

    def push(self, lesson: Lesson):
        """
        Wrapper for `_push` to handle spinner and Exceptions
        """
        base_msg = f'Push "{lesson.name}"'
        spinner = yaspin(Spinners.dots12, text=base_msg, color="blue")
        spinner.start()

        def _log_fn(msg):
            spinner.text = f"{base_msg}: {msg}"

        try:
            self._push(lesson, _log_fn)

        except KeyboardInterrupt:
            _log_fn("Cancelled by user")
            spinner.fail("❌")
            lesson.delete_zip()
            sys.exit()

        except Exception as err:
            spinner.fail("❌")
            lesson.delete_zip()
            raise err

        spinner.text = base_msg
        spinner.ok("✅")

    def _push(self, lesson: Lesson, log):
        """
        Steps:
          1. Get the translation ID of the English translation (needed for upload)
          2. Zip the folder containing source files
          3. Upload the zip file to the database
          4. Link the zip file in the database to the lesson
          5. Clean up: delete the zip file from local disk

        Args:
            lesson (Lesson)
            log (callable): accepts a string to show to user
        """
        # 1. Get ID of english translation (needed for upload)
        log("Finding English translation...")
        response = requests.get(
            f"{self.url}/items/lessons/{lesson.id}"
            "?fields[]=translations.id,translations.languages_code",
            headers=self.auth_header
        )
        response.raise_for_status()

        for translation in response.json()["data"]["translations"]:
            if translation["languages_code"] == "en-US":
                translation_id = translation["id"]
                break
            raise ValueError("No 'en-US' translation found!")

        # 2. Zip file
        log("Zipping folder...")
        lesson.zip()

        # 3. Upload .zip
        log("Uploading...")
        with open(lesson.zip_path, "rb") as fileobj:
            response = requests.post(
                self.url + "/files",
                files={"file": (fileobj)},
                data={"filename": lesson.zip_path.stem},
                headers=self.auth_header,
            )
        response.raise_for_status()
        temp_file_id = response.json()["data"]["id"]

        log("Linking upload...")
        # 4. Link .zip to content
        response = requests.patch(
            self.url + f"/items/lessons/{lesson.id}",
            json={
                "translations": [{"id": translation_id, "temporal_file": temp_file_id}]
            },
            headers=self.auth_header,
        )
        response.raise_for_status()

        # 5. Clean up zipped file afterwards
        log("Cleaning up...")
        lesson.delete_zip()

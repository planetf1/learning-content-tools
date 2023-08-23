import shutil
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
                self.path / f"{random.randint(0, 1_000_000_000)}_{self.name}",
                "zip",
                root_dir=self.path,
            )
        )

    def delete_zip(self):
        if self.zip_path  and self.zip_path.exists():
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
            return os.environ.get("LEARNING_API_TOKEN").strip()

        print(f'\n🔑 Log into "{self.name}":')
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
        Steps:
          1. Get the translation ID of the English translation (needed for upload)
          2. Zip the folder containing source files
          3. Upload the zip file to the database
          4. Link the zip file in the database to the lesson
          5. Clean up: delete the zip file from local disk

        Args:
            lesson (Lesson)
        """
        base_msg = f" Push '{lesson.name}'"
        spinner = yaspin(Spinners.dots2, text=base_msg, color="blue")
        spinner.start()

        try:
            # 1. Get ID of english translation (needed for upload)
            spinner.text = base_msg + ": Finding English translation..."
            response = requests.get(
                f"{self.url}/items/lessons/{lesson.id}"
                "?fields[]=translations.id,translations.languages_code",
                headers=self.auth_header,
            )
            if response.status_code != 200:
                raise Exception(
                    f"Problem connecting to database (error code {response.status_code})."
                )

            for translation in response.json()["data"]["translations"]:
                if translation["languages_code"] == "en-US":
                    translation_id = translation["id"]
                    break
                raise ValueError("No 'en-US' translation found!")

            # 2. Zip file
            spinner.text = base_msg + ": Zipping folder..."
            lesson.zip()

            # 3. Upload .zip
            spinner.text = base_msg + f': Uploading...'
            with open(lesson.zip_path, "rb") as fileobj:
                response = requests.post(
                    self.url + "/files",
                    files={"file": (fileobj)},
                    data={"filename": lesson.zip_path.stem},
                    headers=self.auth_header,
                )

            temp_file_id = response.json()["data"]["id"]
            if response.status_code != 200:
                raise Exception(
                    f"Problem connecting to database (error code {response.status_code})."
                )

            spinner.text = base_msg + f": Linking upload..."
            # 4. Link .zip to content
            response = requests.patch(
                self.url + f"/items/lessons/{lesson.id}",
                json={
                    "translations": [
                        {"id": translation_id, "temporal_file": temp_file_id}
                    ]
                },
                headers=self.auth_header,
            )
            if response.status_code != 200:
                raise Exception(
                    f"Problem connecting to database (error code {response.status_code})."
                )

            # 5. Clean up zipped file afterwards
            spinner.text = base_msg + f': Cleaning up...'
            lesson.delete_zip()

            spinner.text = base_msg.strip()

        except KeyboardInterrupt:
            spinner.text = base_msg.strip() + ": Cancelled by user"
            spinner.fail("❌")
            lesson.delete_zip()
            sys.exit()

        except Exception as err:
            lesson.delete_zip()
            spinner.fail("❌")
            raise err

        spinner.ok("✅")


import sys
import os
import yaml
from pathlib import Path
from .upload import Lesson, Database

CONF_FILE = "./database.conf.yaml"
URLS = {"staging": "https://learning-api-dev.quantum-computing.ibm.com"}


def sync_lessons():
    database_name = os.environ.get("LEARNING_API_NAME", "staging").lower()
    database = Database(database_name, URLS[database_name])

    lesson_ids = parse_yaml(database_name)
    if len(sys.argv) > 1:
        paths = sys.argv[1:]
    else:
        paths = lesson_ids.keys()

    for lesson_path in paths:
        lesson = Lesson(lesson_path, lesson_ids[lesson_path])
        database.push(lesson)

    print("✨ Sync complete! ✨\n")


def parse_yaml(database_name):
    """
    Get dict of lesson paths and lesson IDs
    Args:
        path_to_yaml (str): path to database.conf.yaml
        database_name (str): "staging" or "production"
    Returns:
        dict: { lesson_path: lesson_id }
    """
    with open(CONF_FILE) as f:
        database_info = yaml.safe_load(f.read())

    output = {}
    for lesson in database_info["lessons"]:
        path = lesson["path"]
        lesson_id = lesson[f"id{database_name.lower().capitalize()}"]
        output[path] = lesson_id

    return output
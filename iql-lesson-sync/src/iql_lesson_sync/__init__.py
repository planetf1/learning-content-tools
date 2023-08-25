import sys
import os
import yaml
from pathlib import Path
from .upload import Lesson, Database

CONF_FILE = "./iql.conf.yaml"
DATABASE_URLS = {
    "staging": "https://learning-api-dev.quantum-computing.ibm.com",
    "production": "learning-api.quantum-computing.ibm.com"
}
WEBSITE_URLS = {
    "staging": "https://learning.www-dev.quantum-computing.ibm.com",
    "production": "https://learning.quantum-computing.ibm.com"
}

def get_database_name():
    """
    Either from environment token or user
    """
    if os.environ.get("LEARNING_API_ENVIRONMENT", False):
        return os.environ.get("LEARNING_API_ENVIRONMENT").lower()

    if os.environ.get("LEARNING_API_TOKEN", False):
        raise EnvironmentError(
                "Set 'LEARNING_API_ENVIRONMENT' variable to 'staging' or "
                "'production' when using the 'LEARNING_API_TOKEN' environment "
                "variable. You can unset the token using the command:\n\n    "
                "unset LEARNING_API_TOKEN\n"
        )

    response = input("Push to staging or production? (s/p): ").lower()
    if response in ['s', 'staging']:
        return 'staging'
    if response in ['p', 'production']:
        return 'production'
    print("Not understood; enter either 's' for staging or 'p' for production.")
    print("Trying again...")
    return get_database_name()


def sync_lessons():
    print()
    database_name = get_database_name()
    database = Database(database_name, DATABASE_URLS[database_name], WEBSITE_URLS[database_name])

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
        path_to_yaml (str): path to iql.conf.yaml
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

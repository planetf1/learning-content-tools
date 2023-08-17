import sys
from .upload import push_notebook

def sync_notebooks():
    for notebook in sys.argv[1:]:
        push_notebook(notebook)

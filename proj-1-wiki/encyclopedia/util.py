import re

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

import markdown2
import random

def list_entries():
    """
    Returns a list of all names of encyclopedia entries.
    """
    _, filenames = default_storage.listdir("entries")
    return list(sorted(re.sub(r"\.md$", "", filename)
                for filename in filenames if filename.endswith(".md")))


def save_entry(title, content):
    """
    Saves an encyclopedia entry, given its title and Markdown
    content. If an existing entry with the same title already exists,
    it is replaced.
    """
    filename = f"entries/{title}.md"
    if default_storage.exists(filename):
        default_storage.delete(filename)
    default_storage.save(filename, ContentFile(content))


def get_entry(title, html=True):
    """
    Retrieves an encyclopedia entry by its title. If no such
    entry exists, the function returns None.
    """
    try:
        f = default_storage.open(f"entries/{title}.md")
        if html:
            return markdown2.markdown(f.read().decode("utf-8"))
        else:
            return f.read().decode("utf-8")
    except FileNotFoundError:
        return None
    

def search_entries(query):
    """
    Retrieves a list of encyclopedia entries that contain the query.
    """
    return [entry for entry in list_entries() if query.lower() in entry.lower()]


def random_entry():
    """
    Retrieves a random encyclopedia entry.
    """
    entries = list_entries()
    return random.choice(entries) if entries else None
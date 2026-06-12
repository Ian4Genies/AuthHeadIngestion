import os


def list_fbx_files(directory: str) -> list[str]:
    if not directory or not os.path.isdir(directory):
        return []

    paths = []
    for entry in sorted(os.scandir(directory), key=lambda item: item.name.lower()):
        if not entry.is_file():
            continue
        if entry.name.lower().endswith(".fbx"):
            paths.append(entry.path)
    return paths

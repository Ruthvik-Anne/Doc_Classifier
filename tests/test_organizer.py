from pathlib import Path
import shutil

from smart_organizer.config import Config
from smart_organizer.organizer import SmartFileOrganizer


def test_get_category_by_extension():
    cfg = Config()
    org = SmartFileOrganizer(cfg)

    assert org.get_category_by_extension(Path('file.pdf')) == 'Documents'
    assert org.get_category_by_extension(Path('image.jpg')) == 'Images'
    assert org.get_category_by_extension(Path('song.mp3')) == 'Audio'


def test_organize_file_makes_destination(tmp_path, monkeypatch):
    # Prepare config to use temp directories
    cfg = Config()
    monkeypatch.setattr(cfg, 'watch_dir', tmp_path)
    monkeypatch.setattr(cfg, 'organized_dir', tmp_path / '_organized')

    # Disable AI for speed
    monkeypatch.setattr(cfg, 'use_ai', False)

    org = SmartFileOrganizer(cfg)

    # Create a sample file
    src = tmp_path / 'image.jpg'
    src.write_bytes(b"fake")

    # Monkeypatch detector to return image mime type
    monkeypatch.setattr(org.detector, 'detect', lambda p: {'mime_type': 'image/jpeg'})

    dest = org.organize_file(src)
    assert dest.exists()
    assert dest.parent.name in ('Images', 'Others')

    # Cleanup any temp organized folder if created
    if (tmp_path / '_organized').exists():
        shutil.rmtree(tmp_path / '_organized')

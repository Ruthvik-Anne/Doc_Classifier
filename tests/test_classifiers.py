from pathlib import Path
from smart_organizer.config import Config
from smart_organizer.classifiers import ImageClassifier, DocumentClassifier


def test_config_loads():
    cfg = Config()
    assert cfg.get('use_ai') is not None


def test_image_classifier_model_path_missing(tmp_path, monkeypatch):
    cfg = Config()

    # Override model path to a non-existent file
    monkeypatch.setattr(cfg, 'get', lambda k, default=None: 'missing_model.tflite' if k == 'models.image_classifier' else default)

    clf = ImageClassifier(cfg)
    try:
        clf.load_model()
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        assert True


def test_document_classifier_basic(monkeypatch, tmp_path):
    cfg = Config()

    # Reduce model to a small one to avoid heavy downloads in CI
    monkeypatch.setattr(cfg, 'get', lambda k, default=None: 'all-MiniLM-L6-v2' if k == 'models.sentence_encoder' else default)

    clf = DocumentClassifier(cfg)
    clf.load_model()

    # Create a small text file
    text_file = tmp_path / 'sample.txt'
    text_file.write_text('This is a short report about quarterly performance and financial results.')

    result = clf.classify(text_file, mime_type='text/plain')
    assert 'label' in result
    assert 'confidence' in result

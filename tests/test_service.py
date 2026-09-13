import pytest

from service import multimodal


class FakeEncoder:
    def text(self, text):
        return [1., 0.] if "cat" in text else [0., 1.]

    def image(self, path):
        return [1., 0.] if path.stem == "cat" else [0., 1.]


def test_text_to_image_ranking():
    rows = [{"id": "cat", "caption": "", "image_path": "/tmp/cat.png"},
            {"id": "dog", "caption": "", "image_path": "/tmp/dog.png"}]
    indexed = multimodal.build_index(rows, FakeEncoder())
    assert multimodal.search("cat", indexed, FakeEncoder())[0]["id"] == "cat"


def test_catalog_cannot_escape_root(tmp_path):
    catalog = tmp_path / "catalog.jsonl"
    catalog.write_text('{"id":"x","image_path":"../secret.png"}\n')
    with pytest.raises(ValueError, match="Invalid image path"):
        multimodal.load_catalog(catalog, tmp_path)

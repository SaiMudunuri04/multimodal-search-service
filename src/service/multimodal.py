"""Text-to-image retrieval over a local image and caption catalog using CLIP."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Protocol


def normalize(values: list[float]) -> list[float]:
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError("Embedding must contain finite numbers")
    length = math.sqrt(sum(value * value for value in values))
    if length == 0:
        raise ValueError("Zero embedding")
    return [value / length for value in values]


class Encoder(Protocol):
    def text(self, text: str) -> list[float]: ...
    def image(self, path: Path) -> list[float]: ...


class CLIPEncoder:
    def __init__(self, model_id: str = "openai/clip-vit-base-patch32"):
        import torch
        from transformers import AutoProcessor, CLIPModel
        self.torch = torch
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = CLIPModel.from_pretrained(model_id).eval()

    @staticmethod
    def _vector(output) -> list[float]:
        tensor = output.pooler_output if hasattr(output, "pooler_output") else output
        return normalize(tensor[0].detach().cpu().tolist())

    def text(self, text: str) -> list[float]:
        inputs = self.processor(text=[text], return_tensors="pt", padding=True)
        with self.torch.inference_mode():
            return self._vector(self.model.get_text_features(input_ids=inputs["input_ids"],
                                                              attention_mask=inputs["attention_mask"]))

    def image(self, path: Path) -> list[float]:
        from PIL import Image
        with Image.open(path) as image:
            inputs = self.processor(images=image.convert("RGB"), return_tensors="pt")
        with self.torch.inference_mode():
            return self._vector(self.model.get_image_features(pixel_values=inputs["pixel_values"]))


def load_catalog(path: Path, root: Path) -> list[dict]:
    records = []
    seen = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if not record.get("id") or record["id"] in seen:
            raise ValueError("Catalog IDs must be unique and nonempty")
        seen.add(record["id"])
        image_path = (root / record["image_path"]).resolve()
        if not image_path.is_relative_to(root.resolve()) or not image_path.is_file():
            raise ValueError(f"Invalid image path for {record['id']}")
        records.append({"id": record["id"], "caption": str(record.get("caption", "")),
                        "image_path": str(image_path)})
    if not records:
        raise ValueError("Catalog is empty")
    return records


def build_index(records: list[dict], encoder: Encoder, caption_weight: float = 0.25) -> list[dict]:
    if not 0 <= caption_weight <= 1:
        raise ValueError("caption_weight must be between 0 and 1")
    indexed = []
    dimensions = None
    for record in records:
        visual = normalize(encoder.image(Path(record["image_path"])))
        if dimensions is None:
            dimensions = len(visual)
        elif len(visual) != dimensions:
            raise ValueError("Image embedding dimensions differ")
        caption = record["caption"]
        if caption:
            textual = normalize(encoder.text(caption))
            if len(textual) != len(visual):
                raise ValueError("Caption and image embedding dimensions differ")
            vector = normalize([(1 - caption_weight) * v + caption_weight * t
                                for v, t in zip(visual, textual)])
        else:
            vector = visual
        indexed.append({**record, "embedding": vector})
    return indexed


def search(query: str, indexed: list[dict], encoder: Encoder, limit: int = 5) -> list[dict]:
    if not query.strip() or limit < 1:
        raise ValueError("A nonempty query and positive limit are required")
    question = normalize(encoder.text(query))
    if any(len(item["embedding"]) != len(question) for item in indexed):
        raise ValueError("Query and catalog embedding dimensions differ")
    ranked = sorted(indexed,
                    key=lambda item: (-sum(a * b for a, b in zip(question, item["embedding"])), item["id"]))
    return [{"id": item["id"], "image_path": item["image_path"],
             "caption": item["caption"],
             "score": round(sum(a * b for a, b in zip(question, item["embedding"])), 5)}
            for item in ranked[:limit]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path)
    parser.add_argument("image_root", type=Path)
    parser.add_argument("query")
    parser.add_argument("--model", default="openai/clip-vit-base-patch32")
    args = parser.parse_args()
    encoder = CLIPEncoder(args.model)
    result = search(args.query, build_index(load_catalog(args.catalog, args.image_root), encoder), encoder)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

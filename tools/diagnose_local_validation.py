from pathlib import Path
from tempfile import TemporaryDirectory
from orville_core.local_models import LocalModelCatalog

with TemporaryDirectory() as directory:
    root = Path(directory)
    model_path = root / "model.gguf"
    model_path.write_bytes(b"fake model weights")
    catalog = LocalModelCatalog(root / "catalog.json")
    record = catalog.import_model(model_path, model_id="local-2", runtime="ollama", endpoint="http://localhost:11434")
    print(record)
    print(catalog.validate("local-2"))

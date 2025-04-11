import json
import os
import random
from typing import List, Optional, Dict, Any


class StreamerMetadataTracker:
    def __init__(self, filepath: str = "streamers_metadata.json"):
        self.filepath = filepath
        self.metadata: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    print("Metadata file is corrupted. Starting fresh.")
                    return []
        return []

    def save(self):
        with open(self.filepath, "w") as f:
            json.dump(self.metadata, f, indent=4)

    def append(self, entry: Dict[str, Any]):
        self.metadata.append(entry)
        self.save()

    def all(self) -> List[Dict[str, Any]]:
        return self.metadata

    def weighted_choice(self, key: str = "viewer_share") -> Optional[Dict[str, Any]]:
        if not self.metadata:
            return None
        total_weight = sum(float(item.get(key, 1)) for item in self.metadata)
        r = random.uniform(0, total_weight)
        upto = 0
        for item in self.metadata:
            weight = float(item.get(key, 1))
            if upto + weight >= r:
                return item
            upto += weight
        return random.choice(self.metadata)

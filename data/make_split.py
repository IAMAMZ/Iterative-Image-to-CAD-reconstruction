"""DeepCAD dev/test split: python make_split.py <train_val_test_split.json> <data dir>
writes <data dir>/deepcad/{dev,test}/ids.txt and <data dir>/deepcad/split_meta.json"""
import json, os, random, sys
SEED = 2529
src = sys.argv[1]; out = sys.argv[2]
ids = sorted(json.load(open(src))["test"])
rng = random.Random(SEED)
pick = rng.sample(ids, 200)
dev, test = sorted(pick[:100]), sorted(pick[100:])
for name, part in (("dev", dev), ("test", test)):
    os.makedirs(f"{out}/deepcad/{name}", exist_ok=True)
    open(f"{out}/deepcad/{name}/ids.txt", "w").write("\n".join(part) + "\n")
json.dump({"seed": SEED, "source_split": "test", "n_source": len(ids), "n_dev": 100, "n_test": 100}, open(f"{out}/deepcad/split_meta.json", "w"), indent=2)

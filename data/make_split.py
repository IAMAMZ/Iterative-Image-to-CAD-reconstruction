import json, random, sys
SEED = 2529
src = sys.argv[1]; out = sys.argv[2]
ids = sorted(json.load(open(src))["test"])
rng = random.Random(SEED)
pick = rng.sample(ids, 200)
dev, test = sorted(pick[:100]), sorted(pick[100:])
open(f"{out}/dev.txt", "w").write("\n".join(dev) + "\n")
open(f"{out}/test.txt", "w").write("\n".join(test) + "\n")
json.dump({"seed": SEED, "source_split": "test", "n_source": len(ids), "n_dev": 100, "n_test": 100}, open(f"{out}/meta.json", "w"), indent=2)

import json, math, pathlib
path = pathlib.Path("/Users/florinolariu/Downloads/journalimplementationver2 3/metrics_n10.jsonl")
rows = [json.loads(line) for line in path.read_text().splitlines()]

def pack(key):
    vals = [r[key] for r in rows]
    mean = sum(vals)/len(vals)
    stdev = (sum((x-mean)**2 for x in vals)/len(vals))**0.5
    return {"values": vals, "mean": mean, "stdev": stdev}

summary = {k: pack(k) for k in ["pre","post","dup","pareto","total_time_ms"]}
print(json.dumps(summary, indent=2))

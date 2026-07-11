"""
converter.py
=============
Converts any supported dataset (Dolly-15k, Alpaca, OpenAssistant, UltraChat,
or your own custom source) into ONE unified routing dataset using
router_labeler.build_record() as the single labeling engine.

Design principle (per project spec, point 11):
    "The feature extractor should work for ANY dataset. Only the loader
    should change."

Each loader below is a thin adapter: it knows how to pull (query, context,
style) triples out of one dataset's native schema, and nothing else. All
labeling logic (intent, complexity, tokens, confidence, route) lives
upstream in router_labeler.py and is 100% shared across every source.

To add a new dataset: write one function `load_<name>()` that yields
(query, context, style) tuples, then register it in LOADERS at the bottom.
"""

import json
import csv
from typing import Iterator, Tuple, Optional

from router_labeler import build_record

# A loader yields (query, context, style) tuples. context/style may be None.
LoaderOutput = Iterator[Tuple[str, Optional[str], str]]


# ─────────────────────────────────────────────────────────────────────────
# DATASET LOADERS — only these change per new dataset
# ─────────────────────────────────────────────────────────────────────────

def load_dolly(limit: Optional[int] = None) -> LoaderOutput:
    """
    Databricks Dolly-15k. Fields: instruction, context, response, category.
    Requires: pip install datasets
    """
    from datasets import load_dataset
    ds = load_dataset("databricks/databricks-dolly-15k")["train"]
    for i, row in enumerate(ds):
        if limit and i >= limit:
            break
        instruction = row.get("instruction", "").strip()
        context = row.get("context", "").strip() or None
        if not instruction:
            continue
        yield instruction, context, "dolly"


def load_alpaca(limit: Optional[int] = None) -> LoaderOutput:
    """
    Stanford Alpaca. Fields: instruction, input, output.
    Requires: pip install datasets
    """
    from datasets import load_dataset
    ds = load_dataset("tatsu-lab/alpaca")["train"]
    for i, row in enumerate(ds):
        if limit and i >= limit:
            break
        instruction = row.get("instruction", "").strip()
        context = row.get("input", "").strip() or None
        if not instruction:
            continue
        yield instruction, context, "alpaca"


def load_oasst(limit: Optional[int] = None) -> LoaderOutput:
    """
    OpenAssistant Conversations (OASST1/2). Fields: text, role, parent_id, ...
    Only 'prompter' (human) turns become queries; each is used standalone
    since full conversation-tree reconstruction is out of scope for this
    router-labeling pass.
    Requires: pip install datasets
    """
    from datasets import load_dataset
    ds = load_dataset("OpenAssistant/oasst1")["train"]
    count = 0
    for row in ds:
        if row.get("role") != "prompter":
            continue
        text = (row.get("text") or "").strip()
        if not text:
            continue
        yield text, None, "oasst"
        count += 1
        if limit and count >= limit:
            break


def load_ultrachat(limit: Optional[int] = None) -> LoaderOutput:
    """
    UltraChat-200k. Fields: messages (list of {role, content} turns).
    Only the first user turn per conversation is used as the query — later
    turns depend on conversational context this pipeline doesn't model.
    Requires: pip install datasets
    """
    from datasets import load_dataset
    ds = load_dataset("HuggingFaceH4/ultrachat_200k")["train_sft"]
    for i, row in enumerate(ds):
        if limit and i >= limit:
            break
        messages = row.get("messages", [])
        first_user_msg = next((m["content"] for m in messages if m.get("role") == "user"), None)
        if not first_user_msg:
            continue
        yield first_user_msg.strip(), None, "ultrachat"


def load_linux_nl2bash(limit: Optional[int] = None) -> LoaderOutput:
    """
    NL2Bash — real English-to-bash command corpus (TellinaTool/nl2bash,
    MIT licensed, ~12,600 pairs). Downloaded directly from GitHub raw
    files, no HF datasets dependency needed.

    Only the English query is used; the bash command itself isn't needed
    since this pipeline's intent/complexity/route labeling all operates
    on the natural-language query, not the target command.
    """
    import urllib.request

    nl_url = "https://raw.githubusercontent.com/TellinaTool/nl2bash/master/data/bash/all.nl"
    with urllib.request.urlopen(nl_url) as resp:
        lines = resp.read().decode("utf-8", errors="ignore").splitlines()

    count = 0
    for line in lines:
        query = line.strip().rstrip(".")
        if not query:
            continue
        yield query, None, "linux_nl2bash"
        count += 1
        if limit and count >= limit:
            break


def load_linux_synthetic(limit: Optional[int] = None) -> LoaderOutput:
    """
    Synthetic Linux command queries generated from templates covering
    12 common sysadmin categories (file ops, disk usage, processes,
    permissions, services, networking, logs, etc.) across 4 phrasing
    styles (casual, formal, terse, typo). Free, unlimited, fully
    controllable — no external download required.

    This complements load_linux_nl2bash(): NL2Bash gives real, messy
    phrasing; this gives clean, systematic coverage across intent x
    complexity-tier x phrasing-style combinations.
    """
    import random

    random.seed(7)

    dirs = ["home directory", "downloads folder", "/var/log", "/tmp", "current directory", "Desktop"]
    filetypes = ["log files", "images", "videos", "text files", "backups", "config files"]
    sizes = ["100MB", "500MB", "1GB", "2GB", "50MB"]
    timeperiods = ["last week", "last 24 hours", "last month", "yesterday"]
    processes = ["chrome", "python", "nginx", "mysql", "node", "docker"]
    services = ["nginx", "apache2", "mysql", "docker", "ssh", "redis"]
    packages = ["curl", "git", "vim", "htop", "python3-pip", "nodejs"]

    templates = [
        "show me files in {dir}", "list all files in {dir}",
        "check disk usage", "how much disk space do I have left",
        "show running processes", "is {process} running",
        "kill {process}", "stop the {process} process",
        "check my internet connection", "show network status",
        "install {package}", "update {package}",
        "show system info", "what's my os version",
        "find files named {filetype} in {dir}", "search for files larger than {size}",
        "start {service}", "restart {service}", "check status of {service}",
        "compress {dir}", "zip up {filetype} in {dir}",
        "check logs from {timeperiod}", "tail the system logs",
        "delete all {filetype} in {dir} older than {timeperiod} and compress the rest",
        "recursively change permissions on {dir}",
        "find all {filetype} larger than {size} and remove duplicates",
    ]

    def fill(t):
        return t.format(
            dir=random.choice(dirs), filetype=random.choice(filetypes),
            size=random.choice(sizes), timeperiod=random.choice(timeperiods),
            process=random.choice(processes), service=random.choice(services),
            package=random.choice(packages),
        )

    count = 0
    seen = set()
    attempts = 0
    max_attempts = (limit or 500) * 20  # safety cap to avoid infinite loop if dedup exhausts variety

    while (not limit or count < limit) and attempts < max_attempts:
        attempts += 1
        template = random.choice(templates)
        query = fill(template)
        if query in seen:
            continue
        seen.add(query)
        yield query, None, "linux_synthetic"
        count += 1


def load_wizardlm_evol(limit: Optional[int] = None) -> LoaderOutput:
    """
    WizardLM Evol-Instruct 70k. Fields: instruction, output.

    This dataset exists specifically to counter LOCAL-skew: it takes
    Alpaca/ShareGPT-style instructions and deliberately REWRITES them to be
    more complex through a documented "evolution" process — adding
    constraints, deepening required reasoning, increasing steps, concretizing
    vague requests. Where Dolly/Alpaca/OASST skew heavily toward simple
    single-step instructions, this dataset is purpose-built to skew hard the
    other way, which is exactly the correction your merged dataset needs.
    Requires: pip install datasets
    """
    from datasets import load_dataset
    ds = load_dataset("WizardLMTeam/WizardLM_evol_instruct_70k")["train"]
    for i, row in enumerate(ds):
        if limit and i >= limit:
            break
        instruction = (row.get("instruction") or "").strip()
        if not instruction:
            continue
        yield instruction, None, "wizardlm_evol"


def load_gsm8k(limit: Optional[int] = None) -> LoaderOutput:
    """
    GSM8K (Grade School Math 8K). Fields: question, answer.

    Multi-step math word problems (2-8 reasoning steps each) — genuinely
    hard for a small local model, genuinely easy to justify CLOUD routing.
    Only the question is used as the query; the answer/reasoning trace
    isn't needed for labeling.
    Requires: pip install datasets
    """
    from datasets import load_dataset
    ds = load_dataset("openai/gsm8k", "main")["train"]
    for i, row in enumerate(ds):
        if limit and i >= limit:
            break
        question = (row.get("question") or "").strip()
        if not question:
            continue
        yield question, None, "gsm8k"


def load_custom_jsonl(filepath: str, query_field: str = "query",
                       context_field: Optional[str] = None,
                       limit: Optional[int] = None) -> LoaderOutput:
    """
    Generic loader for your own JSONL files (e.g. the Linux command corpus
    built earlier). Reads one JSON object per line.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            query = row.get(query_field, "").strip()
            context = row.get(context_field, "").strip() if context_field else None
            if not query:
                continue
            yield query, context, "custom"


LOADERS = {
    "dolly": load_dolly,
    "alpaca": load_alpaca,
    "oasst": load_oasst,
    "ultrachat": load_ultrachat,
    "linux_nl2bash": load_linux_nl2bash,
    "linux_synthetic": load_linux_synthetic,
    "wizardlm_evol": load_wizardlm_evol,
    "gsm8k": load_gsm8k,
}


# ─────────────────────────────────────────────────────────────────────────
# CONVERSION PIPELINE — shared by all datasets, never needs to change
# ─────────────────────────────────────────────────────────────────────────

def convert_dataset(source_name: str, limit: Optional[int] = None, verbose: bool = True) -> list:
    """
    Run one registered loader through build_record() and return the list
    of fully labeled routing records.
    """
    if source_name not in LOADERS:
        raise ValueError(f"Unknown source '{source_name}'. Available: {list(LOADERS)}")

    loader_fn = LOADERS[source_name]
    records = []

    for i, (query, context, style) in enumerate(loader_fn(limit=limit)):
        try:
            record = build_record(query, context=context, style=style)
            record["source_dataset"] = source_name
            records.append(record)
        except Exception as e:
            if verbose:
                print(f"  [skip] row {i} failed: {e}")
            continue

        if verbose and (i + 1) % 5000 == 0:
            print(f"  ...{source_name}: {i + 1} rows processed")

    if verbose:
        local_n = sum(1 for r in records if r["recommended_route"] == "LOCAL")
        cloud_n = sum(1 for r in records if r["recommended_route"] == "CLOUD")
        print(f"[{source_name}] done: {len(records)} records | LOCAL={local_n} CLOUD={cloud_n}")

    return records


def save_records(records: list, out_prefix: str) -> None:
    """Save records to both JSON and CSV. Always writes UTF-8 explicitly —
    relying on the platform default encoding fails on Windows (cp1252)
    whenever a query contains non-ASCII characters (e.g. Greek letters,
    accented text, curly quotes pulled in from real dataset content)."""
    if not records:
        print("No records to save.")
        return

    with open(f"{out_prefix}.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    fieldnames = list(records[0].keys())
    with open(f"{out_prefix}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Saved {out_prefix}.json and {out_prefix}.csv ({len(records)} rows)")


def convert_custom_jsonl(filepath: str, query_field: str = "query",
                          context_field: Optional[str] = None,
                          limit: Optional[int] = None, verbose: bool = True) -> list:
    """
    Convert a custom JSONL file (e.g. your own Linux command corpus) using
    the same build_record() engine as the registered dataset loaders.
    Kept separate from convert_dataset() because load_custom_jsonl() needs
    a filepath argument the registry-based loaders don't have.
    """
    records = []
    for i, (query, context, style) in enumerate(load_custom_jsonl(filepath, query_field, context_field, limit)):
        try:
            record = build_record(query, context=context, style=style)
            record["source_dataset"] = "custom"
            records.append(record)
        except Exception as e:
            if verbose:
                print(f"  [skip] row {i} failed: {e}")
            continue
    if verbose:
        local_n = sum(1 for r in records if r["recommended_route"] == "LOCAL")
        cloud_n = sum(1 for r in records if r["recommended_route"] == "CLOUD")
        print(f"[custom:{filepath}] done: {len(records)} records | LOCAL={local_n} CLOUD={cloud_n}")
    return records


def convert_all(sources: dict, out_prefix: str = "unified_route_dataset") -> list:
    """
    Convert multiple datasets and merge into ONE unified file.

    Args:
        sources: {"dolly": 2000, "alpaca": 2000, "oasst": 1000, "ultrachat": 1000}
                 maps source name -> row limit (None = no limit, use full dataset)
        out_prefix: output filename prefix (produces .json and .csv)
    """
    all_records = []
    for source_name, limit in sources.items():
        print(f"\nConverting {source_name} (limit={limit})...")
        records = convert_dataset(source_name, limit=limit)
        all_records.extend(records)

    # dedupe across all sources by query text
    seen = set()
    deduped = []
    for r in all_records:
        if r["query"] not in seen:
            seen.add(r["query"])
            deduped.append(r)

    print(f"\nTotal before dedup: {len(all_records)} | after dedup: {len(deduped)}")

    local_n = sum(1 for r in deduped if r["recommended_route"] == "LOCAL")
    cloud_n = sum(1 for r in deduped if r["recommended_route"] == "CLOUD")
    print(f"Final split -> LOCAL: {local_n} | CLOUD: {cloud_n}")

    save_records(deduped, out_prefix)
    return deduped


if __name__ == "__main__":
    # Using limit=None pulls the FULL dataset for that source. Combined,
    # the four sources below give ~300k+ queries before dedup:
    #   dolly      ~15,000
    #   alpaca     ~52,000
    #   oasst      ~40,000-45,000 (prompter turns only)
    #   ultrachat  ~207,000
    # If you only need >200k total, you can keep one source capped (e.g.
    # oasst) and still clear the target comfortably.
    convert_all(
        sources={
            "dolly": None,
            "alpaca": None,
            "oasst": None,
            "ultrachat": None,
            "wizardlm_evol": None,
        },
        out_prefix="unified_route_dataset",
    )
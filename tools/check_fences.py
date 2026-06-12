import re, glob

PROSE_CHECK = re.compile(
    r"\b(doesn|don't|The |This |In |is |are |was |were |creates|supports|outcome|allows|provides)\b",
    re.IGNORECASE
)

total_bad = 0
for ch in range(1, 11):
    files = glob.glob(
        rf"F:\Personal\Projects\Data_engineering\Data Engineering Design Patterns\ch{ch:02d}_*.md"
    )
    if not files:
        continue
    content = open(files[0], encoding="utf-8").read()
    blocks = re.findall(r"```(\w+)\n(.*?)```", content, re.DOTALL)
    bad = []
    for lang, body in blocks:
        first = body.strip().split("\n")[0]
        if PROSE_CHECK.search(first):
            bad.append((lang, first[:90]))
    if bad:
        print(f"Ch{ch}: {len(bad)} suspect:")
        for lang, first in bad:
            print(f"  [{lang}] {first}")
        total_bad += len(bad)
    else:
        print(f"Ch{ch}: CLEAN ({len(blocks)} fenced blocks)")

print(f"\nTotal suspect blocks: {total_bad}")

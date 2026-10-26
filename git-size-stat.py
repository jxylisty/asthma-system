import subprocess, collections, sys

repo = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\zzx05\Desktop\大床课题\asthma-system-master"

out = subprocess.run(["git", "rev-list", "--objects", "--all"], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout

path_shas = collections.defaultdict(set)
for line in out.splitlines():
    parts = line.split(" ", 1)
    if len(parts) == 2 and len(parts[0]) == 40:
        path_shas[parts[1]].add(parts[0])

# 批量获取大小
sha_list = [s for shas in path_shas.values() for s in shas]
sizes = {}
batch = subprocess.run(["git", "cat-file", "--batch-check=%(objectname) %(objectsize)"], cwd=repo,
                       input="".join(s + "\n" for s in sha_list), capture_output=True, text=True)
for line in batch.stdout.splitlines():
    parts = line.split(" ")
    if len(parts) == 2 and parts[1].isdigit():
        sizes[parts[0]] = int(parts[1])

total_by_path = {}
grand_total = 0
for path, shas in path_shas.items():
    total = sum(sizes.get(s, 0) for s in shas)
    total_by_path[path] = (total, len(shas))
    grand_total += total

print(f"{'累计体积':>10} {'版本数':>6}  路径")
print("-" * 70)
for path, (total, n) in sorted(total_by_path.items(), key=lambda x: -x[1][0])[:25]:
    print(f"{total/1024/1024:>9.1f}MB {n:>6}  {path}")

print(f"\n所有路径累计: {grand_total/1024/1024:.1f} MB")
print(f"路径总数: {len(path_shas)}")

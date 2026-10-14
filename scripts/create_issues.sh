#!/usr/bin/env bash
# Создаёт GitHub Issues из docs/planning/issues/<subject>/*.md: метки, вехи (спринты), задачи.
#
#   scripts/create_issues.sh subject-1                 # сухой прогон: только печатает, что будет сделано
#   scripts/create_issues.sh subject-1 --apply         # создать в репозитории текущего каталога
#   scripts/create_issues.sh subject-2 --apply --repo OWNER/REPO
#
# Нужны: gh (gh auth login) и python3.
# Заголовок задачи = ID + title (для предмета 2 — префикс S2-), повторный запуск не создаёт дублей.
# Задачи со status: done создаются и сразу закрываются, in-progress получают метку status:in-progress.
# Если исполнитель не участник репозитория, задача создаётся без исполнителя (с предупреждением).
set -euo pipefail

SUBJECT="${1:-}"
shift || true
APPLY=0
REPO=""
while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --repo) REPO="$2"; shift ;;
    *) echo "Неизвестный аргумент: $1" >&2; exit 2 ;;
  esac
  shift
done

if [ "$SUBJECT" != "subject-1" ] && [ "$SUBJECT" != "subject-2" ]; then
  echo "Использование: $0 subject-1|subject-2 [--apply] [--repo OWNER/REPO]" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR="$ROOT/docs/planning/issues/$SUBJECT"
[ -d "$DIR" ] || { echo "Нет каталога $DIR" >&2; exit 1; }
command -v python3 >/dev/null || { echo "Нужен python3" >&2; exit 1; }
if [ "$APPLY" = 1 ]; then
  command -v gh >/dev/null || { echo "Нужен GitHub CLI: https://cli.github.com" >&2; exit 1; }
  gh auth status >/dev/null || { echo "Выполните gh auth login" >&2; exit 1; }
fi
if [ -z "$REPO" ] && [ "$APPLY" = 1 ]; then
  REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
fi

APPLY="$APPLY" REPO="$REPO" SUBJECT="$SUBJECT" DIR="$DIR" python3 - <<'PY'
import json, os, re, subprocess, sys, tempfile

apply = os.environ["APPLY"] == "1"
repo = os.environ["REPO"] or "OWNER/REPO"
subject = os.environ["SUBJECT"]
src = os.environ["DIR"]

SPRINT_DUE = {1: "2026-09-24", 2: "2026-10-08", 3: "2026-10-22", 4: "2026-11-05",
              5: "2026-11-19", 6: "2026-12-03", 7: "2026-12-17", 8: "2026-12-25"}
LABEL_COLORS = {"subject": "5319e7", "module": "1d76db", "type": "fbca04", "sprint": "c5def5", "status": "0e8a16"}


def run(args, capture=False):
    shown = " ".join(a if re.fullmatch(r"[\w./:@=-]+", a) else repr(a) for a in args)
    if not apply:
        print("  $", shown)
        return ""
    res = subprocess.run(args, check=True, text=True, capture_output=capture)
    return res.stdout if capture else ""


def parse(path):
    text = open(path, encoding="utf-8").read()
    _, fm, body = text.split("---\n", 2)
    meta = {}
    for line in fm.strip().splitlines():
        key, value = line.split(":", 1)
        value = value.strip()
        if value.startswith("["):
            value = [v.strip() for v in value.strip("[]").split(",") if v.strip()]
        else:
            value = value.strip('"')
        meta[key.strip()] = value
    # Relative links to other task files do not work inside an issue: keep the task ID as text.
    body = re.sub(r"\[([A-Z]+-\d+)\]\((?:\.\./subject-\d/)?[A-Z]+-\d+\.md\)", r"\1", body)
    prefix = "" if subject == "subject-1" else "S2-"
    meta["gh_title"] = f"{prefix}{meta['id']} {meta['title']}"
    header = f"**ID:** {meta['id']} · **Story points:** {meta['story_points']} · **Источник:** `docs/planning/issues/{subject}/{meta['id']}.md`\n\n"
    return meta, header + body.lstrip()


tasks = [parse(os.path.join(src, f)) for f in sorted(os.listdir(src)) if f.endswith(".md")]
print(f"{subject}: {len(tasks)} задач, репозиторий {repo}, режим {'ПРИМЕНЕНИЕ' if apply else 'сухой прогон'}")

labels = sorted({l for meta, _ in tasks for l in meta["labels"]} | {"status:in-progress"})
print(f"\nМетки ({len(labels)}):")
for label in labels:
    color = LABEL_COLORS.get(label.split(":")[0].split("-")[0], "ededed")
    run(["gh", "label", "create", label, "--repo", repo, "--color", color, "--force"])

sprints = sorted({int(meta["milestone"].split()[-1]) for meta, _ in tasks})
print(f"\nВехи ({len(sprints)}):")
existing = set()
if apply:
    out = run(["gh", "api", f"repos/{repo}/milestones?state=all&per_page=100"], capture=True)
    existing = {m["title"] for m in json.loads(out)}
for n in sprints:
    title = f"Sprint {n}"
    if title in existing:
        print(f"  = {title} уже есть")
        continue
    run(["gh", "api", f"repos/{repo}/milestones", "-f", f"title={title}",
         "-f", f"due_on={SPRINT_DUE[n]}T23:59:59Z", "-f", "description=FitQuest, двухнедельный спринт"])

titles = set()
if apply:
    out = run(["gh", "issue", "list", "--repo", repo, "--state", "all", "--limit", "1000", "--json", "title"], capture=True)
    titles = {i["title"] for i in json.loads(out)}

print(f"\nЗадачи ({len(tasks)}):")
for meta, body in tasks:
    if meta["gh_title"] in titles:
        print(f"  = {meta['id']} уже существует, пропуск")
        continue
    labels = list(meta["labels"]) + (["status:in-progress"] if meta["status"] == "in-progress" else [])
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write(body)
        body_file = fh.name
    base = ["gh", "issue", "create", "--repo", repo, "--title", meta["gh_title"], "--body-file", body_file,
            "--milestone", meta["milestone"]]
    for label in labels:
        base += ["--label", label]
    print(f"  + {meta['id']} ({meta['status']}, {meta['story_points']} SP, @{meta['assignee']})")
    try:
        url = run(base + ["--assignee", meta["assignee"]], capture=True)
    except subprocess.CalledProcessError:
        print(f"    ! @{meta['assignee']} нельзя назначить — создаю без исполнителя", file=sys.stderr)
        url = run(base, capture=True)
    os.unlink(body_file)
    if meta["status"] == "done":
        run(["gh", "issue", "close", url.strip() or "<url>", "--repo", repo, "--reason", "completed",
             "--comment", "Сделано до переноса задач в GitHub (см. историю коммитов)."])

print("\nГотово." if apply else "\nСухой прогон: ничего не изменено. Для применения добавьте --apply.")
print("Доску GitHub Projects создайте вручную или: gh project create --owner <OWNER> --title 'FitQuest' "
      "(нужен scope: gh auth refresh -s project), затем добавьте задачи через gh project item-add.")
PY

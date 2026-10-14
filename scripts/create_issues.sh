#!/usr/bin/env bash
# Создаёт GitHub Issues из docs/planning/issues/subject-1/*.md: метки, вехи (спринты), задачи,
# и при --project добавляет их на доску GitHub Projects со статусом и оценкой.
#
#   scripts/create_issues.sh                  # сухой прогон: только печатает, что будет сделано
#   scripts/create_issues.sh --apply          # создать в репозитории текущего каталога
#   scripts/create_issues.sh --apply --repo SonyAkb/FitnessApp --project SonyAkb/1
#
# Нужны: gh (gh auth login; для --project ещё gh auth refresh -s project) и python3.
# Заголовок задачи = ID + title, повторный запуск не создаёт дублей (и досинхронизирует доску).
# Задачи со status: done создаются и сразу закрываются, in-progress получают метку status:in-progress.
# Если исполнитель не участник репозитория, задача создаётся без исполнителя (с предупреждением);
# исполнитель в любом случае указан в шапке задачи.
# На доске: Status = Done / In progress / Ready (спринт уже идёт) / Backlog, Estimate = story points.
set -euo pipefail

APPLY=0
REPO=""
PROJECT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --repo) REPO="$2"; shift ;;
    --project) PROJECT="$2"; shift ;;
    *) echo "Неизвестный аргумент: $1" >&2; exit 2 ;;
  esac
  shift
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR="$ROOT/docs/planning/issues/subject-1"
[ -d "$DIR" ] || { echo "Нет каталога $DIR" >&2; exit 1; }
command -v python3 >/dev/null || { echo "Нужен python3" >&2; exit 1; }
if [ "$APPLY" = 1 ]; then
  command -v gh >/dev/null || { echo "Нужен GitHub CLI: https://cli.github.com" >&2; exit 1; }
  gh auth status >/dev/null || { echo "Выполните gh auth login" >&2; exit 1; }
fi
if [ -z "$REPO" ] && [ "$APPLY" = 1 ]; then
  REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
fi

APPLY="$APPLY" REPO="$REPO" PROJECT="$PROJECT" DIR="$DIR" python3 - <<'PY'
import datetime, json, os, re, subprocess, sys, tempfile

apply = os.environ["APPLY"] == "1"
repo = os.environ["REPO"] or "OWNER/REPO"
project = os.environ["PROJECT"]
src = os.environ["DIR"]
ISSUES_DIR = "docs/planning/issues/subject-1"

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
    body = re.sub(r"\[([A-Z]+-\d+)\]\([A-Z]+-\d+\.md\)", r"\1", body)
    meta["gh_title"] = f"{meta['id']} {meta['title']}"
    header = f"**ID:** {meta['id']} · **Story points:** {meta['story_points']} · **Источник:** `{ISSUES_DIR}/{meta['id']}.md`\n\n"
    return meta, header + body.lstrip()


def board_status(meta):
    if meta["status"] == "done":
        return "Done"
    if meta["status"] == "in-progress":
        return "In progress"
    today = datetime.date.today().isoformat()
    current = next((n for n, due in sorted(SPRINT_DUE.items()) if due >= today), max(SPRINT_DUE))
    return "Ready" if int(meta["milestone"].split()[-1]) <= current else "Backlog"


tasks = [parse(os.path.join(src, f)) for f in sorted(os.listdir(src)) if f.endswith(".md")]
print(f"{len(tasks)} задач, репозиторий {repo}, режим {'ПРИМЕНЕНИЕ' if apply else 'сухой прогон'}")

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

urls = {}
if apply:
    out = run(["gh", "issue", "list", "--repo", repo, "--state", "all", "--limit", "1000", "--json", "title,url"], capture=True)
    urls = {i["title"]: i["url"] for i in json.loads(out)}

print(f"\nЗадачи ({len(tasks)}):")
for meta, body in tasks:
    if meta["gh_title"] in urls:
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
    urls[meta["gh_title"]] = url.strip() or "<url>"
    if meta["status"] == "done":
        run(["gh", "issue", "close", urls[meta["gh_title"]], "--repo", repo, "--reason", "completed",
             "--comment", "Сделано до переноса задач в GitHub (см. историю коммитов)."])

if project:
    owner, number = project.split("/")
    print(f"\nДоска {owner}/projects/{number}:")
    fields, project_id = {}, "<project-id>"
    if apply:
        project_id = json.loads(run(["gh", "project", "view", number, "--owner", owner, "--format", "json"], capture=True))["id"]
        out = run(["gh", "project", "field-list", number, "--owner", owner, "--format", "json"], capture=True)
        fields = {f["name"]: f for f in json.loads(out)["fields"]}
    status_field = fields.get("Status", {"id": "<status>", "options": []})
    options = {o["name"]: o["id"] for o in status_field.get("options", [])}
    estimate = fields.get("Estimate", {"id": "<estimate>"})
    for meta, _ in tasks:
        status = board_status(meta)
        print(f"  > {meta['id']} → {status}, Estimate {meta['story_points']}")
        out = run(["gh", "project", "item-add", number, "--owner", owner, "--url", urls.get(meta["gh_title"], "<url>"),
                   "--format", "json"], capture=True)
        item = json.loads(out)["id"] if out else "<item>"
        if apply and status not in options:
            print(f"    ! на доске нет статуса «{status}», пропуск", file=sys.stderr)
        else:
            run(["gh", "project", "item-edit", "--id", item, "--project-id", project_id,
                 "--field-id", status_field["id"], "--single-select-option-id", options.get(status, f"<{status}>")])
        if not apply or "Estimate" in fields:
            run(["gh", "project", "item-edit", "--id", item, "--project-id", project_id,
                 "--field-id", estimate["id"], "--number", str(meta["story_points"])])

print("\nГотово." if apply else "\nСухой прогон: ничего не изменено. Для применения добавьте --apply.")
if not project:
    print("Чтобы добавить задачи на доску GitHub Projects, передайте --project OWNER/NUMBER "
          "(нужен scope: gh auth refresh -s project).")
PY

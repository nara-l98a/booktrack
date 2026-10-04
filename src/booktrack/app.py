"""Booktrack: a persistent reading tracker with validation and atomic writes."""
from __future__ import annotations
import argparse, json, os, tempfile
from datetime import date
from pathlib import Path

STATUSES = ("想读", "在读", "已读", "搁置")

def data_path(value=None):
    return Path(value or os.environ.get("BOOKTRACK_DATA", "~/.booktrack.json")).expanduser()

def load(path: Path) -> dict:
    if not path.exists(): return {"version": 1, "books": []}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(obj, dict) or not isinstance(obj.get("books"), list): raise ValueError
        return obj
    except (OSError, json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"数据文件无效或无法读取：{path} ({e})")

def save(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def positive_int(v, label):
    try: n = int(v)
    except ValueError: raise argparse.ArgumentTypeError(f"{label}必须是正整数")
    if n <= 0: raise argparse.ArgumentTypeError(f"{label}必须是正整数")
    return n

def rating(v):
    try: n = int(v)
    except ValueError: raise argparse.ArgumentTypeError("评分必须是 1-5 的整数")
    if not 1 <= n <= 5: raise argparse.ArgumentTypeError("评分必须是 1-5 的整数")
    return n

def find_book(obj, bid):
    for b in obj["books"]:
        if b["id"] == bid: return b
    raise ValueError(f"找不到书籍 ID：{bid}")

def next_id(obj): return max((b["id"] for b in obj["books"]), default=0) + 1

def progress(b): return b["current_page"] / b["pages"] * 100

def cmd_add(a, obj):
    title=a.title.strip(); author=a.author.strip()
    if not title or not author: raise ValueError("书名和作者不能为空")
    b={"id":next_id(obj),"title":title,"author":author,"pages":a.pages,"current_page":0,"status":a.status,"rating":a.rating,"notes":a.note or "","added":date.today().isoformat()}
    obj["books"].append(b); return f"已添加 #{b['id']}《{b['title']}》"

def cmd_list(a, obj):
    books=[b for b in obj["books"] if not a.status or b["status"]==a.status]
    if not books: return "暂无符合条件的书籍。"
    lines=["ID  状态  进度    评分  书名 — 作者"]
    for b in books: lines.append(f"{b['id']:<3} {b['status']:<4} {b['current_page']}/{b['pages']} ({progress(b):5.1f}%)  {(str(b['rating'])+'星') if b['rating'] else '未评'}  {b['title']} — {b['author']}")
    return "\n".join(lines)

def cmd_update(a, obj):
    b=find_book(obj,a.id)
    if a.page is not None:
        if a.page > b["pages"]: raise ValueError("当前页不能超过总页数")
        b["current_page"]=a.page
        if a.page == b["pages"] and a.status is None: b["status"]="已读"
    if a.status: b["status"]=a.status
    if a.rating is not None: b["rating"]=a.rating
    if a.note is not None: b["notes"]=a.note
    return f"已更新 #{b['id']}《{b['title']}》，进度 {b['current_page']}/{b['pages']} ({progress(b):.1f}%)"

def cmd_stats(obj):
    bs=obj["books"]; total=sum(b["pages"] for b in bs); read=sum(b["current_page"] for b in bs)
    lines=[f"藏书 {len(bs)} 本 | 总页数 {total} | 已读页数 {read}", "状态分布：" + ("、".join(f"{s} {sum(b['status']==s for b in bs)}" for s in STATUSES) or "无")]
    rated=[b["rating"] for b in bs if b["rating"]]; lines.append(f"平均评分：{sum(rated)/len(rated):.1f}/5" if rated else "平均评分：暂无")
    return "\n".join(lines)

def parser():
    p=argparse.ArgumentParser(prog="booktrack", description="记录书单、阅读进度、评分与笔记")
    p.add_argument("--data", help="JSON 数据文件（也可用 BOOKTRACK_DATA）")
    sub=p.add_subparsers(dest="command", required=True)
    x=sub.add_parser("add", help="添加书籍"); x.add_argument("title"); x.add_argument("author"); x.add_argument("--pages", required=True, type=lambda v:positive_int(v,"页数")); x.add_argument("--status", choices=STATUSES, default="想读"); x.add_argument("--rating", type=rating); x.add_argument("--note")
    x=sub.add_parser("list", help="列出书籍"); x.add_argument("--status", choices=STATUSES)
    x=sub.add_parser("update", help="更新进度或书籍信息"); x.add_argument("id", type=lambda v:positive_int(v,"ID")); x.add_argument("--page", type=lambda v:int(v)); x.add_argument("--status", choices=STATUSES); x.add_argument("--rating", type=rating); x.add_argument("--note");
    x=sub.add_parser("stats", help="显示统计");
    x=sub.add_parser("sample", help="写入无个人数据的示例书单");
    return p

def main(argv=None):
    p=parser(); a=p.parse_args(argv); path=data_path(a.data)
    try:
        obj=load(path)
        if a.command=="add": out=cmd_add(a,obj); save(path,obj)
        elif a.command=="list": out=cmd_list(a,obj)
        elif a.command=="update":
            if a.page is None and a.status is None and a.rating is None and a.note is None: raise ValueError("至少提供一个更新项")
            if a.page is not None and a.page < 0: raise ValueError("当前页不能为负数")
            out=cmd_update(a,obj); save(path,obj)
        elif a.command=="stats": out=cmd_stats(obj)
        else:
            if path.exists(): raise ValueError(f"拒绝覆盖已有数据文件：{path}；如需重新初始化请另选一个 --data 路径")
            obj={"version":1,"books":[{"id":1,"title":"百年孤独","author":"加西亚·马尔克斯","pages":360,"current_page":72,"status":"在读","rating":None,"notes":"关注家族时间循环的叙事结构。","added":"2024-01-01"},{"id":2,"title":"小王子","author":"安托万·德·圣埃克苏佩里","pages":96,"current_page":96,"status":"已读","rating":5,"notes":"","added":"2024-01-02"}]}; save(path,obj); out=f"已写入示例数据：{path}"
        print(out); return 0
    except (ValueError, OSError) as e: p.error(str(e))

if __name__ == "__main__": main()

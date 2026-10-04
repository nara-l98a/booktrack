# Booktrack：中文阅读管理 CLI

Booktrack 是一个**专注阅读过程**的本地命令行工具：记录书名、作者、页数、阅读状态、评分和笔记，更新当前页时自动计算百分比；读完最后一页会自动变为“已读”。数据只写入你指定的 JSON 文件。

## 功能边界

支持书籍增添、进度/状态/评分/笔记更新、按状态过滤、阅读进度显示与汇总统计、无个人信息的样例数据。不支持云同步、账号、多人协作、电子书导入、提醒或全文检索；页数是正整数，评分为 1–5 星，状态仅为“想读/在读/已读/搁置”。

## 要求与安装

需要 Python **3.10 或更高版本**，运行时仅使用标准库。正常安装：

```bash
python -m pip install .
booktrack --help
# 或 python -m booktrack --help
```

开发时可用 `python -m pip install -e .` 安装可编辑版本。

每条命令都支持全局 `--data PATH`；也可设置 `BOOKTRACK_DATA`。未指定时使用 `~/.booktrack.json`。建议测试时使用临时文件。

## 完整 CLI 示例

```bash
# 仅当文件不存在时创建样例数据，不会覆盖旧文件。
booktrack --data ./reading-demo.json sample
booktrack --data ./reading-demo.json list
booktrack --data ./reading-demo.json list --status 在读
booktrack --data ./reading-demo.json add "沙丘" "弗兰克·赫伯特" --pages 688 --status 在读 --rating 5 --note "观察世界观中的生态主题"
booktrack --data ./reading-demo.json update 3 --page 120
booktrack --data ./reading-demo.json update 3 --status 搁置 --note "等待假期继续"
booktrack --data ./reading-demo.json update 3 --rating 4
booktrack --data ./reading-demo.json stats
```

示例输出：

```text
ID  状态  进度    评分  书名 — 作者
1   在读   72/360 ( 20.0%)  未评  百年孤独 — 加西亚·马尔克斯
2   已读   96/96 (100.0%)  5星  小王子 — 安托万·德·圣埃克苏佩里
```

## 命令与参数

- `add TITLE AUTHOR --pages N [--status 状态] [--rating 1..5] [--note 文本]`：添加书籍；页数必须为正整数；书名和作者不能留空。
- `list [--status 状态]`：列出全部或指定状态。
- `update ID [--page N] [--status 状态] [--rating 1..5] [--note 文本]`：至少提供一个更新项；页数不能为负数或超过总页数。进度达到总页数时自动标记“已读”，显式状态参数优先。
- `stats`：显示藏书数、总页数、已读页数、状态分布和平均评分。
- `sample`：仅当目标文件不存在时写入两本示例书籍；若文件已存在则拒绝覆盖。想重新开始时，请指定一个新的 `--data` 路径。
- 全部命令均可加 `--data PATH`（须放在子命令前），或使用 `BOOKTRACK_DATA`。

参数错误会以清晰错误退出，不会写入无效进度。读取已有数据时也会校验每条记录的字段、页数范围、状态、评分和唯一 ID；发现手工编辑造成的损坏数据会在执行命令前拒绝读取，避免静默产生错误统计。中文文本按 UTF-8 读写。

## 数据格式、隐私与安全限制

JSON 顶层为 `{"version": 1, "books": [...]}`；每本书含 `id`、`title`、`author`、`pages`、`current_page`、`status`、`rating`、`notes`、`added`。示例文件 `examples/sample.json` 不含个人数据。这是明文本地文件，可能包含你的阅读笔记；请自行设置文件权限，不要提交真实数据到版本库。程序不联网、不收集遥测、不含凭据或 Token。写盘先写同目录临时文件、刷新并 `fsync` 后原子替换；突然断电等极端情况下仍不保证文件系统或磁盘恢复。

## 开发与测试

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

测试均使用 `tempfile`，不会触碰真实用户数据。GitHub Actions 在 Python 3.10–3.12 上运行同一测试命令。

## 许可证

MIT，详见 [LICENSE](LICENSE)。

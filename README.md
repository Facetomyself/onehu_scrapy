# onehu_scrapy

使用原生 Scrapy 项目结构抓取 `onehu.xyz` 归档页中的所有文章详情，并支持状态保存与增量更新。

## 功能

- 全量抓取：从 `https://onehu.xyz/archives/` 开始翻页直到末页，抓取所有文章详情页
- 断点续跑：启用 Scrapy `JOBDIR`，中断后可继续跑，不必从头开始
- 增量更新：使用 SQLite 记录已抓取的详情页 URL；当曾经完成过一次“全量归档遍历”后，后续运行会从第 1 页开始，只要某一页没有出现新链接就停止继续翻页
- 输出：新增文章追加写入 `data/articles.jsonl`（JSON Lines）

## 环境要求

- Windows 11（默认）
- Python 3.12+（建议使用虚拟环境）
- 依赖：Scrapy

## 安装依赖

如果你已经在当前环境安装了 Scrapy，可跳过此步骤。

PowerShell 示例（pip）：

```powershell
python -m pip install -U pip
python -m pip install scrapy
```

如果你使用 `uv` 管理依赖：

```powershell
uv sync
```

## 运行

全量/增量抓取（同一条命令，逻辑由状态自动决定）：

```powershell
python -m scrapy crawl onehu
```

常用：调试时只抓少量条目（快速验证选择器）：

```powershell
python -m scrapy crawl onehu -s CLOSESPIDER_ITEMCOUNT=5 -s LOG_LEVEL=INFO
```

## 输出与状态文件

- 抓取结果（新增文章，JSON Lines 追加写入）
  - `data/articles.jsonl`
- 增量/去重状态（SQLite）
  - `state/onehu_state.sqlite3`
  - `articles` 表：已抓取的详情页 URL 以及文章基础元信息
  - `meta.full_crawl_completed=1`：表示已经完整遍历过归档页，后续运行可安全早停（增量）
- 断点续跑状态（Scrapy 内置）
  - `state/jobdir`

## 兼容性与常见报错

如果你升级了 Scrapy 并使用旧的 `JOBDIR`，可能会出现如下类似错误：

```
DownloaderAwarePriorityQueue accepts ``slot_startprios`` as a dict; <class 'list'> instance is passed.
```

解决方式二选一：

1) 删除旧的 `state/jobdir`（会丢失断点续跑队列，但不会影响 SQLite 的增量状态）  
2) 保持使用旧队列（本项目已在设置中固定 `SCHEDULER_PRIORITY_QUEUE` 为 `scrapy.pqueues.ScrapyPriorityQueue`）

## 增量更新策略说明

本项目的增量逻辑基于“归档页按时间倒序排列，新文章会出现在前几页”的假设：

- 第一次运行：会持续翻页直到末页，并在到达末页后写入 `full_crawl_completed=1`
- 后续运行：从第 1 页开始抓取
  - 如果某一页没有出现任何“未抓取过”的详情页链接，则认为后续页也不会再有新文章，停止继续翻页

注意：如果站点在较旧的页码插入新文章（非常规情况），该策略可能无法发现，需要手动清理状态并重新全量跑一次。

## 数据字段（items）

每条文章输出为一行 JSON，包含以下字段（见 `onehu_scrapy/items.py`）：

- `url`: 文章详情页 URL
- `title`: 文章标题（来自 `meta[property="og:title"]`）
- `tag`: 文章标签（来自 `meta[property="article:tag"]`）
- `published_time`: 发布时间（来自 `meta[property="article:published_time"]`）
- `modified_time`: 修改时间（来自 `meta[property="article:modified_time"]`）
- `content_html`: 详情页正文 HTML（`article.post-content .markdown-body`）
- `content_text`: 详情页正文纯文本（由正文区域提取并清洗）
- `scraped_at`: 抓取时间（UTC ISO8601）

## 选择器来源

选择器基于仓库内样例页面验证：

- 归档页样例：`analysis/index1.html`、`analysis/index2.html`
  - 文章链接：`div.list-group a.list-group-item::attr(href)`
  - 下一页：`#pagination a.extend.next::attr(href)`
- 详情页样例：`analysis/detail.html`
  - 标题：`meta[property="og:title"]::attr(content)`
  - 正文：`article.post-content .markdown-body`
  

## 重置（从零开始）

以下命令会删除抓取状态与输出文件，重新全量抓取前请确认：

```powershell
Remove-Item -Recurse -Force state, data
python -m scrapy crawl onehu
```

## 免责声明

请在合法合规且获得授权的前提下使用本项目，并遵守目标站点的服务条款与相关法律法规。该仓库仅演示 Scrapy 的工程化抓取与增量策略实现。

# pdf_check

两本教材的只读 Section / Exercise 精确定位 CLI。索引 JSON 来自 [Computer-Vision---Algorithms-2nd_gpt-action](https://github.com/qqq694637644/Computer-Vision---Algorithms-2nd_gpt-action)，不包含教材 PDF。ChatGPT Project 可直接持有、读取并渲染原始 PDF；本工具只返回定位与引用计划。

## 教材

- `cvaa2e` — Richard Szeliski, *Computer Vision: Algorithms and Applications*, Second Edition（938 PDF 页）。
- `dip4e` — Gonzalez & Woods, *Digital Image Processing*, Fourth Edition, Global Edition（1022 PDF 页）。

`pdf_check/catalog/{book_id}/` 内保存完整的编译主索引和对应的 JSON 分片。数据按原样复制，包含原始的 `data_version`、页码、`retrieval_plan`、`content_window` 和 `required_evidence`。

## Python 3.13 全局安装

```powershell
py -3.13 -m pip install git+https://github.com/qqq694637644/pdf_check.git
```

从任意工作目录执行：

```powershell
book-locator --book cvaa2e section 2.1.1
book-locator --book cvaa2e exercise 2.1
book-locator --book cvaa2e list 2
book-locator --book dip4e section 2.6.5
book-locator --book dip4e exercise 2.14
book-locator --book dip4e list 2
```

一个命令只输出一份完整 JSON，供 MCP PowerShell 工具或教学提示词使用。`section` 返回 Section 记录；`exercise` 返回题目及引用检索计划；`list` 返回指定章节的正式习题 ID 清单。查询不到时返回 JSON 错误及非零退出码，不猜测相近 ID。

### 指定其他 Catalog 路径（可选）

默认从安装包内的 `pdf_check/catalog/` 读取，因此不用另外配置绝对路径。如需替换为服务器已有索引，可以传参数：

```powershell
book-locator --book cvaa2e --catalog-root 'D:\teacher\catalog' section 2.1.1
```

或者通过 PowerShell 环境变量统一设置：

```powershell
$env:PDF_CHECK_CATALOG_ROOT = 'D:\teacher\catalog'
book-locator --book dip4e exercise 2.14
```

`--catalog-root` 应指向直接包含 `cvaa2e/`、`dip4e/` 两个子目录的位置。

## 与 ChatGPT Project 配合

通过 MCP 的通用 `pwsh` 工具运行 `book-locator`，读取返回的物理页索引和核验计划，再由 ChatGPT Project 中已上传的原始 PDF 完成正文、公式、表格和页面视觉核验。本 CLI 不托管、转发或修改 PDF，也不要求新增专用 MCP 定位工具。

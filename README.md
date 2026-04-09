# PDF Bookmark Transfer

这个小工具用于解决一个很常见但很烦的 Word 导出 PDF 问题：

- `typeA.pdf`：图片很清晰，但是 PDF 侧边栏没有自动生成的目录
- `typeB.pdf`：PDF 侧边栏有目录，但是图片清晰度不够

目标是生成一个新的 PDF：

- 页面内容使用 `typeA.pdf`
- 侧边目录使用 `typeB.pdf`

也就是说，本项目做的事情本质上是：

> 把 `typeB` 的 PDF 目录信息，迁移到 `typeA` 上。

## 思路

这类问题最稳的处理方式不是“重新拼页面内容”，而是：

1. 保留 `typeA.pdf` 的全部页面内容
2. 读取 `typeB.pdf` 的 PDF outline / bookmarks
3. 按原有层级结构递归写入到新的 PDF
4. 输出一个新的融合版 PDF

这样做的好处是：

- 高清图片完全来自 `typeA`，不会被重新压缩
- PDF 目录直接来自 `typeB`，能保留章节层级
- 不需要重新渲染 PDF 页面，速度快，也更稳定

## 当前脚本

主脚本是：

- `merge_pdf_bookmarks.py`

它会做这些事情：

- 读取内容 PDF，也就是要保留页面内容的文件
- 读取目录 PDF，也就是要复制书签的文件
- 递归复制目录层级
- 保留目录项的展开/折叠状态
- 保留目录项的颜色、粗体、斜体信息
- 尽量保留目录点击后的页内跳转位置
- 默认让输出 PDF 打开时显示左侧目录栏
- 处理中文书签编码，避免标题乱码

## 适用前提

这个方案成立的关键前提是：

- `typeA` 和 `typeB` 的页数一致
- 两者的分页顺序一致
- 同一章节在两份 PDF 中对应的是同一页

如果这几个条件满足，那么目录可以直接迁移。

如果以后遇到下面这种情况，就不能直接搬：

- 两份 PDF 页数不同
- 某一份多了空白页
- 某一份分页位置变了
- 同一个章节在两份 PDF 里不在同一页

这种情况下就需要额外做“页码映射”，不能直接复制目录。

## 使用方法

基本命令：

```bash
python3 merge_pdf_bookmarks.py \
  --content typeA.pdf \
  --bookmarks typeB.pdf \
  --output merged.pdf
```

参数说明：

- `--content`：要保留页面内容的 PDF，通常就是高清版 `typeA`
- `--bookmarks`：要提取目录的 PDF，通常就是有侧边目录的 `typeB`
- `--output`：输出文件路径
- `--force`：如果输出文件已存在，则覆盖

如果不传 `--output`，默认会生成：

```text
<content文件名>_with_bookmarks.pdf
```

例如：

```bash
python3 merge_pdf_bookmarks.py --content typeA.pdf --bookmarks typeB.pdf
```

默认输出会是：

```text
typeA_with_bookmarks.pdf
```

## 本地测试结果

当前目录中的测试文件：

- `typeA.pdf`
- `typeB.pdf`

已经验证生成成功：

- `merged_typeA_with_bookmarks.pdf`

测试结论：

- 输出文件页数保持为 82 页
- 成功复制了 76 个目录项
- 输出 PDF 默认会显示侧边目录
- 页面内容体积与 `typeA.pdf` 基本一致，说明高清内容被保留下来了

## 依赖

脚本使用 Python 3 和 `pypdf`。

如果本机没有 `pypdf`，可以安装：

```bash
pip install pypdf
```

## 注意事项

- 输出文件不能和输入文件同名，脚本已经做了保护
- 如果源 PDF 本身没有目录，脚本会报错退出
- 如果目录 PDF 指向的页码超出内容 PDF 的页数范围，脚本会报错退出
- 如果两份 PDF 页面尺寸略有差异，脚本会按比例修正目录点击后的页内定位

## 适合的使用场景

这个工具很适合下面这种流程：

1. Word 导出一个高清但没有目录的 PDF
2. 再导出一个有目录但清晰度差一些的 PDF
3. 用本脚本把目录从第二份迁到第一份

最后得到一个既有高清图片、又有 PDF 目录的成品文件。

---
name: add-pack-version
description: 给本仓库加一个新的 All the Mods 10: To the Sky 整合包版本（例如 2.0.7）：声明构建目标、取 CI 生成的基线入库、处理 CI 报红、补译新版带进来的文本、写文档，全部放在一个「适配 <版本>」的 PR 里。用于 ATM10 Sky 发了新版、要让汉化包支持它的时候。
---

# 新版本入库

ATM10 Sky 发了新版，要让汉化包支持它。整个适配放在**一个分支、一个 PR** 里，标题写 `feat: 适配整合包 <版本>`。不按模组拆成多个 PR。审查提出的新问题另开 PR，不塞进这一个。

先读 `AGENTS.md`，尤其是「覆盖率与缺口的口径」和「Git 与 PR」。

## 第零步：确认这一版已经发布

以 CurseForge 上的文件为准，不看 GitHub 的 changelog。

```bash
python3 scripts/fetch_pack.py <版本> build/packsrc/<版本> --no-jars
```

版本还没发布时，它会报「CurseForge 上找不到」，并列出最近 50 个文件里已有的版本号。

上游的 `displayName` 混着两种写法：`ATM10SKY-2.0.6` 不带后缀，`ATM10SKY-2.0.7.zip` 带后缀。`find_file_id` 比对前要去掉 `.zip`（`display_ver`），否则带后缀的那些版本会被判成「不存在」。报「找不到」时先看它列出的版本号里有没有带 `.zip` 的同号。

## 第一步：声明构建目标

每样东西一个提交：

1. `versions/<版本>/.gitkeep`：空文件。CI 看到这个目录，才会把这一版当作构建目标。
2. `versions/<版本>/neoforge.txt`：manifest 里的 NeoForge 版本号，例如 `21.1.250`。
3. `versions/<版本>/default_resource_packs.txt`：这一版首次启动后，游戏写进 `options.txt` 的 `resourcePacks` 顺序，不含汉化包。这个值要在装好的这一版整合包里实测，CI 拿不到。没实测到就留空并写明原因，安装器那时不伪造这一行。

## 第二步：取 CI 生成的基线入库

推送后，`build` 会故意报红。它会上传 artifact `new-version-baseline-<版本>`，里面有：

- `versions/<版本>/overrides.sha256`：官方 overrides 的内容指纹
- `versions/db/<版本>/`：`jars.json`、`keybinds.json`、`quest_baseline.json`、`vaultpatcher.json`、`lang_baseline_local.json`

前四个核对后提交。`lang_baseline_local.json` 由 `.gitignore` 排除，不入库。基线只取 CI 的产物，不在本机生成。

之后按 CI 的报错逐项处理。常见的有：

| CI 报错 | 怎么处理 |
|---|---|
| 缺 `versions/db/<版本>/productive_trees.json` | 下一轮 CI 会上传 artifact `productive-trees-baseline`，核对后提交。它同时重扫在册的旧版本，与已入库的那几份应逐字节相同 |
| 上游改写映射在这一版套不上 | 这一版确实没有这段原文：在 `versions/<版本>/unpatchable.json` 登记，写明 `why`。原文改了样子、仍要译：写 `versions/<版本>/upstream/<路径>.json` |
| 找不到 `versions/<版本>/quest_untranslated.json` | 任务书底本里有意不译的键要逐条登记，见第三步 |
| 缺 `versions/<版本>/generated_baseline.txt` | 包已经打出来了，只差该版基线，见第六步 |
| manifest 里有 jar 下不来（`/download` 返回 404） | 写进 `versions/<版本>/unobtainable.json`，`_why` 写明 fileID、projectID、缺的是哪部分 |

闸红了是包不达标。改内容，不改闸。

## 第三步：两份登记表按本版实测重写

两份都不许照抄上一版的数字，判据要在本版的官方包里重新算。官方包里的 `overrides/` 才是判据，跑起来过一次的实例不行：FTB Quests 归一化 `chapters` 时会把 image 块的 hover 字段全部丢掉。

- `unpatchable.json`：八章 hover 的登记。统计本版每章的 image 块数与 hover 字段数写进 `why`。hover 全局为 0 时，这些映射在本版没有落点，`which` 写 `"all"`。
- `quest_untranslated.json`：五组键（孤儿章节、孤儿章节组、整合包名、上游空串、护甲点数）逐组重验：孤儿类在本版的任务书非 lang 文件里仍 0 处引用、空串组仍是空串、护甲点数组仍是纯数字加 `+`。验过才复制。

登记两头都是 fail-closed：登记了但原文其实还在会红，没登记又找不到也会红。

## 第四步：版本层沿用上一版

逐项对照上一版的 `versions/<上一版>/`，判断哪些在新版仍然适用。

`pack_overrides.json` 的判据是**行为变了，不是英文变了**：

- 参数个数变了（一份中文没法同时对两版成立）、描述的行为变了（旧译文发到新版会说错），这两类才分叉。
- 只是措辞细化的，公共层按新版原文写，不分叉。
- 每条写明 `why`：哪个 jar、与哪一版逐字节相同、改了什么。
- 公共层按**最新版**写，旧版用覆盖保留对它才正确的那份。两个旧版的原文逐字节相同时，同一份覆盖要分别写进各自的 `pack_overrides.json`。

## 第五步：找出新版带进来的文本

底本用这一版钉的 jar：

- 新版 jar：`versions/db/<版本>/jars.json` 入库后，用 `fetch_one_jar.py <版本> <文件名> <目录>` 取。装好的整合包确实是这一版时，才能直接读它的 `mods/`。
- 旧版 jar：`fetch_one_jar.py <上一版> <文件名> <目录>`。整合包已经原地升级、旧 jar 不在了，也照样取得到。

拿两版的 `jars.json` 比出新增、移除、升级的模组，然后按下表逐类查：

| 表面 | 怎么查 |
|---|---|
| 模组 lang | 按 `AGENTS.md`「覆盖率与缺口的口径」求差：新版 `en_us` 减旧版，再减模组自带 `zh_cn`、本包 `zh_cn`、整合包 `kubejs/assets`。`lang_baseline_local.json` 只收本包已译的键，不能当分母 |
| 按键显示名 | `key.<modid>.*` 这类键在 jar 的 `en_us` 里有、`zh_cn` 没有兜底时，按键设置里会显示英文。`versions/db/<版本>/keybinds.json` 只记注册名，不记显示名，所以这类缺口要去 jar 的 `en_us` 里找 |
| 任务书 | 跑 `python3 scripts/check_en_drift.py <上一版> <版本>`。本包的任务书是全量覆盖，所以零漂移时译文直接通用 |
| 任务书标题横幅 | 新章节的横幅在 `scripts/gen_quest_banners.py` 登记。文案写死在表里，与章节标题核验，改章节标题要同时改它 |
| 导览书 | 只补**完全没有中文**的新页。模组自带中文跟不上新英文时，不覆盖 |
| VaultPatcher | 升级了的 jar 由 CI 重新核对，按 `vaultpatcher-db` 的结果处理 |
| 可选的拼音搜索 JEC | 查有没有新版，以及新版是否还能注入升级后的 JEI、终端类模组 |

## 第六步：生成物基线

包打出来之后，CI 会报缺 `versions/<版本>/generated_baseline.txt`，同时打印两组实测行：`build_dist.sh` 开头的「生成物实测」，与 `verify_dist.py` 的「实测：」。

只抄这两行的数字，逐项注明 run 号与 commit。与上一版的差别在文件里写清来由，例如本版多出的键本包已有译文、任务书空格修正多了一块。数字掉了先查是不是删错了东西，不许为了变绿往下改。

## 第七步：文档

- `README.md`：兼容版本表加一行，开头那句与下载说明里的 `sky<版本>` 列表跟着改。
- `CHANGELOG.md`：按 [`write-changelog`](../write-changelog/SKILL.md) 写。

## 第八步：收尾

- `上游漂移 + 汉化校验` 与 `build` 两项检查都通过，六个包（三版各 client/server）全部通过内容核验。
- 下载 `build` 的 artifact，核对新加的横幅等生成物。
- PR 正文写清做了什么、还缺什么、依据在哪。squash 合并时，提交信息就取 PR 标题与正文。
- 不打 tag，不发 release。发版由维护者做。

## 不要做的

- 本机不跑 `generate_all.sh`。构建只在 CI 里验证。
- 不在本机生成基线，只提交 CI 的 artifact。
- 不拿旧版整合包当新版的底本，也不拿跑过一次的实例当官方文件。
- 没有 CI 给出的红，不动取包判据与任何闸。
- 版本还没发布时，不写依赖 `jars.json` 的东西。

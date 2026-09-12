#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# atm10sky-zh_cn — All the Mods 10 to the Sky 简体中文汉化补丁
# Copyright (C) 2026 星野夢華 (Hoshino Yumeka)
# SPDX-License-Identifier: GPL-3.0-or-later
"""把另一个整合包自带的中文任务书按任务 id 搬到本包，存进 src/config/。

## 为什么需要这一步

ATM10 Sky 的任务书**不带 zh_cn**；它以 All the Mods 10 为底，两边有大量任务 id 与英文原文
逐字节相同。那部分中文可以直接搬，不必重译。

本包的上游不带 zh_cn，所以这里搬进来的是**整份**中文任务书；但它仍然按 delta 的形态存放
（`zz_hanhua_<上游章节名>.snbt`，与上游章节名脱钩），和上一个仓库一样。
「上游没有 zh_cn 所以用不上 delta 层」这个推论是错的：整合包升版会拆章节、改章节名，
按上游原名存的源文件到那时无法同时满足两个在册版本，而跨版本是这套结构的根本能力。

## 唯一的硬规矩：英文原文必须逐字节一致

任务 id 相同**不等于**内容相同。FTB Quests 的 id 在整合包被改写时是会保留的，
作者改了描述、换了配方、把任务重新定义成别的东西，id 照样不动。此时把旧译文按 id
套上去，玩家读到的是一段**与眼前任务无关、但看起来很像**的中文——这比留着英文糟得多：
漏翻玩家自己会去查，错翻玩家会照着做。

所以搬运的判据不是 id，是「两边的英文原文逐字节相同」。对不上的一条都不搬，
全部写进复核清单等人处理。

## 解析器先自证

SNBT 的值可以跨多行（`quest_desc` 一段一行），切错一个字节就会把译文写坏，而且
坏在数据里、构建不会报。所以开工前先拿全部输入文件跑一遍「解析→回写必须与原文
逐字节相同」，有一个不同就整体中止。

## 中文取**出货树**，不取游戏目录

游戏目录里的 `lang/zh_cn.snbt` 是 `ftbquestslangsplitter` 在运行时合并出来的：它把
`chapters/` 下的文件用 `Files.list` 顺序（哈希序，没有比较器）逐个并进去，谁覆盖谁
不确定，而且合并时会把跨行数组重新序列化成单行。实测拿它和上一个仓库的出货树比，
8700 多个键里有 86 个值的形态不同、另有 29/14 个键的有无差异。

出货树是构建的确定性产出，按上游原文件名整份替换，没有这些问题。所以中文一律从
出货树取。上一个仓库不出货 en_us（`lang/` 下只有 zh_cn），所以英文那份只能从整合包
本身取——那是纯上游内容，我们从不改它。

## 文件名跟着目标整合包走

出货时按上游原文件名整份替换，所以这里的输出文件名必须与目标整合包的章节文件同名。
`ftbquestslangsplitter` 进过一次游戏后会把 `xxx.snbt` 改名成 `xxx.snbt_merged`，
两种后缀都要认，输出一律写成 `.snbt`。

用法:
    python3 scripts/import_quest_lang.py <中文出货树> <源整合包根> <目标整合包根>

    中文出货树   上一个仓库的构建产物里那棵 `config/ftbquests/quests/lang/zh_cn`
                 （CI 的 dev artifact 解开即可，别用游戏目录）
    源整合包根   上面那份中文对应的整合包，只用来读它的 en_us
    目标整合包根 本包对应的整合包（ATM10 Sky）
"""
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:                                          # noqa: BLE001
        pass

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'src' / 'config' / 'ftbquests' / 'quests' / 'lang' / 'zh_cn'
REVIEW = ROOT / 'build' / 'quest_lang_review.txt'

LANG_REL = 'config/ftbquests/quests/lang'
# 出货的是 delta，文件名必须与上游章节名**脱钩**：带前缀的才被 gen_quest_lang_patches.py
# 认成「本包的覆盖」，再按键打进上游那份同名章节文件里发出去。
# 直接按上游原名发整份会出两种事故：上游同名文件的键被整份盖掉（早先 2 个键的
# aether.snbt 盖掉了上游 167 个键）；以及上游哪天拆/改章节名，同一份源文件就无法
# 同时满足两个在册版本——而跨版本是这套结构的根本能力。判据见 src/rules/quests.json。
DELTA_PREFIX = 'zz_hanhua_'

# 只前导颜色码不同的那一类。本包给章节标题统一加了 &f，正文一个字没改——
# 这不是「原文改过」，拿中文照搬、把前导码换成本包的即可，结果与原文一一对应。
# 独立成一个阶段、单独计数：主判据（逐字节一致）一个字没松，这一条是它之外的
# 另一条**可证明安全**的判据，红线仍然是「正文有任何差异就不搬」。
LEAD = re.compile(r'^(?:&[0-9a-fk-or])*')


def recolor(en_src, en_dst, zh):
    """源、目标只差前导颜色码时，返回配上目标前导码的中文；否则 None。

    三样都是 SNBT 的原始切片，可能带引号。跨行数组不参与——那种情形里
    「只差颜色码」难以逐段证明，留给人看。
    """
    def unq(s):
        s = s.strip()
        return (s[1:-1], '"') if len(s) >= 2 and s[0] == '"' == s[-1] else (None, '')
    a, qa = unq(en_src)
    b, qb = unq(en_dst)
    z, qz = unq(zh)
    if a is None or b is None or z is None:
        return None
    pa, pb, pz = LEAD.match(a).group(), LEAD.match(b).group(), LEAD.match(z).group()
    if a[len(pa):] != b[len(pb):]:        # 正文有差异 → 不是这一类
        return None
    if pz != pa:                          # 中文的前导码与源英文对不上 → 说不清，不碰
        return None
    return '%s%s%s%s' % (qz, pb, z[len(pz):], qz)

# 键行：行首若干空白 + 标识符 + 冒号。值一直取到**下一个键**为止，所以跨行数组
# 不需要单独处理括号配平。
KEY = re.compile(r'^(\s*)([A-Za-z_][\w.\-]*)\s*:[ \t]*', re.M)
TAIL_BRACE = re.compile(r'\n[ \t]*\}\s*$')


def parse(text):
    """{键: 值的原始文本}。值按「到下一个键为止」切片；文件末尾那个收尾 } 要剔掉。"""
    ms = list(KEY.finditer(text))
    out = {}
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        val = text[m.end():end]
        if i + 1 == len(ms):
            val = TAIL_BRACE.sub('', val)
        out[m.group(2)] = val.rstrip()
    return out


def dump(pairs):
    """按上游格式回写：{ + Tab 缩进的键值 + }"""
    return '{\n' + ''.join('\t%s: %s\n' % kv for kv in pairs) + '}\n'


def selfcheck(files):
    """解析器自证：每个输入文件「解析→回写」必须与原文逐字节相同。

    只在比较前抹平**文件末尾**的空行：上游有的文件以 `}\\n\\n` 收尾，那一个字节不
    承载任何数据。值内部的空白不在豁免之列——任何一个值被切多或切少，差异都落在
    非末尾位置，照样会被抓住（实测 ATM10 的 mekanism 章节就是只差这一个字节）。
    """
    def norm(s):
        return s.rstrip('\n') + '\n'

    bad = []
    for f in files:
        t = f.read_text(encoding='utf-8', errors='replace')
        if norm(dump(list(parse(t).items()))) != norm(t):
            bad.append(f)
    if bad:
        sys.exit('❌ 解析器自检没过，以下文件回写与原文不一致，已中止（一个字节都不能错）：\n'
                 + '\n'.join('   %s' % f for f in bad[:10]))
    print('解析器自检：%d 个文件回写与原文逐字节相同' % len(files))


def lang_files(pack, lang):
    """某个整合包某种语言的任务书文件。

    **目录优先，且两者只取其一**：进过一次游戏之后，`ftbquestslangsplitter` 会在
    `lang/` 下留下合并后的 `en_us.snbt`，而拆开的 `en_us/` 目录也还在——两边内容重复。
    都算进来会把键数直接翻倍（实测 9255 变 18497），而且按章节写输出时会各写一份。

    取目录而不是取单文件，是因为出货要按上游章节文件名整份替换，单文件没有章节结构。
    """
    d = Path(pack) / LANG_REL
    if (d / lang).is_dir():
        sub = sorted((d / lang).rglob('*.snbt*'))
        if sub:
            return sub
    return [p for p in (d / (lang + '.snbt'), d / (lang + '.snbt_merged')) if p.is_file()]


def read_lang(pack, lang):
    """整份键值表。"""
    out = {}
    for f in lang_files(pack, lang):
        out.update(parse(f.read_text(encoding='utf-8', errors='replace')))
    return out


def main(zh_tree, src_pack, dst_pack):
    zh_files = sorted(Path(zh_tree).rglob('*.snbt*'))
    src_en_files = lang_files(src_pack, 'en_us')
    dst_en_files = lang_files(dst_pack, 'en_us')
    if not zh_files:
        sys.exit('❌ 中文出货树里没有 .snbt：%s\n'
                 '   要的是构建产物里那棵 config/ftbquests/quests/lang/zh_cn' % zh_tree)
    if not src_en_files:
        sys.exit('❌ 源整合包里没有 en_us 任务书：%s/%s\n'
                 '   没有它就无法判断原文是否一致，而只按 id 搬是不允许的'
                 % (src_pack, LANG_REL))
    if not dst_en_files:
        sys.exit('❌ 目标整合包里没有 en_us 任务书：%s/%s' % (dst_pack, LANG_REL))

    selfcheck(zh_files + src_en_files + dst_en_files)

    src_zh = {}
    for f in zh_files:
        src_zh.update(parse(f.read_text(encoding='utf-8', errors='replace')))
    src_en = read_lang(src_pack, 'en_us')

    print('中文出货树 %d 键（%d 个文件） / 源 en_us %d 键'
          % (len(src_zh), len(zh_files), len(src_en)))

    carried = 0
    recolored = 0
    drift = []
    absent = 0
    files = 0
    base_d = Path(dst_pack) / LANG_REL / 'en_us'
    for f in dst_en_files:
        dst_en = parse(f.read_text(encoding='utf-8', errors='replace'))
        pairs = []
        for k, en in dst_en.items():
            if k not in src_zh:
                absent += 1
                continue
            if src_en.get(k) != en:
                fixed = recolor(src_en.get(k) or '', en, src_zh[k])
                if fixed is None:
                    drift.append((f.name, k, src_en.get(k), en))
                    continue
                recolored += 1
                pairs.append((k, fixed))
                continue
            pairs.append((k, src_zh[k]))
        if not pairs:
            continue
        rel = f.relative_to(base_d) if base_d in f.parents or f.parent == base_d \
            else Path(f.name)
        name = rel.name.replace('.snbt_merged', '.snbt')
        if not name.startswith(DELTA_PREFIX):
            name = DELTA_PREFIX + name
        dst = OUT / rel.parent / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(dump(pairs), encoding='utf-8')
        carried += sum(1 for k, _ in pairs if src_en.get(k) == dst_en[k])
        files += 1

    total = carried + recolored + len(drift) + absent
    print()
    print('目标整合包 %d 个英文键：' % total)
    print('  ✅ 原文逐字节一致 → 已搬 : %5d  (%.1f%%)  写进 %d 个文件'
          % (carried, carried / total * 100, files))
    print('  ✅ 只差前导颜色码 → 已搬 : %5d  (%.1f%%)  中文配上本包的前导码'
          % (recolored, recolored / total * 100))
    print('  ⚠️  原文改过 → 没搬       : %5d  (%.1f%%)'
          % (len(drift), len(drift) / total * 100))
    print('  ⛔ 源里没有中文 → 没搬   : %5d  (%.1f%%)'
          % (absent, absent / total * 100))

    REVIEW.parent.mkdir(parents=True, exist_ok=True)
    REVIEW.write_text(''.join(
        '%s  %s\n  源: %s\n  本: %s\n\n' % (fn, k, (a or '')[:400], b[:400])
        for fn, k, a, b in drift), encoding='utf-8')
    print()
    print('原文改过的 %d 条已写进 %s，逐条人工处理——这批**不能**按 id 直接套旧译文。'
          % (len(drift), REVIEW.relative_to(ROOT)))


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__.strip().split('用法:')[-1].strip())
    main(sys.argv[1], sys.argv[2], sys.argv[3])

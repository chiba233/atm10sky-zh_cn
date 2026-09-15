#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# atm10sky-zh_cn — All the Mods 10 to the Sky 简体中文汉化补丁
# Copyright (C) 2026 星野夢華 (Hoshino Yumeka)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Iron Jetpacks 的等级名不在 lang 里，在整合包的 config 里——漏一个就静默显示英文。

## 为什么要这道闸

游戏里显示「Vibranium能量电池」「Creative喷气背包」。乍看像是漏翻了两条，
其实是 17 个等级**一条都没翻**——木/石/铁那几个也是英文，只是不扎眼。

物品名的模板在 lang 里（`item.ironjetpacks.cell` = `%s能量电池`），但 `%s`
不来自 lang，来自整合包 `config/ironjetpacks/jetpacks/*.json` 里的 `name`。
照 `Jetpack#getDisplayName` 的字节码：

    String key = String.format("jetpack.%s.name", name.replaceAll(" ", "_"));
    if (Language.getInstance().has(key)) return Component.translatable(key);
    return Component.literal(displayName);   // 兜底＝把 name 首字母大写

也就是说 mod **留了正规注入点**：只要 lang 里有 `jetpack.<name>.name` 就用它，
没有就悄悄回退成英文。回退是静默的——不报错、不留日志，跟「已经翻好了」
在任何自动检查里都长得一模一样。

而等级清单是**整合包给的、随版本变**：ATM 自己加了 allthemodium / vibranium /
unobtainium / creative 这几档。下个版本 ATM 再加一档，我们这边只会静默少一条。
所以这个清单不能手写死在仓库里，要拿目标版本的官方 config 现查。

整合包也可以**不带**这份 config：档位 json 是 mod 首次启动时按
`com/blakebr0/ironjetpacks/lib/ModJetpacks.class` 里写死的默认值生成的。
这时清单就从整合包自己那个 IronJetpacks jar 的这个类里读（`--mods`），同样不手写。

## fail-closed

上游树没取到、jetpacks 目录不在又没给 `--mods`、mods 里带 ModJetpacks 的 jar 不是恰好一个、
类里的字符串排不成「档位名 + 材料」对、目录里一个 json 都没有、json 解析不了、
缺 `name` 字段、出货树里没有 ironjetpacks 的 lang——全部当红。
「没扫到东西所以通过」是这道闸最没用的失败形态。

`"disable": true` 的档位 mod 根本不注册，不需要译名，跳过；
但 `disable` 字段本身读不出来时按**需要译名**处理（宁可多要一条）。

用法:
    python3 scripts/compliance/check_jetpack_tiers.py <上游树> <出货树>... [--mods <mods 目录>]
"""
import json
import re
import struct
import sys
import zipfile
from pathlib import Path

PACK_LANG = 'resourcepacks/ATM10Sky汉化包/assets/ironjetpacks/lang/zh_cn.json'
CONFIG_DIR = 'config/ironjetpacks/jetpacks'
DEFAULTS_CLASS = 'com/blakebr0/ironjetpacks/lib/ModJetpacks.class'
TIER_NAME = re.compile(r'[a-z][a-z0-9_]*')
# 材料写法：`tag:c:ingots/iron`、`minecraft:copper_ingot`，创造档是字面量 null
MATERIAL = re.compile(r'null|(tag:)?[a-z0-9_.-]+:[a-z0-9_/.-]+')


def die(msg):
    print('❌ %s' % msg)
    sys.exit(1)


def class_strings(data):
    """按常量池顺序取出 class 文件里 CONSTANT_String 的值。只读常量池，不解析方法体。"""
    if data[:4] != b'\xca\xfe\xba\xbe':
        raise ValueError('不是 class 文件')
    count = struct.unpack('>H', data[8:10])[0]
    i, pos, utf8, refs = 1, 10, {}, []
    while i < count:
        tag = data[pos]
        if tag == 1:
            n = struct.unpack('>H', data[pos + 1:pos + 3])[0]
            utf8[i] = data[pos + 3:pos + 3 + n].decode('utf-8', 'replace')
            pos += 3 + n
        elif tag == 8:
            refs.append(struct.unpack('>H', data[pos + 1:pos + 3])[0])
            pos += 3
        elif tag in (3, 4):
            pos += 5
        elif tag in (5, 6):          # long / double 占两个槽位
            pos += 9
            i += 1
        elif tag in (7, 16, 19, 20):
            pos += 3
        elif tag in (9, 10, 11, 12, 17, 18):
            pos += 5
        elif tag == 15:
            pos += 4
        else:
            raise ValueError('常量池里有认不出的 tag %d' % tag)
        i += 1
    return [utf8[r] for r in refs]


def read_default_tiers(mods):
    """整合包没带 config 时，从 IronJetpacks jar 的 ModJetpacks 里读默认档位。

    默认档位是一串 `new Jetpack(档位名, …, 材料, …)`，常量池里的字符串按「档位名、材料」
    成对排列。排不成对就红：上游改了这个类的写法，得有人来看，不许猜。
    """
    if not mods.is_dir():
        die('mods 目录不在：%s —— 读不了默认档位' % mods)
    found = []
    for j in sorted(mods.glob('*.jar')):
        try:
            with zipfile.ZipFile(j) as z:
                if DEFAULTS_CLASS in z.namelist():
                    found.append((j.name, z.read(DEFAULTS_CLASS)))
        except zipfile.BadZipFile:
            continue
    if len(found) != 1:
        die('%s 里带 %s 的 jar 有 %d 个（应恰好 1 个）：%s'
            % (mods, DEFAULTS_CLASS, len(found), [n for n, _ in found]))
    jar, data = found[0]
    try:
        strs = class_strings(data)
    except (ValueError, IndexError, KeyError, struct.error) as e:
        die('%s 里的 %s 读不出常量池：%s' % (jar, DEFAULTS_CLASS, e))
    if not strs or len(strs) % 2:
        die('%s 的 %s 里字符串常量有 %d 个，排不成「档位名 + 材料」对'
            % (jar, DEFAULTS_CLASS, len(strs)))
    tiers = {}
    for name, mat in zip(strs[0::2], strs[1::2]):
        if not TIER_NAME.fullmatch(name) or not MATERIAL.fullmatch(mat):
            die('%s 的 %s 里「%s」「%s」不像「档位名 + 材料」—— 上游改了写法，得有人来看'
                % (jar, DEFAULTS_CLASS, name, mat))
        tiers[name] = '%s 的默认档位' % jar
    print('   整合包没带 %s，档位取 %s 的默认值（%d 个）' % (CONFIG_DIR, jar, len(tiers)))
    return tiers


def read_tiers(uproot, mods=None):
    """读出这一版真实存在的等级名：整合包带了 config 就读 config，没带就读 jar 默认值。"""
    d = uproot / CONFIG_DIR
    if not d.is_dir():
        if mods is None:
            die('上游树里没有 %s，也没给 --mods —— 等级清单无从谈起（树: %s）'
                % (CONFIG_DIR, uproot))
        return read_default_tiers(Path(mods))
    jsons = sorted(d.glob('*.json'))
    if not jsons:
        die('%s 里一个 json 都没有 —— 取包取了个空目录，不算查过' % d)
    tiers = {}
    for p in jsons:
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
        except Exception as e:
            die('%s 解析失败：%s' % (p, e))
        name = data.get('name')
        if not isinstance(name, str) or not name.strip():
            die('%s 缺 name 字段 —— 判不了它需要哪个 lang 键' % p)
        # 只有明确写了 true 才当停用；读不出来一律按「要译名」处理。
        if data.get('disable') is True:
            continue
        tiers[name] = '%s/%s' % (CONFIG_DIR, p.name)
    if not tiers:
        die('%s 里的档位全被 disable —— 不可能，多半是读错了字段' % d)
    return tiers


def check_tree(tree, tiers):
    """出货树里每个等级都得有 jetpack.<name>.name。"""
    lang = tree / PACK_LANG
    if not lang.is_file():
        die('%s 不在 —— 资源包没摊出来，这道闸等于没跑' % lang)
    try:
        data = json.loads(lang.read_text(encoding='utf-8'))
    except Exception as e:
        die('%s 解析失败：%s' % (lang, e))

    missing, empty = [], []
    for name, src in sorted(tiers.items()):
        key = 'jetpack.%s.name' % name.replace(' ', '_')
        if key not in data:
            missing.append((key, src))
        elif not str(data[key]).strip():
            empty.append(key)

    if missing or empty:
        print('❌ %s：Iron Jetpacks 等级名会静默回退成英文' % tree)
        for key, src in missing:
            print('   缺 %-34s （来自 %s）' % (key, src))
        for key in empty:
            print('   空 %s' % key)
        print('   补进 src/pack/assets/ironjetpacks/lang/zh_cn.json 即可，'
              '译名跟对应材料的物品名保持一致')
        return False

    # 反向只报不拦：多余的键不会生效，但多半意味着上游删了档位。
    extra = sorted(k for k in data
                   if k.startswith('jetpack.') and k.endswith('.name')
                   and k[len('jetpack.'):-len('.name')].replace('_', ' ') not in tiers
                   and k[len('jetpack.'):-len('.name')] not in tiers)
    if extra:
        print('ℹ️ %s：这些等级键在本版档位清单里已经没有对应档位了：%s'
              % (tree, '、'.join(extra)))
    print('✅ %s：Iron Jetpacks %d 个等级名全部有译' % (tree, len(tiers)))
    return True


def main(argv):
    args, mods = list(argv[1:]), None
    if '--mods' in args:
        i = args.index('--mods')
        if i + 1 >= len(args):
            die('--mods 后面要跟 mods 目录')
        mods = args[i + 1]
        del args[i:i + 2]
    if len(args) < 2:
        die('用法: check_jetpack_tiers.py <上游树> <出货树>... [--mods <mods 目录>]')
    uproot = Path(args[0])
    tiers = read_tiers(uproot, mods)
    ok = True
    for t in args[1:]:
        ok = check_tree(Path(t), tiers) and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))

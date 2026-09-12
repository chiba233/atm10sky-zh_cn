---
navigation:
  parent: enderdrives_intro/enderdrives_intro-index.md
  title: 磁带盘物品存储元件
  icon: enderdrives:tape_disk
categories:
- tapedrives
item_ids:
- enderdrives:tape_disk
---

# 磁带盘驱动器

磁带机是与 AE2 兼容的强大存储元，专门用于处理 **NBT 较重的物品**，
例如工具、护甲、附魔装备，或任何拥有独特标签、通常会迅速占满传统 ME 驱动器类型空间的物品。

与典型的 AE2 驱动器不同，磁带盘已用字节数会根据所存物品实际的 **NBT 大小** 动态变化——让你能更细致地控制系统。磁带机**不会**告知 AE2 它是任何符合其过滤器物品的首选存储位置，请使用 ME 驱动器优先级。

<Row gap="10">
  <Column>
    <ItemImage id="enderdrives:tape_disk" />
  </Column>
  <Column>
    <ItemLink id="enderdrives:tape_disk" />
  </Column>
</Row>

---

## 工作原理

每个磁带盘只允许存储带有非标准 NBT 的物品、盔甲、工具或不可堆叠物品。

---

## 字节与类型限制

磁带盘同时具有 **类型上限** 和 **字节用量上限**：

- **类型上限** – 可存储的唯一物品种类数上限（例如附魔书、自定义护甲）。
- **字节上限** – 基于每件物品的 **NBT 数据大小**。带有大量标签的物品（如 Apotheosis 装备）由于 NBT 数量较多，会占用更多空间。

磁带盘专门设计为**偏向存储 NBT 数据较重的物品**，非常适合存放装备或一次性物品，而不会占用传统存储驱动器的空间。

---


## 何时使用磁带盘

在以下情况下，请使用磁带盘而不是传统磁盘：

- 你正在存储**不可堆叠物品**，例如护甲、工具或装备。
- 你需要为**NBT 很重的模组物品**腾出空间。
- 你想让特殊物品不要进入普通的 ME 驱动器。

当普通驱动器因占用巨型驱动器的类型限制空间而捉襟见肘时，磁带机就能大显身手。

---

## IO端口传输

磁带盘通过 IO端口 向其传入或从其传出数据时会自动限速。这是因为它可能会处理 NBT 很重的物品，
以避免一次性全部倾倒出来导致游戏卡死。

---

## 可以存储什么？

磁带盘专门用于存放**NBT 数据较重**、**不可堆叠**或**自定义过的**物品——并不适合一般的大宗存储。

---

### 可接受物品

| 物品                                | 示例                                  |
|-------------------------------------|------------------------------------------|
| <ItemImage id="minecraft:diamond_chestplate" /> | 带附魔的 **钻石胸甲** |
| <ItemImage id="minecraft:enchanted_book" />     | 带附魔的 **附魔书**   |
| <ItemImage id="minecraft:splash_potion" />      | 带效果的 **药水**                 |
| <ItemImage id="minecraft:netherite_pickaxe" />  | 有耐久的 **工具**                |

---

### 不接受

| 物品                              | 原因                         |
|-----------------------------------|--------------------------------|
| <ItemImage id="minecraft:cobblestone" /> | 无 NBT，可堆叠              |
| <ItemImage id="minecraft:wheat" />       | 无 NBT，可堆叠  |
| <ItemImage id="minecraft:oak_log" />     | 无 NBT，可堆叠             |
| <ItemImage id="minecraft:apple" />       | 无 NBT，可堆叠    |
| <ItemImage id="minecraft:iron_ingot" />  | 无 NBT，可堆叠    |

---
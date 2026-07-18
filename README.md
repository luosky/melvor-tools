# melvor-tools

Melvor Idle 辅助工具集。

## 依赖说明 (Dependencies)

本项目正常运行需要依赖 **kimi 的 web-bridge**：
- 脚本会自动检测并尝试启动 `kimi-webbridge` 后台服务（默认寻找路径为 `~/.kimi-webbridge/bin/kimi-webbridge`）。
- 运行时需要通过 webbridge 将 Session（默认为 `melvor-chrome`）绑定至 Melvor Idle 游戏标签页（游戏地址：`https://melvoridle.com/index_game.php`）。

## 包含工具

### 1. Melvor Idle 宝箱自动开启脚本 (`melvor_chest_bot.py`)
严格每次只开一个宝箱，根据要求自动进行 Reroll 直到满足特定条件才 Consent 接受。支持在线动态解析宝箱中文名为英文图片资源名称。

#### 用法
```bash
python melvor_chest_bot.py <宝箱名字> <目标1> [目标2] ...
```

#### 目标参数格式说明
- `奖品名字:最低数量`：必须获得匹配该名字的奖品，且单次开出数量大于该值（不含等于）。
- `奖品名字`：只要获得匹配该名字的奖品即可，数量不限。
- `_:最低数量`：不限制奖品名字，只要任意开出奖品的数量大于该值即可。

#### 示例
- **单目标数量限制**（只匹配物品和最低数量）：
  ```bash
  python melvor_chest_bot.py 深渊钓鱼宝箱 虚空之心:3
  ```
  *(注：当开出 3 个或更少虚空之心时会自动 Reroll，开出 4 个及以上才接受并保存)*

- **多目标与任意物品数量限制**：
  ```bash
  python melvor_chest_bot.py 灵火矿脉荚 灰烬:190 _:200
  ```
  *(注：该示例会 Reroll 直到开出“灰烬”且数量大于 190 个，**或者**开出任意物品且数量大于 200 个时才接受并停止)*

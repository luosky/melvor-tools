# melvor-tools

Melvor Idle 辅助工具集。

## 依赖说明 (Dependencies)

本项目正常运行需要依赖 **kimi 的 web-bridge**：
- 脚本会自动检测并尝试启动 `kimi-webbridge` 后台服务（默认寻找路径为 `~/.kimi-webbridge/bin/kimi-webbridge`）。
- 运行时需要通过 webbridge 将 Session（默认为 `melvor-chrome`）绑定至 Melvor Idle 游戏标签页（游戏地址：`https://melvoridle.com/index_game.php`）。

## 包含工具

### 1. Melvor Idle 宝箱自动开启脚本 (`melvor_chest_bot_v2.py`)
严格每次只开一个宝箱，根据要求自动进行 Reroll 直到满足特定条件才 Consent 接受。支持在线动态解析宝箱中文名为英文图片资源名称。

#### 用法
```bash
python melvor_chest_bot_v2.py <宝箱名字> <目标1> [目标2] ...
```

示例：
```bash
python melvor_chest_bot_v2.py 深渊钓鱼宝箱 虚空之心:3
```

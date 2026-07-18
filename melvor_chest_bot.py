#!/usr/bin/env python3
"""
Melvor Idle 宝箱自动开启脚本
严格每次只开一个宝箱，reroll直到满足条件才Consent
用法: python melvor_chest_bot.py <宝箱名字> <目标1> [目标2] [目标3] ...
目标格式: 奖品名字:最低数量 或 奖品名字（只要匹配名字）或 _:最低数量（只看数量）
示例: python melvor_chest_bot.py 深渊钓鱼宝箱 虚空之心:3
      python melvor_chest_bot.py 深渊钓鱼宝箱 虚空之心:3 灰烬:190
      python melvor_chest_bot.py 灵火矿脉荚 灰烬:190 _:200
"""

import subprocess
import json
import time
import sys
import os
from datetime import datetime

BASE_URL = "http://127.0.0.1:10086/command"
SESSION = "melvor-chrome"
LOG_FILE = "/Users/luosky/Documents/kimi/workspace/melvor_chest_log.txt"

# 中文宝箱名字到英文图片文件名的映射
CHEST_NAME_MAP = {
    "深渊钓鱼宝箱": "Abyssal_Fishing_Chest",
    "痛苦宝箱": "Woeful_Chest",
    "衰败宝箱": "Decaying_Chest",
    "背叛宝箱": "Treacherous_Chest",
    "静电宝箱": "static_chest",
    "诅咒宝箱": "cursed_chest",
    "上锁的迷宫宝箱": "Locked_Maze_Chest",
    "骨头宝箱": "bone_chest",
    "标准宝箱": "standard_chest",
    "魔法宝箱": "magic_chest",
    "蜘蛛宝箱": "spider_chest",
    "米奥石宝箱": "miolite_chest",
    "冰霜宝箱": "ice_chest",
    "魔像宝箱": "Golem_Chest",
    "宝藏宝箱": "treasure_chest",
    "精英宝箱": "elite_chest",
    "古代宝箱": "ancient_chest",
    "燃烧宝箱": "burning_chest",
    "失落宝箱": "Lost_Chest",
    "黄金宝箱": "golden_chest",
    "水之宝箱": "water_chest",
    "大地宝箱": "earth_chest",
    "火焰宝箱": "fire_chest",
    "罪恶树木宝箱": "Unholy_Trees_Chest",
    "仪式宝箱": "Ritual_Chest",
    "强盗宝箱": "bandit_chest",
    "欺诈宝箱": "Trickery_Chest",
}

def resolve_chest_img_name(chest_name):
    """根据中文名在网页（游戏内存）中查找对应的英文图片文件名"""
    if check_webbridge():
        resp = webbridge("evaluate", {
            "code": f"""(() => {{
                if (typeof game === 'undefined' || !game.items || !game.items.allObjects) return JSON.stringify(null);
                const item = game.items.allObjects.find(i => i.name === "{chest_name}");
                if (!item) return JSON.stringify(null);
                const mediaUrl = item.media || "";
                const match = mediaUrl.match(/\\/([^\\/]+)\\.(png|jpg|jpeg|gif|svg)$/i);
                return JSON.stringify(match ? match[1] : null);
            }})()"""
        })
        img_name = extract_response_value(resp)
        if img_name:
            log(f"通过网页在线解析找到 '{chest_name}' 对应的英文图片名为: {img_name}")
            return img_name

    # 本地 Map 兜底
    img_name = CHEST_NAME_MAP.get(chest_name)
    if img_name:
        log(f"网页解析失败或未包含，使用本地预设 '{chest_name}' => {img_name}")
        return img_name

    # 终极兜底
    log(f"[警告] 无法解析 '{chest_name}' 的英文名，将直接使用原名进行匹配")
    return chest_name

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def webbridge(action, args, timeout=15):
    payload = json.dumps({"action": action, "args": args, "session": SESSION})
    try:
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", BASE_URL, "-H", "Content-Type: application/json", "-d", payload],
            capture_output=True, text=True, timeout=timeout
        )
        if not result.stdout.strip():
            return {"error": "empty response", "stderr": result.stderr}
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return {"error": f"invalid JSON: {e}", "raw": result.stdout[:200]}
    except Exception as e:
        return {"error": str(e)}

def check_webbridge():
    """检查 webbridge 是否可用"""
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", BASE_URL, "-m", "3"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() in ("200", "404", "405")
    except:
        return False

def ensure_webbridge_running():
    """自动检测 webbridge 是否开启，如果没有开启则尝试启动它"""
    if check_webbridge():
        return True

    log("检测到 webbridge 未开启，尝试自动启动...")
    bin_path = "/Users/luosky/.kimi-webbridge/bin/kimi-webbridge"
    if not os.path.exists(bin_path):
        home = os.path.expanduser("~")
        bin_path = os.path.join(home, ".kimi-webbridge/bin/kimi-webbridge")

    if not os.path.exists(bin_path):
        log("[错误] 未找到 kimi-webbridge 可执行文件，无法自动开启，请手动开启服务。")
        return False

    try:
        # 启动 webbridge 守护进程
        subprocess.run([bin_path, "start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        # 等待服务初始化和监听端口
        for i in range(5):
            time.sleep(1)
            if check_webbridge():
                log("webbridge 自动启动成功!")
                return True
        log("[警告] 启动命令已执行，但 webbridge 端口在5秒内未响应")
    except Exception as e:
        log(f"[错误] 自动启动 webbridge 失败: {e}")
    return False

def start_caffeinate():
    """使用 macOS 的 caffeinate 工具，在脚本运行期间防止系统和屏幕息屏"""
    try:
        pid = os.getpid()
        # 启动 caffeinate，-d 阻止显示器休眠，-i 阻止系统闲置休眠，-w 绑定到当前进程 PID
        subprocess.Popen(["caffeinate", "-d", "-i", "-w", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log("已启动 caffeinate，脚本运行期间将保持屏幕和系统常亮")
    except Exception as e:
        log(f"[警告] 启动 caffeinate 失败（这不影响脚本正常运行）: {e}")

def ensure_tab():
    """确保 session 已绑定到 Melvor 标签页"""
    # 先尝试 find_tab，使用支持 Chrome Extension match pattern 的格式
    resp = webbridge("find_tab", {"url": "https://melvoridle.com/index_game.php"})
    if resp.get("ok"):
        log("已找到 Melvor 标签页")
        return True

    # find_tab 失败，尝试 navigate 打开（页面加载可能较慢，给 30 秒）
    log(f"未找到 Melvor 标签页，尝试打开... : {resp}")
    resp = webbridge("navigate", {"url": "https://melvoridle.com/index_game.php"}, timeout=30)
    if resp.get("ok"):
        log("已打开 Melvor 标签页，等待页面加载...")
        time.sleep(35)
        return True

    log(f"[错误] 无法绑定 Melvor 标签页: {resp.get('error', resp)}")
    return False

def extract_response_value(resp):
    """从 webbridge 响应中提取 JS 返回值"""
    try:
        if "data" in resp and "value" in resp["data"]:
            return json.loads(resp["data"]["value"])
        if "error" in resp:
            log(f"[webbridge错误] {resp.get('error')}")
    except json.JSONDecodeError:
        raw = resp.get("data", {}).get("value", "")
        log(f"[JSON解析失败] raw: {raw[:100]}")
    except Exception as e:
        log(f"[响应解析异常] {e}")
    return None

def get_popup_state():
    resp = webbridge("evaluate", {
        "code": """(() => {
            const popup = document.querySelector(".swal2-popup");
            if (!popup) return JSON.stringify({ found: false });
            const text = popup.innerText;
            const match = text.match(/你找到了：\\s*(\\d+)/);
            const itemMatch = text.match(/你找到了：\\s*\\n\\s*\\n\\s*(\\d+)\\s*(\\S+)/);
            const hasReroll = text.includes("Reroll");
            const hasConsent = text.includes("Consent");
            const hasOk = text.includes("好");
            return JSON.stringify({
                found: true,
                value: match ? parseInt(match[1]) : null,
                itemName: itemMatch ? itemMatch[2] : null,
                hasReroll,
                hasConsent,
                hasOk,
                text: text.slice(0,200)
            });
        })()"""
    })
    result = extract_response_value(resp)
    return result if result else {"found": False}

def click_reroll():
    return webbridge("evaluate", {
        "code": """(() => {
            const popup = document.querySelector(".swal2-popup");
            if (!popup) return JSON.stringify({ error: "no popup" });
            const buttons = Array.from(popup.querySelectorAll("button"));
            const rerollBtn = buttons.find(b => b.innerText.includes("Reroll"));
            if (!rerollBtn) return JSON.stringify({ error: "no reroll button" });
            rerollBtn.click();
            return JSON.stringify({ clicked: true });
        })()"""
    })

def click_consent():
    return webbridge("evaluate", {
        "code": """(() => {
            const popup = document.querySelector(".swal2-popup");
            if (!popup) return JSON.stringify({ error: "no popup" });
            const buttons = Array.from(popup.querySelectorAll("button"));
            const consentBtn = buttons.find(b => b.innerText.includes("Consent"));
            if (!consentBtn) return JSON.stringify({ error: "no consent button" });
            consentBtn.click();
            return JSON.stringify({ clicked: true });
        })()"""
    })

def click_ok():
    return webbridge("evaluate", {
        "code": """(() => {
            const popup = document.querySelector(".swal2-popup");
            if (!popup) return JSON.stringify({ error: "no popup" });
            const buttons = Array.from(popup.querySelectorAll("button"));
            const okBtn = buttons.find(b => b.innerText.includes("好"));
            if (!okBtn) return JSON.stringify({ error: "no ok button" });
            okBtn.click();
            return JSON.stringify({ clicked: true });
        })()"""
    })

def ensure_slider_is_1():
    """严格确保滑块值为1，返回是否成功"""
    resp = webbridge("evaluate", {
        "code": """(() => {
            // 查找"打开物品"区域的 ionRangeSlider 滑块
            const irsRound = document.querySelector(".irs.irs--round.js-irs-2");
            if (!irsRound) return JSON.stringify({ error: "未找到 rangeslider 滑块" });

            // 检查是否在打开物品区域附近
            const openBtn = Array.from(document.querySelectorAll("button")).find(b => {
                if (!b.innerText.includes("打开物品")) return false;
                const r = b.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            });
            if (!openBtn) return JSON.stringify({ error: "未找到打开物品按钮" });

            const handle = irsRound.querySelector(".irs-handle");
            if (!handle) return JSON.stringify({ error: "未找到滑块手柄" });

            // 获取手柄当前位置
            const handleRect = handle.getBoundingClientRect();
            const startX = handleRect.left + handleRect.width / 2;
            const startY = handleRect.top + handleRect.height / 2;

            // 目标位置：最左端
            const endX = 670;
            const endY = startY;

            // 通过拖动手柄到最左端来设置值为1
            handle.dispatchEvent(new MouseEvent("mousedown", {
                clientX: startX, clientY: startY, bubbles: true, cancelable: true
            }));
            handle.dispatchEvent(new MouseEvent("mousemove", {
                clientX: endX, clientY: endY, bubbles: true, cancelable: true
            }));
            handle.dispatchEvent(new MouseEvent("mouseup", {
                clientX: endX, clientY: endY, bubbles: true, cancelable: true
            }));

            // 验证结果
            const single = irsRound.querySelector(".irs-single");
            const displayVal = single ? single.innerText.trim() : null;
            const slider = document.querySelector("input[name=bank-rangeslider-open]");
            const inputVal = slider ? slider.value : null;

            return JSON.stringify({
                sliderSetTo: displayVal || inputVal,
                sliderFound: true,
                isOne: displayVal === "1" || inputVal === "1"
            });
        })()"""
    })
    result = extract_response_value(resp)
    if result:
        if "error" in result:
            log(f"[滑块错误] {result['error']}")
            return False
        return result.get("isOne", False)
    return False

def click_open_item():
    return webbridge("evaluate", {
        "code": """(() => {
            const openBtn = Array.from(document.querySelectorAll("button")).find(b => {
                if (!b.innerText.includes("打开物品")) return false;
                const r = b.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            });
            if (!openBtn) return JSON.stringify({ error: "未找到可见的打开物品按钮" });
            if (openBtn.disabled) return JSON.stringify({ error: "按钮已禁用", disabled: true });
            openBtn.click();
            return JSON.stringify({ clicked: true, disabled: false });
        })()"""
    })

def find_and_select_chest(chest_name):
    """在仓库中找到并选中指定名称的宝箱"""
    # 获取英文图片文件名
    img_name = resolve_chest_img_name(chest_name)

    resp = webbridge("evaluate", {
        "code": f"""(() => {{
            let found = null;

            // 方法1: 通过图片文件名查找（最可靠）
            const imgs = document.querySelectorAll('.bank-item img');
            for (const img of imgs) {{
                const src = img.src || '';
                if (src.includes('{img_name}')) {{
                    found = img.closest('.bank-item');
                    break;
                }}
            }}

            // 方法2: 查找带有 title 或 alt 属性匹配的元素
            if (!found) {{
                document.querySelectorAll('[title*="{chest_name}"], [alt*="{chest_name}"]').forEach(el => {{
                    if (!found) found = el;
                }});
            }}

            // 方法3: 查找包含宝箱名称的文本节点
            if (!found) {{
                const allElements = document.querySelectorAll('*');
                for (const el of allElements) {{
                    if (el.innerText && el.innerText.includes('{chest_name}') && el.offsetParent !== null) {{
                        let clickable = el.closest('.bank-item, .bank-tab-item, [onclick], button, a');
                        if (!clickable) clickable = el;
                        found = clickable;
                        break;
                    }}
                }}
            }}

            if (!found) {{
                return JSON.stringify({{
                    error: '未找到名为 {chest_name} 的物品',
                    searched: true
                }});
            }}

            // 滚动到可见位置并点击
            found.scrollIntoView({{ behavior: 'instant', block: 'center' }});
            found.click();

            return JSON.stringify({{
                clicked: true,
                element: found.tagName,
                text: (found.innerText || '').slice(0, 50)
            }});
        }})()"""
    })
    return extract_response_value(resp)

def select_chest_by_scrolling(chest_name):
    """通过滚动仓库来查找并选中宝箱"""
    # 获取英文图片文件名
    img_name = resolve_chest_img_name(chest_name)

    resp = webbridge("evaluate", {
        "code": f"""(() => {{
            // 获取仓库容器
            const bankContainer = document.querySelector('#bank-container, .bank-container, [class*="bank-container"]');
            if (!bankContainer) {{
                return JSON.stringify({{ error: '未找到仓库容器' }});
            }}

            // 先检查当前可见区域是否有目标物品
            const checkVisible = () => {{
                const items = bankContainer.querySelectorAll('.bank-item');
                for (const item of items) {{
                    // 通过图片文件名查找
                    const img = item.querySelector('img');
                    if (img && img.src && img.src.includes('{img_name}')) {{
                        item.scrollIntoView({{ behavior: 'instant', block: 'center' }});
                        item.click();
                        return {{ found: true, src: img.src.split('/').pop() }};
                    }}
                    // 通过文本查找
                    const text = item.innerText || '';
                    if (text.includes('{chest_name}')) {{
                        item.scrollIntoView({{ behavior: 'instant', block: 'center' }});
                        item.click();
                        return {{ found: true, text: text.slice(0, 50) }};
                    }}
                }}
                return {{ found: false }};
            }};

            // 先检查当前区域
            let result = checkVisible();
            if (result.found) {{
                return JSON.stringify({{ clicked: true, ...result }});
            }}

            // 尝试滚动查找
            const scrollStep = 200;
            const maxScroll = bankContainer.scrollHeight;
            let currentScroll = 0;

            for (let i = 0; i < 50; i++) {{
                currentScroll += scrollStep;
                if (currentScroll > maxScroll) break;
                bankContainer.scrollTop = currentScroll;
                result = checkVisible();
                if (result.found) {{
                    return JSON.stringify({{ clicked: true, ...result, scrollPos: currentScroll }});
                }}
            }}

            return JSON.stringify({{
                error: '滚动查找后仍未找到 {chest_name}',
                searched: true,
                totalScroll: maxScroll
            }});
        }})()"""
    })
    return extract_response_value(resp)

def ensure_chest_selected(chest_name, max_retries=3):
    """确保宝箱已被选中，如果没有则自动选中"""
    for attempt in range(max_retries):
        # 先检查打开物品按钮是否存在（说明已有物品被选中）
        btn_status = check_open_btn_exists()
        if btn_status.get("exists"):
            log(f"物品已选中（打开物品按钮存在）")
            return True

        log(f"尝试选中宝箱 '{chest_name}' (第 {attempt+1} 次)...")

        # 尝试直接点击查找
        result = find_and_select_chest(chest_name)
        if result and result.get("clicked"):
            log(f"已选中: {result.get('text', '')}")
            time.sleep(1)
            # 验证是否选中成功
            btn_status = check_open_btn_exists()
            if btn_status.get("exists"):
                return True

        # 尝试滚动查找
        log("尝试滚动仓库查找...")
        result = select_chest_by_scrolling(chest_name)
        if result and result.get("clicked"):
            log(f"滚动找到并选中: {result.get('text', '')}")
            time.sleep(1)
            btn_status = check_open_btn_exists()
            if btn_status.get("exists"):
                return True

        log(f"第 {attempt+1} 次尝试失败，等待2秒后重试...")
        time.sleep(2)

    log(f"[错误] 经过 {max_retries} 次尝试仍无法选中 '{chest_name}'")
    return False

def check_open_btn_exists():
    """检查打开物品按钮是否存在"""
    resp = webbridge("evaluate", {
        "code": """(() => {
            const openBtn = Array.from(document.querySelectorAll("button")).find(b => {
                if (!b.innerText.includes("打开物品")) return false;
                const r = b.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            });
            if (!openBtn) return JSON.stringify({ exists: false });
            return JSON.stringify({ exists: true, disabled: openBtn.disabled });
        })()"""
    })
    result = extract_response_value(resp)
    return result if result else {"exists": False}

def check_page_responsive():
    """检查页面是否响应（息屏后可能无响应）"""
    resp = webbridge("evaluate", {
        "code": """(() => {
            return JSON.stringify({
                responsive: true,
                timestamp: Date.now()
            });
        })()"""
    })
    result = extract_response_value(resp)
    return result is not None and result.get("responsive", False)

def keep_page_alive():
    """保持页面活跃（息屏时防止JavaScript暂停）"""
    return webbridge("evaluate", {
        "code": """(() => {
            // 触发一个微小的DOM操作来保持页面活跃
            const el = document.createElement('div');
            el.style.display = 'none';
            document.body.appendChild(el);
            document.body.removeChild(el);
            return JSON.stringify({ alive: true });
        })()"""
    })

def wake_up_page():
    """唤醒页面（息屏后恢复）"""
    # 尝试多种方式唤醒页面
    resp = webbridge("evaluate", {
        "code": """(() => {
            // 1. 尝试聚焦窗口
            if (window.focus) window.focus();
            
            // 2. 触发鼠标移动事件
            document.dispatchEvent(new MouseEvent('mousemove'));
            
            // 3. 触发键盘事件
            document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Shift' }));
            
            // 4. 尝试滚动页面
            window.scrollBy(0, 0);
            
            // 5. 检查页面是否真的被暂停
            const now = Date.now();
            const start = performance.now();
            
            // 执行一个简单的计算来检测页面是否响应
            let dummy = 0;
            for (let i = 0; i < 1000; i++) {
                dummy += Math.sqrt(i);
            }
            
            const elapsed = performance.now() - start;
            
            return JSON.stringify({
                waked: true,
                elapsed: elapsed,
                timestamp: now
            });
        })()"""
    })
    result = extract_response_value(resp)
    return result and result.get("waked", False)

def main():
    if len(sys.argv) < 3:
        print("用法: python melvor_chest_bot.py <宝箱名字> <目标1> [目标2] ...")
        print("目标格式: 奖品名字:最低数量 或 奖品名字 或 _:最低数量")
        print("示例: python melvor_chest_bot.py 深渊钓鱼宝箱 虚空之心:3")
        print("      python melvor_chest_bot.py 深渊钓鱼宝箱 虚空之心:3 灰烬:190")
        print("      python melvor_chest_bot.py 灵火矿脉荚 灰烬:190 _:200")
        sys.exit(1)

    chest_name = sys.argv[1]

    # 解析多个目标
    targets = []
    for arg in sys.argv[2:]:
        if ":" in arg:
            parts = arg.split(":", 1)
            name = parts[0] if parts[0] != "_" else None
            count = int(parts[1]) if parts[1] else None
            if name or count:
                targets.append({"name": name, "count": count})
        else:
            # 只有名字，没有数量
            if arg != "_":
                targets.append({"name": arg, "count": None})
            else:
                targets.append({"name": None, "count": None})

    if not targets:
        print("[错误] 至少需要一个目标")
        sys.exit(1)

    stats = {}
    pending_item_name = None
    pending_item_value = 0

    chest_count = 0
    total_rerolls = 0
    consecutive_errors = 0
    same_state_count = 0
    last_state_text = ""

    log(f"=== Melvor Idle {chest_name} 自动开启脚本启动 ===")
    log(f"Session: {SESSION}, Target: Chrome")
    log(f"目标数量: {len(targets)}")
    for i, t in enumerate(targets):
        name_desc = t["name"] if t["name"] else "任意"
        count_desc = f">{t['count']}" if t["count"] is not None else "任意数量"
        log(f"  目标{i+1}: {name_desc} {count_desc}")

    # 检查并确保 webbridge 运行
    if not ensure_webbridge_running():
        log("[警告] 无法自动启动 webbridge，开始等待手动开启，请确保:")
        log("  1. Kimi 桌面端已启动")
        log(f"  2. Session '{SESSION}' 已在 Chrome 中激活")
        log(f"  3. webbridge 服务运行在 {BASE_URL}")
        log("等待 webbridge 可用...")
        for i in range(30):
            time.sleep(2)
            if check_webbridge():
                log("webbridge 已连接!")
                break
        else:
            log("[错误] webbridge 30秒内未响应，脚本退出")
            return

    # 确保绑定到 Melvor 标签页
    if not ensure_tab():
        log("[错误] 无法绑定 Melvor 标签页，脚本退出")
        return

    # 防止屏幕和系统休眠
    start_caffeinate()

    # 自动选中宝箱
    log(f"正在自动选中宝箱 '{chest_name}'...")
    if not ensure_chest_selected(chest_name):
        log("[错误] 无法自动选中宝箱，请确保:")
        log(f"  1. 仓库中有名为 '{chest_name}' 的宝箱")
        log("  2. 游戏页面已正确加载")
        log("  3. 仓库标签页已打开")
        log("脚本退出")
        return
    log(f"宝箱 '{chest_name}' 已选中，准备开始自动开箱...")

    rule_desc = "每次只开1个宝箱，reroll直到"
    target_descs = []
    for t in targets:
        parts = []
        if t["name"]:
            parts.append(f"是{t['name']}")
        if t["count"] is not None:
            parts.append(f">{t['count']}")
        if parts:
            target_descs.append("且".join(parts))
        else:
            target_descs.append("任意")
    rule_desc += "或".join(target_descs) + "才Consent"
    log(f"规则: {rule_desc}")
    
    while True:
        try:
            # 定期保持页面活跃（防止息屏时JavaScript暂停）
            keep_page_alive()
            
            state = get_popup_state()
            
            if state.get("found"):
                consecutive_errors = 0
                value = state.get("value")
                hasReroll = state.get("hasReroll")
                hasConsent = state.get("hasConsent")
                hasOk = state.get("hasOk")
                
                # 检测重复状态（点击可能无效）
                state_text = f"{value}_{hasReroll}_{hasConsent}_{hasOk}"
                if state_text == last_state_text:
                    same_state_count += 1
                    if same_state_count >= 5:
                        log(f"[状态重复] 连续 {same_state_count} 次相同状态，继续尝试点击...")
                else:
                    same_state_count = 0
                    last_state_text = state_text
                
                if hasReroll and hasConsent:
                    # 处于reroll阶段
                    if value is None:
                        time.sleep(0.8)
                        continue
                    
                    itemName = state.get("itemName", "")

                    # 检查是否满足任意一个目标
                    matched = False
                    match_reason = ""
                    for t in targets:
                        name_ok = not t["name"] or (itemName and t["name"] in itemName)
                        count_ok = t["count"] is None or value > t["count"]
                        if name_ok and count_ok:
                            matched = True
                            match_reason = f"匹配目标[{t['name'] or '任意'}>{t['count'] or '任意'}]"
                            break

                    if matched:
                        log(f">>> 结果 {value} {itemName} {match_reason}! 点击 Consent...")
                        pending_item_name = itemName
                        pending_item_value = value
                        click_consent()
                        time.sleep(1.0)
                        # 验证是否进入下一状态
                        verify = get_popup_state()
                        if verify.get("found") and verify.get("hasReroll"):
                            log("[警告] Consent 未生效，重试...")
                            click_consent()
                            time.sleep(1.5)
                    else:
                        # 收集不满足的原因
                        reasons = []
                        for t in targets:
                            name_ok = not t["name"] or (itemName and t["name"] in itemName)
                            count_ok = t["count"] is None or value > t["count"]
                            if not name_ok and not count_ok:
                                reasons.append(f"不是{t['name']}且数量{value}<={t['count']}")
                            elif not name_ok:
                                reasons.append(f"不是{t['name']}")
                            elif not count_ok:
                                reasons.append(f"数量{value}<={t['count']}")
                        # log(f"结果 {value} {itemName} 不满足({'; '.join(reasons)})，点击 Reroll...")
                        pending_item_name = None
                        pending_item_value = 0
                        click_reroll()
                        total_rerolls += 1
                        time.sleep(0.5)
                        # 验证 reroll 是否生效
                        verify = get_popup_state()
                        if verify.get("found") and verify.get("hasReroll") and verify.get("value") == value:
                            log("[警告] Reroll 未生效，重试...")
                            click_reroll()
                            time.sleep(0.5)
                
                elif hasOk and not hasReroll:
                    # 只有好按钮，说明已Consent，点击关闭
                    log(f"接受结果 {value}，点击 好 关闭...")
                    
                    # 验证弹窗是否真的关闭（息屏后可能点击无效）
                    for retry in range(5):
                        click_ok()
                        time.sleep(1.0)
                        verify = get_popup_state()
                        if not verify.get("found"):
                            break
                        log(f"[警告] 弹窗未关闭，重试点击 ({retry+1}/5)...")
                    
                    if verify.get("found"):
                        log("[错误] 弹窗无法关闭，尝试唤醒页面...")
                        # 尝试唤醒页面
                        for wake_attempt in range(3):
                            wake_up_page()
                            time.sleep(2)
                            # 再次尝试点击
                            click_ok()
                            time.sleep(1)
                            verify = get_popup_state()
                            if not verify.get("found"):
                                log(f"[恢复] 页面唤醒成功，第 {wake_attempt+1} 次尝试后弹窗关闭")
                                break
                        else:
                            log("[错误] 页面唤醒失败，等待10秒后重试...")
                            time.sleep(10)
                            continue
                    
                    if pending_item_name:
                        if pending_item_name not in stats:
                            stats[pending_item_name] = {"times": 0, "amount": 0}
                        stats[pending_item_name]["times"] += 1
                        stats[pending_item_name]["amount"] += pending_item_value
                        log(f"【累计统计】{pending_item_name} -> 本次: {pending_item_value} 个 | 累计: {stats[pending_item_name]['amount']} 个 (共 {stats[pending_item_name]['times']} 次)")
                        pending_item_name = None
                        pending_item_value = 0

                    chest_count += 1
                    log(f"=== 已完成第 {chest_count} 个宝箱 (总reroll次数: {total_rerolls}) ===")
                    time.sleep(0.5)

                    # 关闭后检查是否有新弹窗（可能自动开了下一个）
                    state2 = get_popup_state()
                    if not state2.get("found"):
                        # 没有新弹窗，需要重新选中宝箱并点击打开物品
                        log("没有新弹窗，重新选中宝箱...")

                        # 使用 ensure_chest_selected 确保宝箱真正被选中
                        if not ensure_chest_selected(chest_name):
                            log("[错误] 无法重新选中宝箱，停止脚本")
                            break

                        time.sleep(0.5)

                        # 严格确保滑块为1
                        slider_ok = ensure_slider_is_1()
                        if not slider_ok:
                            log("[警告] 滑块设置失败，重试...")
                            time.sleep(1)
                            slider_ok = ensure_slider_is_1()
                            if not slider_ok:
                                log("[错误] 滑块无法设置为1，停止脚本")
                                break

                        log("滑块已确认设置为1，点击 打开物品...")
                        click_open_item()
                        time.sleep(1.5)
                else:
                    log(f"[未知弹窗状态: hasReroll={hasReroll}, hasConsent={hasConsent}, hasOk={hasOk}]")
                    time.sleep(1.0)
            else:
                # 没有弹窗，需要点击打开物品
                consecutive_errors = 0
                
                # 检查按钮是否存在
                btn_status = check_open_btn_exists()
                if not btn_status.get("exists"):
                    log('[错误] 未找到"打开物品"按钮，可能宝箱已用完或页面状态不对')
                    log("等待5秒后重试...")
                    time.sleep(5)
                    continue
                
                if btn_status.get("disabled"):
                    log("[警告] 按钮已禁用，等待2秒...")
                    time.sleep(2)
                    continue
                
                log("没有弹窗，准备开启宝箱...")
                
                # 严格确保滑块为1
                slider_ok = ensure_slider_is_1()
                if not slider_ok:
                    log("[警告] 滑块设置失败，重试...")
                    time.sleep(1)
                    slider_ok = ensure_slider_is_1()
                    if not slider_ok:
                        log("[错误] 滑块无法设置为1，停止脚本")
                        break
                
                log("滑块已确认设置为1，点击 打开物品...")
                click_result = click_open_item()
                result_value = extract_response_value(click_result) if click_result else None
                
                if result_value and result_value.get("error"):
                    log(f"[错误] {result_value['error']}")
                    time.sleep(2)
                    continue
                
                time.sleep(1.5)
                
                # 验证是否出现弹窗
                verify = get_popup_state()
                if not verify.get("found"):
                    log("[警告] 点击后未出现弹窗，等待2秒后重试...")
                    time.sleep(2)
                    # 再次检查
                    verify2 = get_popup_state()
                    if not verify2.get("found"):
                        log("[错误] 仍然没有弹窗，可能宝箱已用完或需要手动操作")
                        log("等待5秒后重试...")
                        time.sleep(5)
                
        except Exception as e:
            consecutive_errors += 1
            log(f"[错误] {e} (连续错误: {consecutive_errors})")
            if consecutive_errors >= 10:
                log("连续错误过多，脚本停止")
                break
            time.sleep(3)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("=== 用户中断 ===")
        sys.exit(0)
    except Exception as e:
        log(f"=== 致命错误: {e} ===")
        sys.exit(1)

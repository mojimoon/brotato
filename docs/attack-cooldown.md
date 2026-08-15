# 攻击间隔随机化：源码机制、蒙特卡洛模拟与三方案对比

> 研究目标：搞清楚 Brotato 真实源码是如何随机化「武器攻击间隔」的，然后用四把代表性武器做蒙特卡洛模拟，
> 判断真实的范围 / 均值，并对比 **MultiTool**、**ImprovedTooltips（mod）**、**我们 codex 的实现** 哪种最准。
>
> ⚠️ 取整存在一些不明确性（尤其 recoil 的 tween 到底占几帧），所以绝对数值只能「供参考」，±1~2 帧属正常。

---

## 一、游戏源码是怎么随机化攻击间隔的

攻击间隔 = **空闲时间（recoil / 近战动画，确定值）** + **随机化的武器冷却（帧）**。

### 1.1 随机化的武器冷却（`weapons/weapon.gd`）

```gdscript
# get_next_cooldown() —— 每次开火后调用，返回「下一发冷却（帧，连续浮点）」
func get_next_cooldown(at_wave_begin = false):
    if is_big_reload_active(at_wave_begin):
        return current_stats.cooldown * current_stats.additional_cooldown_multiplier
    var cooldown_basis = current_stats.cooldown          # 已含攻速修正的整数帧
    if at_wave_begin and cooldown_basis >= 180:
        cooldown_basis = 180
    var max_rand = get_max_rand_cooldown(cooldown_basis)
    return rand_range(max(1, cooldown_basis - max_rand), cooldown_basis + max_rand)

func get_max_rand_cooldown(cooldown_basis):
    var weapon_count = min(_parent.get_nb_weapons(), 6)
    return min(weapon_count * cooldown_basis / 5.0, weapon_count * 5.0)
```

要点：

- **随机化是均匀分布** `rand_range(lo, hi)`，只作用在「武器冷却帧数」上，对 recoil / 动画空闲时间无影响。
- **`cooldown_basis`** = `current_stats.cooldown`，即攻速修正后的整数帧：`apply_attack_speed_mod_to_cooldown` 里
  `max(MIN_COOLDOWN=2, floor(base_cooldown / (1 + atkSpd)))`（`singletons/weapon_service.gd:570`）。
- **`max_rand`** = `min(weapon_count · cooldown_basis / 5, weapon_count · 5)`，`weapon_count` 夹到 `[1, 6]`。
- 均值（对称时）= `cooldown_basis`；当下界被 `max(1, …)` 截断时均值会略微抬升。
- 冷却计数器 `_current_cooldown` 只在「非射击」时扣减；recoil / 动画 tween 期间冻结，所以**空闲时间是实打实叠在冷却之上的**。

### 1.2 空闲时间（确定性）

**远程**（`weapons/shooting_behaviors/ranged_weapon_shooting_behavior.gd`）：两段各 `recoil_duration` 秒的 tween，
所以 `空闲帧 = 2 × recoil_duration × 60`。`recoil_duration` 会被攻速缩放：`recoil_duration /= (1 + atkSpd)`（`weapon_service.gd:232`）。

**近战**（`melee_weapon_shooting_behavior.gd` + `melee_shooting_data.gd`）：
`空闲 = recoil_duration + attack_duration/2 + back_duration`（Swing / Thrust 都是 `atkDur/2`，只是摆动轨迹不同）。
`attack_duration` 随攻击距离变化：`atkDur = max(0.01, 0.2 − atkSpd/10) + range_factor·0.15`，
`range_factor = max_range / clamp(70·(1+atkSpd/3), 70, 120)`，`back_duration = 0.2 / (1 + atkSpd·3)`。
> 源码里**没有**「Swing +1 帧」这种东西——那是工具自己加的启发式。

### 1.3 确定性基础间隔（不含随机）

| 武器 | cooldown_basis(0%攻速) | 空闲帧 | 基础间隔(帧) = 空闲 + cooldown |
|------|------|------|------|
| SMG T1（远程·高攻速） | 4 | 2×0.05×60 = 6 | 10 |
| Sniper Pistol T3（远程·低攻速） | 50 | 2×0.1×60 = 12 | 62 |
| Hatchet T1（近战·高攻速·Swing） | 9 | (0.1 + 0.234 + 0.2)×60 = 32.0 | 41.0 |
| War Hammer T3（近战·低攻速·Swing） | 60 | (0.1 + 0.288 + 0.2)×60 = 35.3 | 95.3 |

---

## 二、四把武器的蒙特卡洛模拟（真实源码公式）

复刻上面的 `rand_range` 均匀分布，每配置 400 万次抽样（连续浮点，即源码的「理想」下限；
实际游戏因 tween 取整会比这个略高 1~2 帧，见第五节）。

格式：`min–maxf（均值，秒）`。`cd[a, b]` 是随机化冷却区间（不含空闲）。

| 武器 | 武器数 | 真实范围 (min–max) | 真实均值 | 随机化冷却区间 |
|------|------|------|------|------|
| SMG T1 | 1 | 9.2–10.8f（10.0f / 0.167s） | 10.0f | [3.2, 4.8] |
| SMG T1 | 6 | 7.0–14.8f（10.9f / 0.182s） | 10.9f | [1, 8.8] |
| SMG T1 +1%攻速 | 1 | 8.3–9.5f（8.9f / 0.149s） | 8.9f | [2.4, 3.6] |
| Sniper Pistol T3 | 1 | 57–67f（62.0f / 1.033s） | 62.0f | [45, 55] |
| Sniper Pistol T3 | 6 | 32–92f（62.0f / 1.033s） | 62.0f | [20, 80] |
| Hatchet T1 | 1 | 39.2–42.8f（41.0f / 0.684s） | 41.0f | [7.2, 10.8] |
| Hatchet T1 | 6 | 33.0–51.8f（42.4f / 0.707s） | 42.4f | [1, 19.8] |
| War Hammer T3 | 1 | 90.3–100.3f（95.3f / 1.587s） | 95.3f | [55, 65] |
| War Hammer T3 | 6 | 65.3–125.3f（95.3f / 1.587s） | 95.3f | [30, 90] |

> 观察：
> - **武器数越大，范围越宽**（×6 时 SMG 是 7–15f，Hatchet 是 33–52f），均值几乎不变（随机是对称的）。
> - SMG 从 0%→+1% 攻速：均值 10.0→8.9f，**只少约 1 帧**（cooldown_basis 4→3）。这正是之前修掉的 bug 想要表达的结论。
> - 近战「基础攻击间隔有确定公式」成立；随机只来自 cooldown 那段，idle 是确定的（在固定攻击距离下）。

---

## 三、三种方案的实现方式

### MultiTool（`ArosRising's Brotato MultiTool 1.4.xlsx` · DPS Calculator!M6）
- **只给一个均值，不显示范围**。
- 远程：`(wcf+1)/60 + 2·ROUNDDOWN(recoil·60+1)/60 + W36/60`
- 近战：`ROUNDDOWN((wcf+1)+ROUNDDOWN(recoil·60+1)+ROUNDDOWN(atkDur/2·60+1)+ROUNDDOWN(backDur·60+1)+1)/60 + Swing奖励 + W36/60`
- `W36`（随机化平均修正）= `V36 + 0.5 − wcf`，即「随机区间中点 + 0.5 缓冲」——和我们 `getWeaponRandomizationFrames` 完全同公式。
- recoil 用 `ROUNDDOWN(recoil·60+1)`：整数 recoil 每项多算 1 帧。

### ImprovedTooltips（mod，`_wl-ImprovedTooltips` · `item_description.gd`）
- **显示显式 min–max 范围**，均值取中点 `(min+max)/2`。
- 远程：`add_cd = 2·tween(recoil) − 1`；`min = add_cd + floor(max(1, wcf−spread)) + 1`，`max = add_cd + ceil(wcf+spread)`。
- 近战：`add_cd = tween(recoil) + tween(backDur) − 1 + (Swing: 2·tween(atkDur/4))`；min/max 同上。
- `spread = min(weapon_count·wcf/5, weapon_count·5)`（与源码一致）。
- `tween(d)` 是作者手调的 hack：`d==0.05 → 4`，否则 `floor(d·60)+2`。注释自承「0.05s 比预期少 1 帧、0.1s 偶尔少 1 帧，全部忽略」。

### 我们 codex 的实现（`codex/src/App.vue`）
- **远程**：与 mod 完全一致（`getRangedCooldownRange`，中点即显示值）。
- **近战**：显示值用 `round` 逐段折算 + 范围感知（`getMeleeTiming`，与源码同公式）+ Swing +1 + `W36` 平均修正；
  **但「帧数」后缀的范围有 bug**——`frameRange()` 的近战分支漏算了 recoil 帧（且没 +1 缓冲），导致范围比真实值低约 6~10 帧。

---

## 四、三方案数值对比（count=1 与 count=6，0% 攻速）

带 `*` 的「范围」来自 mod / 我们的实现；MultiTool 无范围，只列均值。

### 远程

| 武器 | 真实(源码) | MultiTool | mod / 我们 |
|------|------|------|------|
| SMG T1 ×1 | 9.2–10.8f（10.0f / 0.167s） | 13.5f（0.225s） | **11–12f（11.5f / 0.192s）** |
| SMG T1 ×6 | 7.0–14.8f（10.9f / 0.182s） | 14.4f（0.240s） | **9–16f（12.5f / 0.208s）** |
| SMG T1 +1% ×1 | 8.3–9.5f（8.9f / 0.149s） | 10.5f（0.175s） | **10–11f（10.5f / 0.175s）** |
| Sniper Pistol T3 ×1 | 57–67f（62.0f / 1.033s） | 65.5f（1.092s） | **61–70f（65.5f / 1.092s）** |
| Sniper Pistol T3 ×6 | 32–92f（62.0f / 1.033s） | 65.5f（1.092s） | **36–95f（65.5f / 1.092s）** |

> SMG ×1 的 11–12f / +1% 的 10–11f 正是你和两位作者核对过的「正确值」——来自 mod / 我们的实现，
> 而源码连续公式给出的是 9–11f / 8.3–9.5f（低约 1.5 帧，全部来自 recoil tween 取整，见第五节）。

### 近战

| 武器 | 真实(源码) | MultiTool | mod | 我们(值 / 范围bug) |
|------|------|------|------|------|
| Hatchet T1 ×1 | 39.2–42.8f（41.0f / 0.684s） | 47.5f（0.792s） | 47–50f（48.5f / 0.808s） | **44.5f（0.742s）** / 34–38f ⚠️ |
| Hatchet T1 ×6 | 33.0–51.8f（42.4f / 0.707s） | 48.9f（0.815s） | 41–59f（50.0f / 0.833s） | **45.9f（0.765s）** / 28–47f ⚠️ |
| War Hammer T3 ×1 | 90.3–100.3f（95.3f / 1.587s） | 101.5f（1.692s） | 97–106f（101.5f / 1.692s） | **98.5f（1.642s）** / 85–95f ⚠️ |
| War Hammer T3 ×6 | 65.3–125.3f（95.3f / 1.587s） | 101.5f（1.692s） | 72–131f（101.5f / 1.692s） | **98.5f（1.642s）** / 60–120f ⚠️ |

---

## 五、哪种方案最准确？

**远程：MultiTool 最不准，mod 与我们实现并列最准。**
- MultiTool 不显示范围（只能看均值），且 recoil 用 `ROUNDDOWN(recoil·60+1)` 让 SMG 空闲变成 8 帧（真实 ~6、mod/我们 7），整体偏高约 2~3 帧。
- mod 与我们实现完全一致，且 SMG 的 11–12f / 10–11f 已被你和社区核对为实际游戏表现 → **远程以 mod / 我们为准**。

**近战：我们的「值」最接近源码，mod 偏高约 7 帧，MultiTool 同样偏高。但我们的「范围后缀」有 bug。**
- 源码近战空闲用精确动画时长（无 +2 hack、无 Swing +1）；mod 的 `tween(d)=floor(d·60)+2` 给每个动画 tween 多塞 2 帧，Hatchet/Hammer 凭空高 ~7 帧。
- 我们的近战显示值用 `round`（无 +2 hack）+ 范围感知，只比源码高约 3~4 帧（来自 `wcf+1`、`+1` 缓冲、Swing +1），**是三者里最贴近源码的**。
- ⚠️ 但我们的「帧数」切换里近战范围后缀漏算 recoil 帧（且缺 +1 缓冲），显示成 34–38f（Hatchet）这种比真实低约 6~10 帧的错值——这是要修的 bug。

**取整不确定性（为什么不能钉死到 <1 帧）：**
- 真实游戏的 tween 是「秒」为单位、按 60fps 量化。SMG 的 `0.05s` 在连续公式里是 3 帧/tween（共 6），
  但 mod 作者实测「0.05s 比预期少 1 帧」，于是用 `tween(0.05)=4` 校准（共 7）。
  这正是源码连续值（9–11f）与 mod/我们（11–12f）差 1.5 帧的根源。
- 因为社区已用实测确认 mod/我们的远程值对得上游戏内表现，我们**把 mod/我们当作远程的实际参考**；
  源码连续公式是「理论下限」。近战没有你的实测对照，按源码公式 + 我们的 round 实现最稳。

---

## 六、结论与待办

1. **源码随机化机制已厘清**：范围只来自 `rand_range(max(1, wcf−max_rand), wcf+max_rand)` 的冷却帧；idle 是确定值。
2. **远程**：mod 与我们的实现最准，已对齐社区实测；MultiTool 不显示范围且 recoil 偏高。
3. **近战**：我们的「显示值」最贴近源码（比 mod 低 ~4 帧）；但「帧数」范围后缀有 bug（漏 recoil），需修。
4. **建议**：把 codex 近战 `frameRange()` 补上 recoil 帧并统一 `tween_duration` 折算（或保持 round 与显示值一致），让近战范围后缀与点值自洽。代码改动未提交，按惯例由你自行 commit。

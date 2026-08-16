# Brotato 武器冷却机制（简化版）

**推荐使用土豆兄弟图鉴 - [mojimoon.top](https://brotato.mojimoon.top/) 进行准确的冷却计算。**

## 0. 总览

$$\text{CD}_{\text{冷却均值}} = T_{\text{攻击间隔（固定）}} + C_{\text{延迟帧（随机）}}$$

冷却时间包含**回弹动画**和仅限近战武器的**挥砍动画**，受**攻速**与**范围**影响，是固定的。

延迟帧 $C$ 受**武器数量**影响，是随机的。

游戏中的 1 秒 = 60 帧。下文中，用 $t$ 和 $f$ 表示以秒和帧表示的时长。

## 1. 基础信息

**攻速因子**（面板攻速 % → 小数）

$$a=\frac{\%\text{攻击速度}}{100}$$

**冷却帧 (f)** （基于武器的基础冷却帧 $w_{\text{base}}$，正攻速缩短，负攻速延长。下限为 2 帧）

$$w = \max\Big(2,\;\Big\lfloor\begin{cases}\dfrac{w_{\text{base}}}{1+a}, & a\ge 0\\ w_{\text{base}}(1+|a|), & a<0\end{cases}\Big\rfloor\Big)$$

**注意：显示冷却帧 $w$ 仅影响随机延迟帧 $C$，不影响固定攻击间隔 $T$。**

**回弹时长 (s)**（基于武器的基础回弹时长 $r_{\text{base}}$，正攻速缩短，负攻速不变。大部分武器的 $r_{\text{base}}$ 为 0.1s）

$$r=\begin{cases}\dfrac{r_{\text{base}}}{1+a}, & a\ge 0\\ r_{\text{base}}, & a<0\end{cases}$$

**tween 帧数折算(s→f)**（将秒数转换为动画实际占用的帧数）

$$\text{tween}(s) = \begin{cases}4, & s=0.05\\ \lfloor s \cdot 60\rfloor + 2, & \text{其他}\end{cases}$$

## 2. 远程武器

远程武器的冷却时间只包含 2 段回弹动画（前摇 + 后摇）。

**回弹动画 (f)**

$$f_\text{recoil} = 2 \cdot \text{tween}(r) - 1$$

**攻击间隔 (f)**

$$\boxed{f = 2 \cdot \text{tween}(r) - 1 + C}$$

除以 60 即得实际冷却时间 (s)。

**tooltip 显示冷却时间 (s)**

$$\boxed{t_\text{tooltip} = 2r + \frac{w}{60}}$$

## 3. 近战武器

近战武器的冷却时间包含 3 段动画（前摇 + 挥砍 + 后摇）。

**范围因子**（与武器范围成正比。正攻速 $a$ 减少范围因子，+215 攻速时最多减少到 $\frac{7}{12}$，负攻速不会增加范围因子）

$$\text{rangeFactor} = \frac{\text{max\_range}}{\text{clamp}\big(70(1+a/3),\;70,\;120\big)}$$

其中 $\text{max\_range}$ 为武器范围，相当于武器的基础范围 + 玩家范围属性的一半。例如，基础范围 150，玩家范围属性 100，则 $\text{max\_range} = 150 + 100/2 = 200$。

**前摇动画 (s)**

$$t_\text{pre} = r$$

**挥砍动画 (s)**（分为两部分，攻速越高、范围因子越低，挥砍动画越短）

$$t_\text{atk} = \max\Big(0.01,\; 0.2 - \frac{a}{10}\Big) + \text{rangeFactor} \times 0.15$$

**后摇动画 (s)**（基础值 0.2 秒，正攻速缩短，负攻速不变）

$$t_\text{back} = \frac{0.2}{1 + \max(0,a) \times 3}$$

**攻击间隔 (f)**

$$\boxed{f = \text{tween}(r) + \text{tween}(t_\text{back}) - 1 + \begin{cases} \text{tween}(\frac{t_\text{atk}}{2}), & \text{突刺}\\ 2\text{tween}(\frac{t_\text{atk}}{4}), & \text{横扫}\end{cases} + C}$$

除以 60 即得实际冷却时间 (s)。

对于在两种攻击方式之间交替的武器，当 $\text{tween}(\frac{t_\text{atk}}{2}) > 2\text{tween}(\frac{t_\text{atk}}{4})$ 时，冷却下界 -2 帧、均值 -1 帧。

**tooltip 显示冷却时间 (s)**

$$\boxed{t_\text{tooltip} = r + t_\text{back} + \frac{t_\text{atk}}{2} + \frac{w}{60}}$$

## 3. 随机延迟帧

随机延迟帧 (f) 是在 $\max(1, w - \Delta)$ 到 $w + \Delta$ 之间均匀分布的整数，其中 $\Delta = \min\Big(\frac{nw}{5},5n\Big)$，$n$ 为武器数量，最多取 6。

对这个均匀分布求期望即得到 $C$ 的均值，下文用 $\text{getAvg}$ 表示，具体算法：

$$\text{tri}_v = \frac{v(v+1)}{2}$$

$$\text{getAvg}(\text{min}, \text{max}) = \frac{(\lceil\text{min}\rceil - \text{min})\lceil\text{min}\rceil + \text{tri}_{\lfloor\text{max}\rfloor} - \text{tri}_{\lceil\text{min}\rceil} + (\text{max} - \lfloor\text{max}\rfloor)\lceil\text{max}\rceil}{\text{max} - \text{min}}$$

武器数量越多，$\Delta$ 越大，随机延迟帧的范围越宽，但是几乎不影响均值（注意由于下限最少为 1 帧，当 $w < 30$ 时随着武器数量增加确实会略微增加均值）。

当 $w \le 25$ 时：

| $n$ | 下限 | 上限 |
| --- | --- | --- |
| 1 | $\max(1,\frac{4}{5}w)$ | $\frac{6}{5}w$ |
| 2 | $\max(1,\frac{3}{5}w)$ | $\frac{7}{5}w$ |
| 3 | $\max(1,\frac{2}{5}w)$ | $\frac{8}{5}w$ |
| 4 | $\max(1,\frac{1}{5}w)$ | $\frac{9}{5}w$ |
| 5 | $1$ | $2w$ |
| 6 | $1$ | $\frac{11}{5}w$ |

当 $w > 25$ 时：

| $n$ | 下限 | 上限 |
| --- | --- | --- |
| 1 | $w - 5$ | $w + 5$ |
| 2 | $w - 10$ | $w + 10$ |
| 3 | $w - 15$ | $w + 15$ |
| 4 | $w - 20$ | $w + 20$ |
| 5 | $w - 25$ | $w + 25$ |
| 6 | $\max(1, w - 30)$ | $w + 30$ |

最终，最低和最高延迟帧 (f) 分别为：

$$\boxed{C_\text{min} = \lfloor\max(1, w - \Delta)\rfloor + 1}$$

$$\boxed{C_\text{max} = \lceil w + \Delta\rceil}$$

从上述计算中可以知道，由于 (i) 动画占用的时间 $\text{tween}(f)$ 总是比 tooltip 使用的时长 $\frac{f}{60}$ 多 1-2 帧，(ii) 随机冷却帧的均值总是略高于 tooltip 使用的 $\frac{w}{60}$，因此 tooltip 显示的冷却时间存在低估。通常远程武器相差 1-3 帧，近战武器相差 2-5 帧，随机帧相差的近似值约 0.5-3.5 帧 (0.0833-0.5833 秒，但可能随其他变量进一步变化)。

![](../misc/cooldown_deviation.png)

## 4. 示例计算

以下全部假设 6 把武器的情况。

| 武器 | 类型 | $w_\text{base}$ | $r_\text{base}$ | 范围 | 攻击方式 |
| --- | --- | --- | --- | --- | --- |
| 冲锋枪 T1 | 远程 | 4 | 0.05 | 400 | - |
| 短斧 T1 | 近战 | 9 | 0.1 | 125 | 横扫 |

冲锋枪 T1

- 冷却帧 $w = \lfloor\frac{4}{1}\rfloor = 4$ f
- 回弹时长 $r = \frac{0.05}{1} = 0.05$ s, $\text{tween}(r) = 4$ f
- 回弹动画 $f_\text{recoil} = 2 \times 4 - 1 = 7$ f
- 随机分布 $\Delta = \min(\frac{6 \times 4}{5}, 5 \times 6) = 4.8$
    - $C \sim \mathcal{U}(\max(1, -0.8), 8.8) = \mathcal{U}(1, 8.8)$ f
    - 最小值 $\text{min} = 7 + \lfloor 1 \rfloor + 1 = 9$ f
    - 最大值 $\text{max} = 7 + \lceil 8.8 \rceil = 16$ f
    - 期望 $\bar{C} = \text{getAvg}(1, 8.8) = 5.410$ f
- 冷却均值 $\bar{f} = 7 + 5.410 = 12.410$ f $\rightarrow 0.2068$ s
- 游戏显示 $t_\text{tooltip} = 2 \times 0.05 + \frac{4}{60} = 0.17$ s

冲锋枪 T1 (+1%攻速)

- 冷却帧 $w = \lfloor\frac{4}{1.01}\rfloor = 3$ f
- 回弹时长 $r = \frac{0.05}{1.01} = 0.0495$ s
    - $\text{tween}(r) = \lfloor 0.0495 \times 60\rfloor + 2 = 4$ f
- 回弹动画 $f_\text{recoil} = 2 \times 4 - 1 = 7$ f
- 随机分布 $\Delta = \min(\frac{6 \times 3}{5}, 5 \times 6) = 3.6$
    - $C \sim \mathcal{U}(1, 6.6)$ f
    - 最小值 $\text{min} = 7 + \lfloor 1 \rfloor + 1 = 9$ f
    - 最大值 $\text{max} = 7 + \lceil 6.6 \rceil = 14$ f
    - 期望 $\bar{C} = \text{getAvg}(1, 6.6) = 4.321$ f
- 冷却均值 $\bar{f} = 7 + 4.321 = 11.321$ f $\rightarrow 0.1887$ s
- 游戏显示 $t_\text{tooltip} = 2 \times 0.0495 + \frac{3}{60} = 0.15$ s

冲锋枪 T1 (-50% 攻速)

- 冷却帧 $w = \lfloor 4 \times (1 + 0.5)\rfloor = 6$ f
- 回弹时长 $r = 0.05$ s, $\text{tween}(r) = 4$ f
- 回弹动画 $f_\text{recoil} = 2 \times 4 - 1 = 7$ f
- 随机分布 $\Delta = \min(\frac{6 \times 6}{5}, 5 \times 6) = 7.2$
    - $C \sim \mathcal{U}(1, 13.2)$ f
    - 最小值 $\text{min} = 7 + \lfloor 1 \rfloor + 1 = 9$ f
    - 最大值 $\text{max} = 7 + \lceil 13.2 \rceil = 21$ f
    - 期望 $\bar{C} = \text{getAvg}(1, 13.2) = 7.606$ f
- 冷却均值 $\bar{f} = 7 + 7.606 = 14.606$ f $\rightarrow 0.2433$ s
- 游戏显示 $t_\text{tooltip} = 2 \times 0.05 + \frac{6}{60} = 0.20$ s

短斧 T1

- 冷却帧 $w = \lfloor\frac{9}{1}\rfloor = 9$ f
- 回弹时长 (前摇动画) $r = \frac{0.1}{1} = 0.1$ s
    - $\text{tween}(r) = \lfloor 0.1 \times 60\rfloor + 2 = 8$ f
- 范围系数 $\text{rangeFactor} = \frac{125}{70} = 1.7857$
- 挥砍动画 $t_\text{atk} = \max(0.01, 0.2 - 0) + 1.7857 \times 0.15 = 0.2 + 0.2679 = 0.4679$ s
    - $\text{tween}(\frac{t_\text{atk}}{4}) = \lfloor 0.4679/4 \times 60\rfloor + 2 = 9$ f
- 后摇动画 $t_\text{back} = \frac{0.2}{1 + 0} = 0.2$ s
    - $\text{tween}(t_\text{back}) = \lfloor 0.2 \times 60\rfloor + 2 = 14$ f
- 攻击间隔 $f = 8 + 14 + 2 \times 9 - 1 = 39$ f
- 随机分布 $\Delta = \min(\frac{6 \times 9}{5}, 5 \times 6) = 10.8$
    - $C \sim \mathcal{U}(1, 19.8)$ f
    - 最小值 $\text{min} = 39 + \lfloor 1 \rfloor + 1 = 41$ f
    - 最大值 $\text{max} = 39 + \lceil 19.8 \rceil = 59$ f
    - 期望 $\bar{C} = \text{getAvg}(1, 19.8) = 10.904$ f
- 冷却均值 $\bar{f} = 39 + 10.904 = 49.904$ f $\rightarrow 0.8317$ s
- 游戏显示 $t_\text{tooltip} = 0.1 + 0.2 + 0.4679/2 + \frac{9}{60} = 0.68$ s

短斧 T1 (+1%攻速)

- 冷却帧 $w = \lfloor\frac{9}{1.01}\rfloor = 8$ f
- 回弹时长 (前摇动画) $r = \frac{0.1}{1.01} = 0.099$ s
    - $\text{tween}(r) = 7$ f
- 范围系数 $\text{rangeFactor} = \frac{125}{70(1+0.01/3)} = 1.7798$
- 挥砍动画 $t_\text{atk} = \max(0.01, 0.2 - 0.01/10) + 1.7798 \times 0.15 = 0.199 + 0.2669 = 0.4659$ s
    - $\text{tween}(\frac{t_\text{atk}}{4}) = 8$ f
- 后摇动画 $t_\text{back} = \frac{0.2}{1 + 0.01 \times 3} = 0.1941$ s
    - $\text{tween}(t_\text{back}) = 13$ f
- 攻击间隔 $f = 7 + 13 + 2 \times 8 - 1 = 35$ f
- 随机分布 $\Delta = \min(\frac{6 \times 8}{5}, 5 \times 6) = 9.6$
    - $C \sim \mathcal{U}(1, 17.6)$ f
    - 最小值 $\text{min} = 35 + \lfloor 1 \rfloor + 1 = 37$ f
    - 最大值 $\text{max} = 35 + \lceil 17.6 \rceil = 53$ f
    - 期望 $\bar{C} = \text{getAvg}(1, 17.6) = 9.807$ f
- 冷却均值 $\bar{f} = 35 + 9.807 = 44.807$ f $\rightarrow 0.7468$ s
- 游戏显示 $t_\text{tooltip} = 0.099 + 0.1941 + 0.4659/2 + \frac{8}{60} = 0.66$ s

短斧 T1 (+1%攻速 +1范围)

- 冷却帧 $w = 8$ f
- 回弹时长 (前摇动画) $r = 0.099$ s, $\text{tween}(r) = 7$ f
- 范围系数 $\text{rangeFactor} = \frac{125.5}{70(1+0.01/3)} = 1.7869$
- 挥砍动画 $t_\text{atk} = \max(0.01, 0.2 - 0.01/10) + 1.7869 \times 0.15 = 0.467$ s
    - $\text{tween}(\frac{t_\text{atk}}{4}) = 9$ f
- 后摇动画 $t_\text{back} = 0.1941$ s, $\text{tween}(t_\text{back}) = 13$ f
- 攻击间隔 $f = 7 + 13 + 2 \times 9 - 1 = 37$ f
- 随机分布 $\Delta = \min(\frac{6 \times 8}{5}, 5 \times 6) = 9.6$
    - $C \sim \mathcal{U}(1, 17.6)$ f
    - 最小值 $\text{min} = 37 + \lfloor 1 \rfloor + 1 = 39$ f
    - 最大值 $\text{max} = 37 + \lceil 17.6 \rceil = 55$ f
    - 期望 $\bar{C} = \text{getAvg}(1, 17.6) = 9.807$ f
- 冷却均值 $\bar{f} = 37 + 9.807 = 46.807$ f $\rightarrow 0.7801$ s
- 游戏显示 $t_\text{tooltip} = 0.099 + 0.1941 + 0.467/2 + \frac{9}{60} = 0.68$ s

| 武器 | 攻速 | 范围 | 冷却均值 (s) | 游戏显示 (s) | 最小 - 最大范围 (f) | DPS 差距 |
| --- | --- | --- | --- | --- | --- | --- |
| 冲锋枪 T1 | 0% | 0 | 0.2068 | 0.17 | 9 - 16 | - |
| 冲锋枪 T1 | +1% | 0 | 0.1887 | 0.15 | 9 - 14 | +9.6% |
| 冲锋枪 T1 | -50% | 0 | 0.2433 | 0.20 | 9 - 21 | -15.2% |
| 短斧 T1 | 0% | 0 | 0.8317 | 0.68 | 41 - 59 | - |
| 短斧 T1 | +1% | 0 | 0.7468 | 0.66 | 37 - 53 | +11.4% |
| 短斧 T1 | +1% | +1 | 0.7801 | 0.68 | 39 - 55 | +6.6% |

攻速的收益很难定性分析，但是绝大多数武器的正攻速收益都没有明显的衰减（+100% 攻速的 DPS 收益一般在 +80% ~ +110% 之间，+200% 攻速的 DPS 收益一般在 +140% 以上。这不适用于冲锋枪或者更快的远程武器，它们有比较明确的攻速断点），而负攻速的惩罚也不太严重（-100% 攻速的 DPS 变化一般在 -50% ~ -20% 之间）。

至于范围对近战武器的影响，+200 范围属性的 DPS 变化在 -4% ~ -14% 之间，-200 范围属性的 DPS 收益在 +5% ~ +20% 之间。

**推荐使用土豆兄弟图鉴 - [mojimoon.top](https://brotato.mojimoon.top/) 进行准确的冷却计算。**

"""
绘制武器冷却帧 w(1..50) 变化时，随机延迟的期望与基准 w/60 的关系图。

左轴（折线）：
  - 期望秒数  E[ceil(C)]/60   （get_avg_attack_duration 取整均值，与 codex 一致）— 实线
  - 基准秒数  w/60            — 实线
  - 随机冷却下界 lo/60、上界 hi/60  — 两条虚线
右轴（柱状）：
  - 期望与基准之差 = E[ceil(C)]/60 - w/60（秒），y 轴上限压到约 0.12s

计算口径与 codex/src/store/codexStore.js 完全一致：
  - 攻速 = 0%  =>  wcf = w
  - Δ = min(weapon_count * wcf / 5, weapon_count * 5)，weapon_count = 6
  - 随机冷却帧 C ~ U( max(1, wcf-Δ), wcf+Δ )
  - 期望帧数 = E[ceil(C)]（game 按整数帧倒数 = 对连续随机值取 ceil）
只使用 getAvg()，不使用天真均匀平均。
"""

import math
import seaborn as sns
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sns.set_theme(style="whitegrid", context="talk",
              rc={"axes.edgecolor": "#444444", "font.family": "DejaVu Sans"})


def get_avg_attack_duration(min_cd, max_cd):
    """原样移植 codexStore.js 的 getAvgAttackDuration：返回 ceil(均匀值) 的期望帧数。"""
    if max_cd <= min_cd:
        return max_cd
    tri = lambda v: v * (v + 1) / 2
    ceil_min = math.ceil(min_cd)
    floor_max = math.floor(max_cd)
    return (
        (ceil_min - min_cd) * ceil_min
        + tri(floor_max)
        - tri(ceil_min)
        + (max_cd - floor_max) * math.ceil(max_cd)
    ) / (max_cd - min_cd)


WEAPON_COUNT = 6
FPS = 60


def compute(w):
    wcf = w  # 0% 攻速
    delta = min(WEAPON_COUNT * wcf / 5.0, WEAPON_COUNT * 5.0)
    lo = max(1, wcf - delta)
    hi = wcf + delta
    avg_frames = get_avg_attack_duration(lo, hi)
    exp_sec = avg_frames / FPS
    base_sec = wcf / FPS
    return delta, lo, hi, avg_frames, exp_sec, base_sec, exp_sec - base_sec


def main():
    ws = np.arange(1, 51)
    exp_sec, base_sec, diff_sec, lo_sec, hi_sec = [], [], [], [], []
    for w in ws:
        delta, lo, hi, avg_frames, e, b, d = compute(w)
        exp_sec.append(e)
        base_sec.append(b)
        diff_sec.append(d)
        lo_sec.append(lo / FPS)
        hi_sec.append(hi / FPS)

    palette = sns.color_palette("deep")
    X_MIN, X_MAX = 0.5, 50.5

    fig, ax1 = plt.subplots(figsize=(10, 5.6))

    # 左轴：两条实线（期望 / 基准）+ 两条虚线（最小 / 最大）
    ax1.plot(ws, exp_sec, color=palette[0], lw=2.6, label="E[random delay] / 60  (getAvg)")
    ax1.plot(ws, base_sec, color=palette[1], lw=2.4, label="baseline w / 60")
    ax1.plot(ws, lo_sec, color=palette[2], lw=1.8, ls="--", alpha=0.9, label="min lo / 60")
    ax1.plot(ws, hi_sec, color=palette[3], lw=1.8, ls="--", alpha=0.9, label="max hi / 60")
    ax1.set_xlabel("weapon cooldown frames w")
    ax1.set_ylabel("cooldown (s)", color=palette[0])
    ax1.tick_params(axis="y", labelcolor=palette[0])
    ax1.set_xlim(X_MIN, X_MAX)
    ax1.set_ylim(0, max(hi_sec) * 1.10)

    # 右轴：柱状差值（上限压到 ~0.12s）
    ax2 = ax1.twinx()
    ax2.bar(ws, diff_sec, color=palette[4], alpha=0.4, width=0.8,
            label="difference (E - baseline)")
    ax2.set_ylabel("difference (s)", color=palette[4])
    ax2.tick_params(axis="y", labelcolor=palette[4])
    ax2.set_xlim(X_MIN, X_MAX)          # 与左轴同一横轴
    ax2.set_ylim(0, 0.24)
    ax2.set_xticks([])                  # 不重复画横轴刻度，避免「两套横轴」
    ax2.grid(False)
    # 移动图层到最后
    ax2.set_zorder(ax1.get_zorder() + 1)

    # Δ 封顶标注
    ax1.axvline(25, color="#888888", lw=1.0, ls=":")
    ax1.text(25.4, ax1.get_ylim()[1] * 0.90, "w=25: Δ caps at 0.05s",
             color="#555555", fontsize=11)

    # 图例放左上角（低 w 处两线都低，留白大）
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=10.5, framealpha=0.95)

    plt.title("Randomized delay expectation vs. tooltip (6 weapons)", pad=14)
    fig.tight_layout()
    out = "cooldown_deviation.png"
    fig.savefig(out, dpi=130)
    print("saved", out)

    # 关键点表格
    # print(f"{'w':>3} {'Δ':>6} {'[lo,hi]':>14} {'E[ceil]':>8} {'期望(s)':>8} "
    #       f"{'基准(s)':>8} {'差值(s)':>9} {'差值%':>8}")
    # for w in (1, 2, 4, 9, 15, 25, 30, 40, 50):
    #     delta, lo, hi, avg_frames, e, b, d = compute(w)
    #     print(f"{w:>3} {delta:>6.1f} [{lo:>4.1f},{hi:>5.1f}] {avg_frames:>8.3f} "
    #           f"{e:>8.4f} {b:>8.4f} {d:>9.4f} {d/b*100:>7.2f}%")


if __name__ == "__main__":
    main()

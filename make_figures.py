# Creates the figures used in README.md from the files in data/.
# Run from the main folder: python make_figures.py
# Note: the smile figure also needs data/SPX_2026-10-26_1030_iv.csv (created by notebook 03).
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import sys; sys.path.insert(0, ".")
from functions import svi, black_price

BLUE, ORANGE, INK, MUTE, GRID = "#2a78d6", "#eb6834", "#222222", "#6b6b6b", "#e6e6e6"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": "#9a9a9a", "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titleweight": "bold", "axes.titlesize": 11})
S_ = "SPX_2026-10-26_1030"
surf = pd.read_csv(f"data/{S_}_surface.csv").sort_values("T").reset_index(drop=True)
iv = pd.read_csv(f"data/{S_}_iv.csv")
pc = ["a", "b", "rho", "m", "sig"]; T_list = surf["T"].values

# ---------- 1. 3D surface
cmap = LinearSegmentedColormap.from_list("blues", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
k = np.linspace(-0.6, 0.2, 80); use = surf[(surf["T"] >= 0.1) & (surf["T"] <= 3.1)]
K_, T_ = np.meshgrid(k, use["T"].values)
Z = np.array([np.sqrt(svi(k, *r[pc]) / r["T"]) for _, r in use.iterrows()]) * 100
fig = plt.figure(figsize=(9, 6.2)); ax = fig.add_subplot(projection="3d")
ax.plot_surface(K_, T_, Z, cmap=cmap, edgecolor="none", rstride=1, cstride=1, antialiased=True)
ax.set_xlabel("log-moneyness  k = ln(K/F)", labelpad=8); ax.set_ylabel("maturity T (years)", labelpad=8)
ax.set_zlabel("implied volatility (%)", labelpad=6); ax.view_init(elev=22, azim=-125); ax.set_zlim(10, np.ceil(Z.max() / 5) * 5)
ax.xaxis.pane.fill = ax.yaxis.pane.fill = ax.zaxis.pane.fill = False
ax.set_title("SPX implied volatility surface (SVI), 26 October 2026", pad=4)
fig.tight_layout(); fig.savefig("figures/vol_surface.png", dpi=160, bbox_inches="tight"); plt.close(fig)

# ---------- 2. smile fits vs bid/ask
targets = [1/12, 0.43, 1.0, 2.0]
fig, axes = plt.subplots(1, 4, figsize=(15, 3.9), sharey=False)
for ax, t in zip(axes, targets):
    row = surf.iloc[(surf["T"] - t).abs().argmin()]
    q = iv[iv["expiry"] == row["expiry"]].sort_values("k")
    q = q[(q["k"] > -0.7) & (q["k"] < 0.25)]
    med = q["iv"].rolling(5, center=True).median(); keep = ~((q["iv"] - med).abs() > 0.01)
    g, bad = q[keep], q[~keep]
    ax.vlines(g["k"], g["iv_bid"] * 100, g["iv_ask"] * 100, color="#8c8c8c", lw=1.4)
    ax.plot(g["k"], g["iv"] * 100, "o", color="#8c8c8c", ms=2.5, label="market (mid, bid–ask bar)")
    if len(bad): ax.plot(bad["k"], bad["iv"] * 100, "o", mfc="none", mec=ORANGE, ms=5, label="removed (stale)")
    kk = np.linspace(q["k"].min(), q["k"].max(), 300)
    ax.plot(kk, np.sqrt(svi(kk, *row[pc]) / row["T"]) * 100, color=BLUE, lw=2, label="SVI fit")
    ax.set_title(f"expiry {row['expiry']}  (T = {row['T']:.2f})")
    ax.set_xlabel("log-moneyness k"); ax.grid(color=GRID, lw=0.7)
axes[0].set_ylabel("implied volatility (%)")
h, l = [], []
for ax in axes:
    for hh, ll in zip(*ax.get_legend_handles_labels()):
        if ll not in l: h.append(hh); l.append(ll)
fig.legend(h, l, frameon=False, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.06))
fig.tight_layout(); fig.savefig("figures/smile_fits.png", dpi=160, bbox_inches="tight"); plt.close(fig)

# ---------- 3. constant vol vs SVI at 1 year
def total_variance(kv, T):
    i = min(max(np.searchsorted(T_list, T) - 1, 0), len(T_list) - 2); T1, T2 = T_list[i], T_list[i+1]
    w1 = svi(kv, *surf.loc[i, pc]); w2 = svi(kv, *surf.loc[i+1, pc]); return w1 + (T - T1)/(T2 - T1)*(w2 - w1)
T = 1.0; F = np.exp(np.interp(T, T_list, np.log(surf["F"]))); r = np.interp(T, T_list, surf["r"]); S = surf["spot"].iloc[0]
atm = np.sqrt(total_variance(0.0, T) / T)
mny = np.linspace(0.6, 1.2, 200); vs = np.sqrt(total_variance(np.log(mny * S / F), T) / T) * 100
legs = [("Put 90%", 0.9, "P"), ("Put 70%", 0.7, "P"), ("Call 110%", 1.1, "C")]
rows = []
for name, m, ty in legs:
    Kx = m * S; v = np.sqrt(total_variance(np.log(Kx / F), T) / T)
    rows.append((name, m, v, black_price(F, Kx, T, r, atm, ty), black_price(F, Kx, T, r, v, ty)))
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.6), gridspec_kw={"width_ratios": [1.25, 1]})
a1.plot(mny * 100, vs, color=BLUE, lw=2, label="SVI surface")
a1.axhline(atm * 100, color=ORANGE, lw=2, ls="--", label=f"constant vol {atm*100:.2f}%")
for name, m, v, *_ in rows:
    a1.plot(m * 100, v * 100, "o", color=BLUE, ms=6); a1.annotate(f"{name}\n{v*100:.1f}%", (m * 100, v * 100),
        textcoords="offset points", xytext=(6, -26) if m > 1 else (6, 6), fontsize=9, color=INK)
a1.set_xlabel("strike (% of spot)"); a1.set_ylabel("implied volatility (%)"); a1.grid(color=GRID, lw=0.7)
a1.set_title("1-year volatility: market skew against a constant volatility"); a1.legend(frameon=False)
x = np.arange(len(rows)); wbar = 0.38
b1 = a2.bar(x - wbar/2, [r_[3] for r_ in rows], wbar, color=ORANGE, label="constant vol (Black-Scholes)")
b2 = a2.bar(x + wbar/2, [r_[4] for r_ in rows], wbar, color=BLUE, label="SVI surface")
for b in list(b1) + list(b2):
    a2.annotate(f"{b.get_height():.1f}", (b.get_x() + b.get_width()/2, b.get_height()), ha="center",
                va="bottom", fontsize=9, xytext=(0, 2), textcoords="offset points", color=INK)
a2.set_xticks(x, [r_[0] for r_ in rows]); a2.set_ylabel("price (index points)")
a2.set_title("1-year option prices"); a2.legend(frameon=False, loc="upper left"); a2.grid(axis="y", color=GRID, lw=0.7)
fig.tight_layout(); fig.savefig("figures/constant_vs_svi.png", dpi=160, bbox_inches="tight"); plt.close(fig)
for r_ in rows: print(r_[0], round(r_[2]*100, 2), "const %.2f svi %.2f" % (r_[3], r_[4]))
print("atm", atm, "F", F, "r", r)

# ---------- 4. two surfaces side by side, and what changed
other = pd.read_csv("data/SPX_2026-11-20_1210_surface.csv").sort_values("T").reset_index(drop=True)
dates = {"26 October 2026": surf, "20 November 2026": other}
col = {"26 October 2026": BLUE, "20 November 2026": ORANGE}

def ivol(s, kv, T):
    TL = s["T"].values; i = min(max(np.searchsorted(TL, T) - 1, 0), len(TL) - 2)
    w1 = svi(kv, *s.loc[i, pc]); w2 = svi(kv, *s.loc[i + 1, pc])
    return np.sqrt((w1 + (T - TL[i]) / (TL[i + 1] - TL[i]) * (w2 - w1)) / T)

kg = np.linspace(-0.6, 0.2, 70); Tg = np.linspace(0.1, 2.0, 70); KM, TM = np.meshgrid(kg, Tg)
Zs = {d: np.array([ivol(s, kg, T) * 100 for T in Tg]) for d, s in dates.items()}
zmin, zmax = min(z.min() for z in Zs.values()), max(z.max() for z in Zs.values())
fig = plt.figure(figsize=(15, 6.2))
for n, (d, s) in enumerate(dates.items()):
    ax = fig.add_subplot(1, 2, n + 1, projection="3d")
    sf = ax.plot_surface(KM, TM, Zs[d], cmap=cmap, vmin=zmin, vmax=zmax, edgecolor="none", antialiased=True)
    ax.set_zlim(np.floor(zmin), np.ceil(zmax)); ax.view_init(elev=22, azim=-125)
    ax.set_xlabel("log-moneyness k", labelpad=6); ax.set_ylabel("maturity T (years)", labelpad=6)
    ax.set_zlabel("implied volatility (%)", labelpad=4)
    ax.xaxis.pane.fill = ax.yaxis.pane.fill = ax.zaxis.pane.fill = False
    ax.set_title(f"{d}  ·  S&P 500 at {s['spot'].iloc[0]:,.0f}", pad=2)
cb = fig.colorbar(sf, ax=fig.axes, shrink=0.6, pad=0.02); cb.set_label("implied volatility (%)")
fig.suptitle("SPX implied volatility surface before and after the November fall", fontweight="bold", y=0.97)
fig.savefig("figures/vol_surface_comparison.png", dpi=150, bbox_inches="tight"); plt.close(fig)

fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.4))
Tt = np.linspace(0.1, 2.0, 80); mg = np.linspace(0.6, 1.15, 150)
for d, s in dates.items():
    a1.plot(Tt, [ivol(s, 0.0, T) * 100 for T in Tt], color=col[d], lw=2, label=d)
    a2.plot(mg * 100, ivol(s, np.log(mg), 1.0) * 100, color=col[d], lw=2, label=d)
a1.set_title("At-the-money volatility by maturity: the term structure inverts")
a1.set_xlabel("maturity T (years)"); a1.set_ylabel("implied volatility (%)")
a2.set_title("1-year smile: the level rises, the shape stays")
a2.set_xlabel("strike (% of forward)"); a2.set_ylabel("implied volatility (%)")
for a in (a1, a2): a.grid(color=GRID, lw=0.7); a.legend(frameon=False)
fig.tight_layout(); fig.savefig("figures/surface_change.png", dpi=160, bbox_inches="tight"); plt.close(fig)

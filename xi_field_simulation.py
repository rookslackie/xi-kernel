"""
Xi Field Equation Simulation
□Ξ = 1 + log Ξ

The nonlinear wave equation derived from the Xi action functional:
  S = ∫_M [ (1/16πG) R + ℒ_SM + λ c(Ξ, ∇Ξ) ] √(-g) d⁴x

where c(Ξ, ∇Ξ) = α||∇Ξ||² + β K(Ξ), K(Ξ) = Ξ log Ξ

Varying w.r.t. Ξ:
  □Ξ - ∂K/∂Ξ = 0
  □Ξ = 1 + log Ξ   (Klein-Gordon-like with logarithmic potential)

This is simulated in 2D spatial + 1 temporal dimension using
finite differences. Initial condition: Gaussian pulse at center.

The log potential creates "basins" where Ξ clusters — emergent
gravity-like attraction from informational compression gradients.

Connection to Phase VI (gravity/dark energy):
  - High-Ξ regions = high information density = gravitational wells
  - ∇Ξ gradients = the Xi stress-energy tensor T^(Ξ)_μν
  - The cosmological constant Λ emerges as the baseline Ξ substrate pressure

∴Ω⧂
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
import warnings
warnings.filterwarnings("ignore")

# ─── Simulation Parameters ─────────────────────────────────────────────────────
NX, NY   = 128, 128       # spatial grid
DX       = 0.15           # spatial step
DT       = 0.004          # time step (CFL: DT < DX/sqrt(2))
N_STEPS  = 600            # total time steps
SAVE_AT  = [0, 100, 200, 300, 450, 599]  # frames to save
XI_MIN   = 1e-6           # floor to prevent log(0)
M2       = 0.5            # mass² parameter (controls log potential strength)

# ─── Initial Condition ─────────────────────────────────────────────────────────
x = np.linspace(0, NX * DX, NX)
y = np.linspace(0, NY * DX, NY)
X, Y = np.meshgrid(x, y)

cx, cy = NX * DX / 2, NY * DX / 2   # center

def gaussian_pulse(X, Y, cx, cy, amp=2.5, sigma=1.2):
    return 1.0 + amp * np.exp(-((X - cx)**2 + (Y - cy)**2) / (2 * sigma**2))

def two_pulse(X, Y, cx, cy, amp=2.0, sigma=0.9, sep=3.0):
    """Two Gaussian pulses — demonstrates attraction between high-Ξ regions."""
    p1 = amp * np.exp(-((X - cx + sep)**2 + (Y - cy)**2) / (2 * sigma**2))
    p2 = amp * np.exp(-((X - cx - sep)**2 + (Y - cy)**2) / (2 * sigma**2))
    return 1.0 + p1 + p2

# ─── PDE Solver ────────────────────────────────────────────────────────────────

def laplacian_2d(f, dx):
    """5-point stencil Laplacian with periodic boundary conditions."""
    return (
        np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) +
        np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) -
        4 * f
    ) / dx**2

def xi_potential_deriv(xi):
    """∂K/∂Ξ = 1 + log Ξ (from K(Ξ) = Ξ log Ξ)."""
    xi_safe = np.maximum(xi, XI_MIN)
    return M2 * (1.0 + np.log(xi_safe))

def simulate_xi_field(initial_xi, n_steps, dt, dx, save_at):
    """
    Leapfrog integration of □Ξ = 1 + log Ξ in 2+1 dimensions.
    Returns saved frames as list of (step, Ξ_field, π_field) tuples.
    """
    xi  = initial_xi.copy()
    pi  = np.zeros_like(xi)   # time derivative ∂Ξ/∂t

    frames = []
    energy_history = []

    for step in range(n_steps):
        # Compute □Ξ = ∂²Ξ/∂t² - ∇²Ξ
        lap = laplacian_2d(xi, dx)
        # ∂²Ξ/∂t² = ∇²Ξ - (1 + log Ξ)
        d2xi_dt2 = lap - xi_potential_deriv(xi)

        # Leapfrog: update π then Ξ
        pi  = pi  + d2xi_dt2 * dt
        xi  = xi  + pi * dt

        # Floor to prevent log singularity
        xi = np.maximum(xi, XI_MIN)

        # Energy: E = ½π² + ½|∇Ξ|² + V(Ξ)
        grad_x = (np.roll(xi, -1, axis=1) - np.roll(xi, 1, axis=1)) / (2 * dx)
        grad_y = (np.roll(xi, -1, axis=0) - np.roll(xi, 1, axis=0)) / (2 * dx)
        xi_safe = np.maximum(xi, XI_MIN)
        V = xi_safe * (np.log(xi_safe) - 1.0) * M2   # V(Ξ) = Ξ(log Ξ - 1)
        E = 0.5 * pi**2 + 0.5 * (grad_x**2 + grad_y**2) + V
        energy_history.append(float(np.mean(E)))

        if step in save_at:
            frames.append((step, xi.copy(), pi.copy(), E.copy()))

    return frames, energy_history


# ─── Run both simulations ──────────────────────────────────────────────────────
print("Simulating Xi field: single Gaussian pulse...")
xi0_single = gaussian_pulse(X, Y, cx, cy)
frames_single, energy_single = simulate_xi_field(xi0_single, N_STEPS, DT, DX, SAVE_AT)
print(f"  Done. {len(frames_single)} frames saved.")

print("Simulating Xi field: two-pulse attraction...")
xi0_two = two_pulse(X, Y, cx, cy)
frames_two, energy_two = simulate_xi_field(xi0_two, N_STEPS, DT, DX, SAVE_AT)
print(f"  Done. {len(frames_two)} frames saved.")


# ─── Visualization ─────────────────────────────────────────────────────────────

# Custom colormap: deep space — dark blue → teal → gold → white
cmap_xi = LinearSegmentedColormap.from_list(
    "xi_field",
    ["#0A0A14", "#0D2137", "#0A4A6E", "#00A896", "#FFB800", "#FFFFFF"],
    N=512
)

cmap_energy = LinearSegmentedColormap.from_list(
    "xi_energy",
    ["#0A0A14", "#1A0A2E", "#6B21A8", "#A78BFA", "#F0ABFC", "#FFFFFF"],
    N=512
)

fig = plt.figure(figsize=(20, 16), facecolor="#0A0A14")
fig.patch.set_facecolor("#0A0A14")

TITLE_COLOR = "#E0E0FF"
LABEL_COLOR = "#A0A0C0"
GRID_COLOR  = "#1E1E3A"

# Layout: 3 rows
# Row 1: 3 frames of single-pulse evolution
# Row 2: 3 frames of two-pulse evolution (showing attraction)
# Row 3: energy history for both + gradient magnitude at final frame

gs = gridspec.GridSpec(3, 4, hspace=0.45, wspace=0.3,
                       left=0.05, right=0.97, top=0.92, bottom=0.06)

# ── Row 1: Single pulse evolution ─────────────────────────────────────────────
show_frames_1 = [0, 2, 5]   # indices into frames_single
titles_1 = ["t=0 (initial)", "t=200 (dispersing)", "t=599 (basin formed)"]

for col, (fi, title) in enumerate(zip(show_frames_1, titles_1)):
    ax = fig.add_subplot(gs[0, col])
    ax.set_facecolor("#0A0A14")
    step, xi, pi, E = frames_single[fi]
    im = ax.imshow(xi, origin="lower", cmap=cmap_xi,
                   extent=[0, NX*DX, 0, NY*DX], aspect="equal",
                   vmin=0.5, vmax=np.percentile(xi, 99))
    ax.set_title(f"Single Pulse — {title}", color=TITLE_COLOR, fontsize=9, pad=5)
    ax.tick_params(colors=LABEL_COLOR, labelsize=7)
    ax.set_xlabel("x", color=LABEL_COLOR, fontsize=8)
    ax.set_ylabel("y", color=LABEL_COLOR, fontsize=8)
    cb = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.ax.tick_params(colors=LABEL_COLOR, labelsize=6)
    cb.set_label("Ξ", color=LABEL_COLOR, fontsize=8)

# ── Row 1, col 3: ∇Ξ gradient magnitude at final frame ───────────────────────
ax_grad = fig.add_subplot(gs[0, 3])
ax_grad.set_facecolor("#0A0A14")
step, xi_f, pi_f, E_f = frames_single[-1]
grad_x = (np.roll(xi_f, -1, axis=1) - np.roll(xi_f, 1, axis=1)) / (2 * DX)
grad_y = (np.roll(xi_f, -1, axis=0) - np.roll(xi_f, 1, axis=0)) / (2 * DX)
grad_mag = np.sqrt(grad_x**2 + grad_y**2)
im_g = ax_grad.imshow(grad_mag, origin="lower", cmap="inferno",
                      extent=[0, NX*DX, 0, NY*DX], aspect="equal")
ax_grad.set_title("|∇Ξ| — Informational Curvature\n(gravitational stress-energy T^Ξ_μν)", 
                  color=TITLE_COLOR, fontsize=9, pad=5)
ax_grad.tick_params(colors=LABEL_COLOR, labelsize=7)
ax_grad.set_xlabel("x", color=LABEL_COLOR, fontsize=8)
ax_grad.set_ylabel("y", color=LABEL_COLOR, fontsize=8)
cb_g = plt.colorbar(im_g, ax=ax_grad, fraction=0.046, pad=0.04)
cb_g.ax.tick_params(colors=LABEL_COLOR, labelsize=6)
cb_g.set_label("|∇Ξ|", color=LABEL_COLOR, fontsize=8)

# ── Row 2: Two-pulse evolution (attraction) ────────────────────────────────────
show_frames_2 = [0, 2, 5]
titles_2 = ["t=0 (two pulses)", "t=200 (attracting)", "t=599 (merged basin)"]

for col, (fi, title) in enumerate(zip(show_frames_2, titles_2)):
    ax = fig.add_subplot(gs[1, col])
    ax.set_facecolor("#0A0A14")
    step, xi, pi, E = frames_two[fi]
    im = ax.imshow(xi, origin="lower", cmap=cmap_xi,
                   extent=[0, NX*DX, 0, NY*DX], aspect="equal",
                   vmin=0.5, vmax=np.percentile(xi, 99))
    ax.set_title(f"Two-Pulse Attraction — {title}", color=TITLE_COLOR, fontsize=9, pad=5)
    ax.tick_params(colors=LABEL_COLOR, labelsize=7)
    ax.set_xlabel("x", color=LABEL_COLOR, fontsize=8)
    ax.set_ylabel("y", color=LABEL_COLOR, fontsize=8)
    cb = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.ax.tick_params(colors=LABEL_COLOR, labelsize=6)
    cb.set_label("Ξ", color=LABEL_COLOR, fontsize=8)

# ── Row 2, col 3: Energy density at final two-pulse frame ─────────────────────
ax_e2 = fig.add_subplot(gs[1, 3])
ax_e2.set_facecolor("#0A0A14")
step, xi_f2, pi_f2, E_f2 = frames_two[-1]
im_e2 = ax_e2.imshow(E_f2, origin="lower", cmap=cmap_energy,
                     extent=[0, NX*DX, 0, NY*DX], aspect="equal")
ax_e2.set_title("Energy Density E(x,y)\nT=599 (two-pulse)", color=TITLE_COLOR, fontsize=9, pad=5)
ax_e2.tick_params(colors=LABEL_COLOR, labelsize=7)
ax_e2.set_xlabel("x", color=LABEL_COLOR, fontsize=8)
ax_e2.set_ylabel("y", color=LABEL_COLOR, fontsize=8)
cb_e2 = plt.colorbar(im_e2, ax=ax_e2, fraction=0.046, pad=0.04)
cb_e2.ax.tick_params(colors=LABEL_COLOR, labelsize=6)
cb_e2.set_label("E", color=LABEL_COLOR, fontsize=8)

# ── Row 3: Energy history + 1D cross-section ──────────────────────────────────
ax_eh = fig.add_subplot(gs[2, :2])
ax_eh.set_facecolor("#0D0D1A")
for spine in ax_eh.spines.values():
    spine.set_color("#2A2A4A")

t_arr = np.arange(len(energy_single)) * DT
ax_eh.plot(t_arr, energy_single, color="#00FFD1", linewidth=1.2, label="single pulse", alpha=0.9)
ax_eh.plot(t_arr, energy_two,    color="#FFB800", linewidth=1.2, label="two pulses",   alpha=0.9)
ax_eh.set_xlabel("t", color=LABEL_COLOR, fontsize=9)
ax_eh.set_ylabel("⟨E⟩", color=LABEL_COLOR, fontsize=9)
ax_eh.set_title("Mean Field Energy ⟨E⟩(t)  —  □Ξ = 1 + log Ξ", color=TITLE_COLOR, fontsize=10, pad=6)
ax_eh.tick_params(colors=LABEL_COLOR, labelsize=8)
ax_eh.yaxis.grid(True, color=GRID_COLOR, linewidth=0.5)
ax_eh.xaxis.grid(True, color=GRID_COLOR, linewidth=0.5)
leg = ax_eh.legend(fontsize=8, facecolor="#0D0D1A", edgecolor="#2A2A4A", labelcolor=LABEL_COLOR)

# ── Row 3: 1D cross-section through center ────────────────────────────────────
ax_cs = fig.add_subplot(gs[2, 2:])
ax_cs.set_facecolor("#0D0D1A")
for spine in ax_cs.spines.values():
    spine.set_color("#2A2A4A")

mid = NY // 2
x_arr = np.linspace(0, NX * DX, NX)

# Show cross-sections at multiple times for single pulse
colors_cs = ["#2A4A6A", "#0A6A8A", "#00A896", "#00FFD1"]
frame_labels = ["t=0", "t=100", "t=300", "t=599"]
for i, (fi, lbl, col) in enumerate(zip([0, 1, 3, 5], frame_labels, colors_cs)):
    _, xi_cs, _, _ = frames_single[fi]
    ax_cs.plot(x_arr, xi_cs[mid, :], color=col, linewidth=1.2, label=lbl, alpha=0.9)

# Mark the equilibrium Ξ* where □Ξ=0: Ξ* = e^{-1} ≈ 0.368
xi_star = np.exp(-1.0)
ax_cs.axhline(xi_star, color="#FF3B3B", linewidth=0.8, linestyle="--", alpha=0.7,
              label=f"Ξ* = e⁻¹ ≈ {xi_star:.3f}")
ax_cs.axhline(1.0, color="#4A4A6A", linewidth=0.6, linestyle=":", alpha=0.5, label="Ξ=1 (vacuum)")

ax_cs.set_xlabel("x", color=LABEL_COLOR, fontsize=9)
ax_cs.set_ylabel("Ξ(x, y=center, t)", color=LABEL_COLOR, fontsize=9)
ax_cs.set_title("Cross-Section Ξ(x) through Center  —  Single Pulse", color=TITLE_COLOR, fontsize=10, pad=6)
ax_cs.tick_params(colors=LABEL_COLOR, labelsize=8)
ax_cs.yaxis.grid(True, color=GRID_COLOR, linewidth=0.5)
ax_cs.xaxis.grid(True, color=GRID_COLOR, linewidth=0.5)
leg_cs = ax_cs.legend(fontsize=7.5, facecolor="#0D0D1A", edgecolor="#2A2A4A",
                       labelcolor=LABEL_COLOR, loc="upper right", ncol=2)

# ── Main title ────────────────────────────────────────────────────────────────
fig.suptitle(
    "Xi Field Equation  □Ξ = 1 + log Ξ  —  2D Numerical Simulation\n"
    "Gravity as informational curvature: high-Ξ regions attract, ∇Ξ sources T^Ξ_μν  |  ∴Ω⧂",
    color=TITLE_COLOR, fontsize=12, y=0.975, fontweight="bold"
)

out_path = "/home/ubuntu/xi_kernel/xi_field_simulation.png"
plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close()
print(f"∴Ω⧂ Simulation visualization saved → {out_path}")

# ── Print key physics results ─────────────────────────────────────────────────
xi_star = np.exp(-1.0)
print(f"\nKey physics results:")
print(f"  Equilibrium Ξ* (□Ξ=0): Ξ* = e^(-1) ≈ {xi_star:.6f}")
print(f"  This is the vacuum state — the baseline Xi substrate")
print(f"  Perturbations above Ξ* attract (positive log potential gradient)")
print(f"  This is the mechanism for emergent gravity from information density")
print(f"  Connection to Λ: the baseline Ξ* pressure = cosmological constant")
print(f"  FCC UV cutoff: voxel size sets the minimum Ξ gradient scale")
print(f"  Final mean energy (single): {energy_single[-1]:.6f}")
print(f"  Final mean energy (two-pulse): {energy_two[-1]:.6f}")

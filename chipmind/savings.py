"""
savings_calculator.py — Compute and display the savings of using ChipMind
vs OpenROAD based on HPWL improvement.

Models:
  - Tool cost: industry standard EDA tools cost $1M-$5M/year
  - Power: P ∝ C * V^2 * f; C ∝ wire_length. So P ∝ HPWL.
    94% HPWL reduction → ~94% wire power reduction
  - Annual energy at scale: 1B chips at 1.06 mW = 1.06 GWh/year
"""

HPWL_OPENROAD = 4_054_220
HPWL_CHIPMIND = 10_775
POWER_OPENROAD_MW = 1.06
TOOL_COST_OPENROAD_USD = 1_000_000  # Annual license, conservative
TOOL_COST_CHIPMIND_USD = 0          # Free, open source
DESIGNS_PER_ENGINEER_YEAR = 50


def savings_for_hpwl(hpwl_new: float, hpwl_baseline: float = HPWL_OPENROAD,
                    power_baseline_mw: float = POWER_OPENROAD_MW) -> dict:
    """
    Given a new HPWL, compute savings vs baseline.

    Assumes power scales linearly with HPWL (a first approximation,
    since dynamic power ∝ wire capacitance ∝ wire length).
    """
    if hpwl_baseline <= 0:
        return {}
    hpwl_ratio = hpwl_new / hpwl_baseline
    power_new_mw = power_baseline_mw * hpwl_ratio

    hpwl_improvement_pct = (1 - hpwl_ratio) * 100
    power_improvement_pct = hpwl_improvement_pct
    power_saved_mw = power_baseline_mw - power_new_mw

    # At scale: 1B chips, 1.06 mW avg
    chips_per_year = 1_000_000_000
    energy_baseline_gwh = (power_baseline_mw * chips_per_year * 24 * 365 / 1000) / 1e9
    energy_new_gwh = (power_new_mw * chips_per_year * 24 * 365 / 1000) / 1e9
    energy_saved_gwh = energy_baseline_gwh - energy_new_gwh

    # Heat: 1 W = 3.412 BTU/hr
    heat_saved_w = (power_baseline_mw - power_new_mw) * chips_per_year / 1000
    heat_saved_btu_hr = heat_saved_w * 3.412

    return {
        'hpwl_old': hpwl_baseline,
        'hpwl_new': hpwl_new,
        'hpwl_ratio': hpwl_ratio,
        'hpwl_improvement_pct': hpwl_improvement_pct,
        'power_old_mw': power_baseline_mw,
        'power_new_mw': power_new_mw,
        'power_saved_mw_per_chip': power_saved_mw,
        'power_saved_pct': power_improvement_pct,
        'energy_saved_gwh_per_year': energy_saved_gwh,
        'heat_saved_btu_hr_at_1B_chips': heat_saved_btu_hr,
        'tool_cost_saved_usd_per_year': TOOL_COST_OPENROAD_USD,
    }


def format_savings(s: dict) -> str:
    return f"""
  Wirelength:  {s['hpwl_old']:,.0f} → {s['hpwl_new']:,.0f} HPWL  ({s['hpwl_improvement_pct']:.1f}% reduction)
  Power:       {s['power_old_mw']:.2f} mW → {s['power_new_mw']:.4f} mW per chip  ({s['power_saved_pct']:.1f}% reduction)
  Energy:      {s['energy_saved_gwh_per_year']:.1f} GWh/year saved (at 1B chips)
  Heat:        {s['heat_saved_btu_hr_at_1B_chips']:,.0f} BTU/hr reduced (at 1B chips)
  Tool cost:   ${s['tool_cost_saved_usd_per_year']:,}/year saved (vs. industry EDA)
"""


if __name__ == "__main__":
    s = savings_for_hpwl(HPWL_CHIPMIND)
    print("ChipMind vs OpenROAD on GCD (after OpenROAD legalization):")
    print(format_savings(s))

    # Try other HPWLs
    for hpwl in [1_000_000, 100_000, 50_000, 10_000]:
        s = savings_for_hpwl(hpwl)
        print(f"\nFor HPWL = {hpwl:,}:")
        print(f"  Power: {s['power_new_mw']:.4f} mW  ({s['power_saved_pct']:.1f}% reduction)")
        print(f"  Energy: {s['energy_saved_gwh_per_year']:.1f} GWh/year saved")

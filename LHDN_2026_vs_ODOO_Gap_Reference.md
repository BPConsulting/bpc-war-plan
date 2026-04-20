# LHDN 2026 MTD Spec vs Odoo — Gap Reference
> Last updated: 21 April 2026
> Source: spesifikasi-kaedah-pengiraan-berkomputer-pcb-2026.pdf (01 Jan 2026)
> Modules: bpc19_intrix_payroll, BPC19_INTRIX_Statutory, BPC19_INTRIX_Employees
> Status: ALL VARIABLES AND CALCULATIONS RESOLVED (20 Apr 2026 session)

## TABLE 1: Variables — ALL DONE

| # | LHDN Var | Odoo location | Status |
|---|----------|---------------|--------|
| 1 | P (annual chargeable) | bpc_pcb() step 7 — full D+S+DU+SU+QC+LP | DONE |
| 2 | Y (YTD gross) | _bpc_ytd_taxable_income() | DONE |
| 3 | K (YTD EPF capped) | _bpc_ytd_line_sum('EPF_EE') + TP3 | DONE |
| 4 | Y1 (current gross) | _bpc_pcb_taxable_income() | DONE |
| 5 | K1 (current EPF) | epf_ee_amount parameter | DONE |
| 6 | Y2 (future est.) | = Y1 implicit | DONE |
| 7 | K2 (future EPF) | min([cap-K-K1-Kt]/n, K1) | DONE |
| 8 | Yt (bonus gross) | bpc_pcb_additional() | DONE |
| 9 | Kt (bonus EPF) | bpc_pcb_additional() | DONE |
| 10 | n, n+1 | 12-period, division correct | DONE |
| 11 | X (YTD MTD paid) | _bpc_ytd_line_sum('PCB') + TP3 | DONE |
| 12 | Z (YTD zakat) | _bpc_ytd_line_sum('ZAKAT') + TP3 | DONE |
| 13 | M, R (bracket) | hr.statutory.pcb | DONE |
| 14 | B Cat1&3 | hr.statutory.pcb.b_cat1_3 | DONE |
| 15 | B Cat2 | hr.statutory.pcb.b_cat2 | DONE |
| 16 | D (individual 9k) | bpc.statutory.variable | DONE |
| 17 | S (spouse 4k) | pcb_category=='2' | DONE |
| 18 | DU (disabled 7k) | handicapped field | DONE |
| 19 | SU (disabled spouse 6k) | spouse_disabled field | DONE |
| 20 | QC (children) | pcb_child_relief computed | DONE |
| 21 | Category 1/2/3 | pcb_category Selection | DONE |
| 22 | Tax region | tax_region Selection | DONE |
| 23 | Resident status | is_resident Boolean | DONE |
| 24 | Zakat monthly | zakat_monthly Float | DONE |
| 25-29 | TP3 x5 fields | tp3_taxable_gross/epf/pcb/zakat/deductions | DONE |
| 30-31 | TP1 LP/LP1 | bpc.employee.tp1.claim + helpers | DONE |

## TABLE 2: Calculations — ALL DONE

| # | LHDN step | Status |
|---|-----------|--------|
| C1 | Category determination | DONE |
| C2 | K2 formula | DONE |
| C3 | Build P with all deductions | DONE |
| C4 | Table 1 M/R/B lookup | DONE |
| C5 | MTD = [(P-M)R+B-(Z+X)]/(n+1) | DONE |
| C6 | Net MTD - zakat | DONE |
| C7 | RM10 threshold | DONE |
| C8 | Round UP 5 sen | DONE |
| C9 | Rebate in B values | DONE |
| C10-14 | Bonus 5-step formula | DONE |
| C15 | Non-resident 30% | DONE |
| C19-22 | Exports (CP39/PCB2II/TP1/TP3) | DEFERRED |

## Verified test cases (20 Apr 2026)

| Employee | Basic | Cat | Children | Expected | Result |
|---|---|---|---|---|---|
| ITO0007 | 4,000 | 1 | 0 | 16.70 | 16.70 ✓ |
| ITO0019 | 6,000 | 1 | 0 | 207.50 | 207.50 ✓ |
| ITO0019 | 6,000 | 1 | 1 u18 | 189.20 | 189.20 ✓ |
| ITO0019 | 6,000 | 2 | 0 | 170.85 | 170.85 ✓ |
| LHDN Ex | 5,500 | 3 | 3 u18 | 110.00 | 110.00 ✓ |
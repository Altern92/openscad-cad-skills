"""Every ISO 286 cell in check_fits.py for 4-30 mm equals the printed table in Bethune 2016,
appendix PDF pp. 773-774 (ANSI B4.2 hole basis). Values: (max, min) mm per basic size, as printed."""
import importlib.util, sys
spec = importlib.util.spec_from_file_location("cf", sys.argv[1]); cf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cf)
S = [4, 5, 6, 8, 10, 12, 16, 20, 25, 30]
B = {  # printed (max, min) of size S[0] per range group; every size in a group shares the deviations
 "H7": [(12, 0), (15, 0), (18, 0), (21, 0)], "H8": [(18, 0), (22, 0), (27, 0), (33, 0)],
 "H9": [(30, 0), (36, 0), (43, 0), (52, 0)], "H11": [(75, 0), (90, 0), (110, 0), (130, 0)],
 "g6": [(-4, -12), (-5, -14), (-6, -17), (-7, -20)], "h6": [(0, -8), (0, -9), (0, -11), (0, -13)],
 "k6": [(9, 1), (10, 1), (12, 1), (15, 2)], "p6": [(20, 12), (24, 15), (29, 18), (35, 22)],
 "c11": [(-70, -145), (-80, -170), (-95, -205), (-110, -240)], "d9": [(-30, -60), (-40, -76), (-50, -93), (-65, -117)],
 "f7": [(-10, -22), (-13, -28), (-16, -34), (-20, -41)], "n6": [(16, 8), (19, 10), (23, 12), (28, 15)],
 "s6": [(27, 19), (32, 23), (39, 28), (48, 35)], "u6": [(31, 23), (37, 28), (44, 33)],
}
group = {4: 0, 5: 0, 6: 0, 8: 1, 10: 1, 12: 2, 16: 2, 20: 3, 25: 3, 30: 3}
n = 0
for c, rows in B.items():
    for s in S:
        g = group[s]
        if g >= len(rows):
            continue
        mx, mn = rows[g]
        lo, hi = cf.iso_limits(c, s)
        assert abs(lo - (s + mn / 1000)) < 1e-9 and abs(hi - (s + mx / 1000)) < 1e-9, (c, s, lo, hi)
        n += 1
for c, s in (("u6", 20), ("c11", 40)):  # outside the verified table -> ValueError (exit 4 in the checker)
    try:
        cf.iso_limits(c, s); raise AssertionError(f"{c} @ {s} must be refused")
    except ValueError:
        pass
print(f"OK: {n} ISO 286 cells match Bethune 2016")

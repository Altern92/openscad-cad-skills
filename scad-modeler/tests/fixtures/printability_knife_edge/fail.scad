// 30 deg wedge standing on its base, apex up: a convex edge sharper than 45 deg (and nothing else).
rotate([90,0,0]) linear_extrude(20) polygon([[0,0],[10,0],[5,5/tan(15)]]);

#!/usr/bin/env bash
# P26 / AC-1, AC-3, AC-4 (2026-11-19, Fable audit e8). "Joined" was proven by a declaration plus a point
# inside the part's own mesh, so a shelf 110 mm above its base got joints/attachment/collisions=PASS, rc=0.
# contact_geometry now measures the real mesh distance of every declared joint.
set -uo pipefail
V="$SCAD_MODELER_SCRIPTS/validate_scad.sh"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
P="$tmp/p"; mkdir -p "$P/parts"; cd "$P"
cat > assembly.scad <<'S'
use <parts/base.scad>
use <parts/shelf.scad>
MODE = is_undef(MODE) ? "assembly" : MODE;
PART = is_undef(PART) ? "" : PART;
Z = is_undef(Z) ? 110 : Z;
if (MODE=="assembly" || PART=="base") base();
if (MODE=="assembly" || PART=="shelf") translate([0,0,Z]) shelf();
S
printf '// EXPECTED_BBOX: [40, 40, 10]\n// EXPECTED_THROUGH_HOLES: 0\nmodule base(){cube([40,40,10]);}\nbase();\n' > parts/base.scad
printf '// EXPECTED_BBOX: [40, 40, 5]\n// EXPECTED_THROUGH_HOLES: 0\nmodule shelf(){cube([40,40,5]);}\nshelf();\n' > parts/shelf.scad
echo '[{"name":"shelf_on_base","part":"shelf","to":"base","at":[20,20,2.5]},{"name":"base_hold","part":"base","at":[20,20,5]}]' > attachments.json
echo '{"bodies":{"base":{"render":[{"MODE":"part","PART":"base"}]},"shelf":{"render":[{"MODE":"part","PART":"shelf"}]}},"joints":[{"a":"shelf","b":"base","max_gap":0.3}],"ground":{"z":0,"bodies":["base"],"tol":0.5}}' > behavior.json
fail=0
res() { grep -o "CHECK_RESULT $1=[A-Z]*" <<< "$2" | head -1; }

# AC-1: floating shelf -> contact_geometry FAIL naming the distance
out=$(bash "$V" --all 2>&1); rc=$?
[ "$(res contact_geometry "$out")" = "CHECK_RESULT contact_geometry=FAIL" ] && grep -q <<< "$out" "base and shelf.*apart" && [ $rc -ne 0 ] \
    || { echo "AC-1: floating shelf not caught (rc=$rc): $(grep -E 'contact_geometry|apart' <<< "$out")" >&2; fail=1; }
# AC-1 negative: shelf resting on the base -> PASS
sed -i '' 's/? 110 :/? 10 :/' assembly.scad
out=$(bash "$V" --all 2>&1)
[ "$(res contact_geometry "$out")" = "CHECK_RESULT contact_geometry=PASS" ] \
    || { echo "AC-1: touching parts not PASS: $(grep -E 'contact_geometry|apart' <<< "$out")" >&2; fail=1; }
# AC-1: a declared name with no part -> FAIL
echo '[{"name":"x","part":"shelf","to":"bracket","at":[20,20,2.5]},{"name":"b","part":"base","at":[20,20,5]}]' > attachments.json
out=$(bash "$V" --all 2>&1)
grep -q <<< "$out" "bracket" && [ "$(res contact_geometry "$out")" = "CHECK_RESULT contact_geometry=FAIL" ] \
    || { echo "AC-1: unknown part name not caught: $(grep -E 'contact_geometry|bracket' <<< "$out")" >&2; fail=1; }
# AC-3: fragment names no longer match -- ["s","l"] with a big allowance must not excuse a 3 mm overlap
echo '[{"name":"s","part":"shelf","to":"base","at":[20,20,2.5]},{"name":"b","part":"base","at":[20,20,5]}]' > attachments.json
sed -i '' 's/? 10 :/? 7 :/' assembly.scad
echo '{"contacts":[{"pair":["s","l"],"joint_type":"rest","expected_interference_mm":[0,50],"derivation":"fixture: fragment names must not match"}]}' > joints.json
out=$(bash "$V" --all 2>&1)
[ "$(res collisions "$out")" = "CHECK_RESULT collisions=FAIL" ] && ! grep -qi <<< "$out" "intentional" \
    || { echo "AC-3: fragment pair still excuses overlap: $(grep -E 'collisions|intentional' <<< "$out")" >&2; fail=1; }
rm joints.json
# AC-4: one part whose bbox equals the assembly (base under a smaller shelf) is not the MODE/PART tripwire
sed -i '' 's/? 7 :/? 10 :/' assembly.scad
printf '// EXPECTED_BBOX: [40, 40, 20]\n// EXPECTED_THROUGH_HOLES: 0\nmodule base(){difference(){cube([40,40,20]); translate([5,5,10]) cube([30,30,11]);}}\nbase();\n' > parts/base.scad
printf '// EXPECTED_BBOX: [20, 20, 5]\n// EXPECTED_THROUGH_HOLES: 0\nmodule shelf(){translate([10,10,0]) cube([20,20,5]);}\nshelf();\n' > parts/shelf.scad
echo '[{"name":"sb","part":"shelf","to":"base","at":[20,20,2.5]},{"name":"b","part":"base","at":[2,2,5]}]' > attachments.json
echo '{"bodies":{"base":{"render":[{"MODE":"part","PART":"base"}]},"shelf":{"render":[{"MODE":"part","PART":"shelf"}]}},"joints":[{"a":"shelf","b":"base","max_gap":0.3}],"ground":{"z":0,"bodies":["base"],"tol":0.5}}' > behavior.json
out=$(bash "$V" --all 2>&1)
grep -q <<< "$out" "MODE/PART switch did not take effect" \
    && { echo "AC-4: enclosure-sized part tripped the MODE/PART tripwire" >&2; fail=1; }
# AC-2: behavior.json that leaves the shelf out -> FAIL naming it; no behavior.json at all -> FAIL
echo '{"bodies":{"base":{"render":[{"MODE":"part","PART":"base"}]}},"joints":[],"ground":{"z":0,"bodies":["base"],"tol":0.5}}' > behavior.json
out=$(bash "$V" --all 2>&1)
[ "$(res behavior "$out")" = "CHECK_RESULT behavior=FAIL" ] && grep -q <<< "$out" "part shelf is in no body" \
    || { echo "AC-2: partial body list passed: $(grep -E 'behavior|no body' <<< "$out")" >&2; fail=1; }
rm behavior.json; out=$(bash "$V" --all 2>&1)
[ "$(res behavior "$out")" = "CHECK_RESULT behavior=FAIL" ] \
    || { echo "AC-2: missing behavior.json not FAIL: $(grep -E 'CHECK_RESULT behavior' <<< "$out")" >&2; fail=1; }
# AC-1: a gap filled by a modelled purchased part (behavior.json MODE vit body joined to both) is proven by
# the behavior gate -> contact_geometry accepts it; the same chain through a PRINTED body does not count
mkdir -p "$tmp/b/parts"; cd "$tmp/b"
cat > assembly.scad <<'S'
use <parts/base.scad>
use <parts/shelf.scad>
MODE = is_undef(MODE) ? "assembly" : MODE;
PART = is_undef(PART) ? "" : PART;
VIT = is_undef(VIT) ? "" : VIT;
if (MODE=="assembly" || PART=="base") base();
if (MODE=="assembly" || PART=="shelf") translate([0,0,13]) shelf();
if (MODE=="assembly" || PART=="spacer" || VIT=="spacer") translate([15,15,10]) cube([10,10,3]);
S
printf '// EXPECTED_BBOX: [40, 40, 10]\n// EXPECTED_THROUGH_HOLES: 0\nmodule base(){cube([40,40,10]);}\nbase();\n' > parts/base.scad
printf '// EXPECTED_BBOX: [40, 40, 5]\n// EXPECTED_THROUGH_HOLES: 0\nmodule shelf(){cube([40,40,5]);}\nshelf();\n' > parts/shelf.scad
echo '[{"name":"sb","part":"shelf","to":"base","at":[20,20,2.5]},{"name":"b","part":"base","at":[20,20,5]}]' > attachments.json
beh() { echo "{\"bodies\":{\"base\":{\"render\":[{\"MODE\":\"part\",\"PART\":\"base\"}]},\"shelf\":{\"render\":[{\"MODE\":\"part\",\"PART\":\"shelf\"}]},\"spacer\":{\"render\":[$1]}},\"joints\":[{\"a\":\"base\",\"b\":\"spacer\",\"max_gap\":0.05},{\"a\":\"spacer\",\"b\":\"shelf\",\"max_gap\":0.05}],\"ground\":{\"z\":0,\"bodies\":[\"base\"],\"tol\":0.5}}" > behavior.json; }
beh '{"MODE":"vit","VIT":"spacer"}'
bash "$V" --all > out.txt 2>&1
grep -q "CHECK_RESULT contact_geometry=PASS" out.txt && grep -q "bridged by purchased spacer" out.txt \
    || { echo "AC-1: purchased spacer bridge not accepted: $(grep -E 'contact_geometry|bridged|apart' out.txt)" >&2; fail=1; }
beh '{"MODE":"part","PART":"spacer"}'
bash "$V" --all > out.txt 2>&1
grep -q "CHECK_RESULT contact_geometry=FAIL" out.txt \
    || { echo "AC-1: a printed body bridged the gap: $(grep -E 'contact_geometry|bridged|apart' out.txt)" >&2; fail=1; }
exit $fail

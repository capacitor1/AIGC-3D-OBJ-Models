"""Make Blender's MTL friendlier to legacy Phong viewers.

Blender writes physically based Pr/Pm values but leaves the legacy Ks at 0.5
and omits Ns.  That makes matte dielectrics (notably the coated cone) look like
polished chrome in viewers that only understand Phong.  Derive Ks/Ns from the
authored metalness/roughness while keeping the Pr/Pm extension intact.
"""
import re
from pathlib import Path

path = Path(__file__).with_name("subwoofer_SW12.mtl")
text = path.read_text(encoding="utf-8")
blocks = re.split(r"(?=^newmtl )", text, flags=re.M)
out = []
for block in blocks:
    if not block.startswith("newmtl "):
        out.append(block)
        continue
    pr_match = re.search(r"^Pr\s+([0-9.]+)", block, flags=re.M)
    pm_match = re.search(r"^Pm\s+([0-9.]+)", block, flags=re.M)
    pr = float(pr_match.group(1)) if pr_match else 0.5
    pm = float(pm_match.group(1)) if pm_match else 0.0
    ks = 0.04 + 0.50 * pm
    ns = 2.0 + 900.0 * (1.0 - pr) ** 2
    block = re.sub(
        r"^Ks\s+[0-9. ]+$",
        f"Ks {ks:.6f} {ks:.6f} {ks:.6f}",
        block,
        count=1,
        flags=re.M,
    )
    if not re.search(r"^Ns\s+", block, flags=re.M):
        block = re.sub(
            r"(^Ks\s+[0-9. ]+\n)",
            rf"\1Ns {ns:.6f}\n",
            block,
            count=1,
            flags=re.M,
        )
    out.append(block)
path.write_text("".join(out), encoding="utf-8", newline="\n")
print("polished", path)

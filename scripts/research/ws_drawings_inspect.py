"""Dump ALL drawing text + check for cell-reference linkages.

For Q4 — find the flow-diagram '87' label. If it's not a literal text
node it may be a cell reference, an embedded image, or stored in a
per-sheet drawing shape with formula-driven text.
"""
import glob
import re
import zipfile

WS = glob.glob("docs/100prosim_d_*/WS.xlsm")[0]

with zipfile.ZipFile(WS) as z:
    members = sorted(z.namelist())
    draw_members = [m for m in members if m.startswith("xl/drawings/") and m.endswith(".xml")]
    print(f"Drawing xmls: {draw_members}\n")

    for m in draw_members:
        print("=" * 70)
        print(m)
        print("=" * 70)
        data = z.read(m).decode("utf-8", errors="replace")
        # Extract all <xdr:sp> shapes — each may have <xdr:txBody> with <a:t> text runs
        # Also extract <xdr:cxnSp> (connectors)
        # Pull all text runs first
        runs = re.findall(r'<a:t[^>]*>([^<]+)</a:t>', data)
        # Also pull any <f> (formula) nodes
        fmls = re.findall(r'<f>([^<]+)</f>', data)
        # Print all short texts
        print(f"  Text runs ({len(runs)}):")
        for i, t in enumerate(runs):
            if len(t) <= 40:
                print(f"    [{i:03d}] {t!r}")
        if fmls:
            print(f"  Formulas in drawing ({len(fmls)}):")
            for f in fmls:
                print(f"    {f!r}")
        print()

    # Also check if any drawing references sheet cells (via xdr:oneCellAnchor etc.
    # The actual text-value linkage would be in <xdr:sp><xdr:nvSpPr><xdr:cNvPr name=.../> but
    # dynamic text comes from <xdr:txBody> with <a:r><a:t>N</a:t></a:r>
    # Formula-bound shapes are rare; more likely the diagram is:
    #   (a) manually typed text
    #   (b) an embedded image (check xl/media/)
    print("\n" + "=" * 70)
    print("Images in xl/media/")
    print("=" * 70)
    medias = [m for m in members if m.startswith("xl/media/")]
    for m in medias:
        print(f"  {m}  ({z.getinfo(m).file_size} bytes)")

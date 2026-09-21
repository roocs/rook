"""Lay out Quarto's editable Milano slides without a reference PPTX template.

Pandoc splits text/image/table sequences into continuation slides. Reunite each
sequence at its next title, preserving native text, tables, pictures and links.
Only the five-section main talk is supported; fail loudly when its structure changes.
"""

# Only parses locally generated Quarto packages, never downloaded documents.
# ruff: noqa: S314, S405

import argparse
import copy
import posixpath
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


def xml_bytes(root):
    """Serialize XML while preserving Office package namespaces."""
    # Office package metadata uses a default namespace (also required by LibreOffice).
    if root.tag.startswith("{" + REL + "}"):
        ET.register_namespace("", REL)
    elif root.tag.endswith("}Types"):
        ET.register_namespace("", "http://schemas.openxmlformats.org/package/2006/content-types")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def tag(name):
    """Expand a DrawingML namespace prefix."""
    prefix, local = name.split(":")
    return f"{{{NS[prefix]}}}{local}"


def child(parent, name):
    """Find a direct child or append it when absent."""
    element = parent.find(name, NS)
    if element is None:
        element = ET.SubElement(parent, tag(name))
    return element


def text(element):
    """Collect the visible text of a shape."""
    return "".join(t.text or "" for t in element.findall(".//a:t", NS))


def is_title(shape):
    """Identify a title placeholder before removing layout inheritance."""
    return any(p.get("type") in {"title", "ctrTitle"} for p in shape.findall(".//p:ph", NS))


def emu(inches):
    """Convert inches to Office drawing units."""
    return str(round(inches * 914400))


def order_children(element, names):
    """Keep DrawingML properties in schema order for PowerPoint compatibility."""
    order = {tag(name): index for index, name in enumerate(names.split())}
    element[:] = sorted(element, key=lambda item: order.get(item.tag, -1))


def place(shape, box, *, picture=False):
    """Position a shape, preserving picture proportions."""
    x, y, width, height = box
    if shape.tag == tag("p:graphicFrame"):
        transform = child(shape, "p:xfrm")
    else:
        transform = child(child(shape, "p:spPr"), "a:xfrm")
    if picture:
        old = transform.find("a:ext", NS)
        ratio = int(old.get("cx")) / int(old.get("cy"))
        fitted_width = min(width, height * ratio)
        fitted_height = fitted_width / ratio
        x += (width - fitted_width) / 2
        y += (height - fitted_height) / 2
        width, height = fitted_width, fitted_height
    child(transform, "a:off").attrib.update(x=emu(x), y=emu(y))
    child(transform, "a:ext").attrib.update(cx=emu(width), cy=emu(height))


def style_text(shape, size=23, *, title=False):  # noqa: C901 -- explicit DrawingML property handling
    """Apply explicit typography while preserving links and code formatting."""
    # Resolve inherited bullet behavior before detaching layout placeholders.
    for body in shape.findall(".//p:txBody", NS) + shape.findall(".//a:txBody", NS):
        props = child(body, "a:bodyPr")
        props.attrib.update(anchor="t", wrap="square", lIns="0", rIns="0", tIns="0", bIns="0")  # codespell:ignore lins
        for fit in list(props):
            if fit.tag in {tag("a:normAutofit"), tag("a:spAutoFit"), tag("a:noAutofit")}:
                props.remove(fit)
        ET.SubElement(props, tag("a:noAutofit"))
        for paragraph in list(body.findall("a:p", NS)):
            if not text(paragraph).strip():
                body.remove(paragraph)
                continue
            ppr = child(paragraph, "a:pPr")
            bullet = ppr.find("a:buNone", NS) is None and ppr.get("marL") is None
            ppr.attrib.update(marL=emu(0.23) if bullet else "0", indent=emu(-0.19) if bullet else "0", algn="l")
            for name in ("a:lnSpc", "a:spcBef", "a:spcAft"):
                old = ppr.find(name, NS)
                if old is not None:
                    ppr.remove(old)
            ET.SubElement(ET.SubElement(ppr, tag("a:lnSpc")), tag("a:spcPct"), val="108000")
            ET.SubElement(ET.SubElement(ppr, tag("a:spcAft")), tag("a:spcPts"), val="900")
            if bullet:
                child(ppr, "a:buChar").set("char", "•")
            else:
                child(ppr, "a:buNone")
            runs = paragraph.findall("a:r/a:rPr", NS)
            runs += [child(ppr, "a:defRPr"), child(paragraph, "a:endParaRPr")]
            for rpr in runs:
                font = rpr.find("a:latin", NS)
                mono = font is not None and font.get("typeface") in {
                    "Courier",
                    "Courier New",
                    "Consolas",
                }
                rpr.set("sz", str(round(size * 100)))
                child(rpr, "a:latin").set("typeface", "Consolas" if mono else "Arial")
                # Preserve code highlighting and hyperlink relationships.
                fill = rpr.find("a:solidFill", NS)
                if fill is None or title:
                    if fill is not None:
                        rpr.remove(fill)
                    ET.SubElement(
                        ET.SubElement(rpr, tag("a:solidFill")),
                        tag("a:srgbClr"),
                        val="457B9D" if title else "222222",
                    )
                if title:
                    rpr.set("b", "1")
                order_children(
                    rpr,
                    "a:ln a:noFill a:solidFill a:gradFill a:blipFill a:pattFill a:grpFill a:effectLst a:effectDag a:highlight "
                    "a:uLnTx a:uLn a:uFillTx a:uFill a:latin a:ea a:cs a:sym a:hlinkClick a:hlinkMouseOver a:rtl a:extLst",
                )
            order_children(
                ppr,
                "a:lnSpc a:spcBef a:spcAft a:buClrTx a:buClr a:buSzTx a:buSzPct a:buSzPts a:buFontTx "
                "a:buFont a:buNone a:buAutoNum a:buChar a:buBlip a:tabLst a:defRPr a:extLst",
            )
    for parent in shape.iter():
        for element in list(parent):
            if element.tag == tag("p:ph"):
                parent.remove(element)
    if shape.tag == tag("p:sp"):
        make_text_box(shape)


def make_text_box(shape):
    """Make detached placeholders self-contained for PowerPoint importers.

    Placeholder geometry normally comes from the slide layout. Once p:ph is
    removed, explicitly identify a text box and provide its geometry; otherwise
    importers can discard the shape even though its text and bounds are present.
    """
    child(child(shape, "p:nvSpPr"), "p:cNvSpPr").set("txBox", "1")
    props = child(shape, "p:spPr")
    for element in list(props):
        if element.tag in {
            tag("a:prstGeom"),
            tag("a:custGeom"),
            tag("a:noFill"),
            tag("a:solidFill"),
            tag("a:gradFill"),
            tag("a:blipFill"),
            tag("a:pattFill"),
            tag("a:grpFill"),
            tag("a:ln"),
        }:
            props.remove(element)
    child(ET.SubElement(props, tag("a:prstGeom"), prst="rect"), "a:avLst")
    ET.SubElement(props, tag("a:noFill"))
    child(ET.SubElement(props, tag("a:ln")), "a:noFill")
    order_children(
        props,
        "a:xfrm a:custGeom a:prstGeom a:noFill a:solidFill a:gradFill "
        "a:blipFill a:pattFill a:grpFill a:ln a:effectLst a:effectDag a:scene3d a:sp3d a:extLst",
    )


def layout(shapes, index):
    """Arrange the five main slides and reject unsupported content structures."""
    titles = [s for s in shapes if is_title(s)]
    pictures = [s for s in shapes if s.tag == tag("p:pic")]
    tables = [s for s in shapes if s.tag == tag("p:graphicFrame")]
    bodies = [s for s in shapes if s.tag == tag("p:sp") and s not in titles and text(s).strip()]
    expected = (1, 1, 0, 2 if index < 4 else 1)
    actual = (len(titles), len(pictures), len(tables), len(bodies))
    if actual != expected:
        raise ValueError(f"Main slide {index + 1}: expected title/image/table/body counts {expected}, got {actual}; update the PPTX layout")
    title = titles[0]
    place(title, (0.65, 0.4, 12.05, 0.75))
    style_text(title, 36 if index == 0 else 30, title=True)
    if index == 0:
        boxes = [(0.65, 1.5, 7.4, 5.5), (8.5, 5.8, 4.15, 1.3)]
        diagram = (8.65, 1.5, 3.85, 4.1)
        sizes = [22, 14]
        caption = bodies[1].find("p:txBody/a:p", NS)
        for run in list(caption):
            if text(run).startswith("CC BY-SA"):
                caption.insert(list(caption).index(run), ET.Element(tag("a:br")))
    elif index == 4:
        boxes = [(0.65, 4.7, 12.05, 2.3)]
        diagram = (0.8, 1.4, 11.75, 3.0)
        sizes = [23]
    else:
        boxes = [(0.65, 1.4, 12.05, 1.8), (0.65, 6.2, 12.05, 1.0)]
        diagram = (0.8, 3.3, 11.75, 2.65)
        sizes = [22, 20]
    for shape, box, size in zip(bodies, boxes, sizes, strict=True):
        place(shape, box)
        style_text(shape, size)
    place(pictures[0], diagram, picture=True)
    return [title, *bodies, *pictures, *tables]


def style_pptx(source, output):  # noqa: C901 -- preserve package relationships while merging slides
    """Combine Quarto continuation slides and write the styled main deck."""
    with zipfile.ZipFile(source) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    presentation = ET.fromstring(files["ppt/presentation.xml"])
    relationships = ET.fromstring(files["ppt/_rels/presentation.xml.rels"])
    by_id = {r.get("Id"): r for r in relationships}
    slide_list = presentation.find("p:sldIdLst", NS)
    groups = []
    for entry in list(slide_list):
        relation = by_id[entry.get(tag("r:id"))]
        path = posixpath.normpath("ppt/" + relation.get("Target"))
        root = ET.fromstring(files[path])
        shapes = list(root.find("p:cSld/p:spTree", NS))[2:]
        if any(is_title(s) for s in shapes):
            groups.append([])
        if not groups:
            raise ValueError("PowerPoint starts with an untitled continuation slide")
        groups[-1].append((entry, path, root, shapes))
    if len(groups) != 5:
        raise ValueError(f"Expected five main sections, found {len(groups)}")
    removed = set()
    for index, group in enumerate(groups):
        _, target_path, root, _ = group[0]
        tree = root.find("p:cSld/p:spTree", NS)
        for shape in list(tree)[2:]:
            tree.remove(shape)
        merged = []
        rels = ET.Element(f"{{{REL}}}Relationships")
        for number, (entry, path, _, shapes) in enumerate(group):
            rel_path = posixpath.dirname(path) + "/_rels/" + posixpath.basename(path) + ".rels"
            source_rels = ET.fromstring(files[rel_path])
            mapping = {}
            for relation in source_rels:
                if number and relation.get("Type").endswith(("/slideLayout", "/notesSlide")):
                    continue
                new = copy.deepcopy(relation)
                old_id = new.get("Id")
                new_id = f"rId{len(rels) + 1}"
                mapping[old_id] = new_id
                new.set("Id", new_id)
                rels.append(new)
            for shape in shapes:
                shape = copy.deepcopy(shape)
                for element in shape.iter():
                    for key, value in list(element.attrib.items()):
                        if key.startswith("{" + NS["r"] + "}"):
                            element.set(key, mapping[value])
                merged.append(shape)
            if number:
                slide_list.remove(entry)
                relationships.remove(by_id[entry.get(tag("r:id"))])
                removed.update({path, rel_path})
        arranged = layout(merged, index)
        for shape_id, shape in enumerate(arranged, 2):
            shape.find(".//p:cNvPr", NS).set("id", str(shape_id))
            tree.append(shape)
        files[target_path] = xml_bytes(root)
        rel_path = posixpath.dirname(target_path) + "/_rels/" + posixpath.basename(target_path) + ".rels"
        files[rel_path] = xml_bytes(rels)
    presentation.find("p:sldSz", NS).attrib.update(cx=emu(13.333333), cy=emu(7.5))
    files["ppt/presentation.xml"] = xml_bytes(presentation)
    files["ppt/_rels/presentation.xml.rels"] = xml_bytes(relationships)
    types = ET.fromstring(files["[Content_Types].xml"])
    for override in list(types):
        if override.get("PartName", "").lstrip("/") in removed:
            types.remove(override)
    files["[Content_Types].xml"] = xml_bytes(types)
    for name, data in list(files.items()):
        if name.startswith("ppt/theme/") and name.endswith(".xml"):
            theme = ET.fromstring(data)
            for color_name in ("hlink", "folHlink"):
                color = theme.find(f".//a:clrScheme/a:{color_name}", NS)
                if color is not None:
                    color[:] = [ET.Element(tag("a:srgbClr"), val="457B9D")]
            files[name] = xml_bytes(theme)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            if name not in removed:
                archive.writestr(name, data)
    print(f"Styled five editable main slides: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    style_pptx(args.source, args.output)

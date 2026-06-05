from __future__ import annotations

from pathlib import Path

from defusedxml import ElementTree

from bib_csl_xsl.__main__ import main
from bib_csl_xsl.converter import convert_csl_file, parse_csl_style

FIXTURE = Path(__file__).parent / "fixtures" / "ieee.csl"


def test_parse_csl_style_reads_metadata() -> None:
    style = parse_csl_style(FIXTURE)

    assert style.title == "IEEE Reference Guide version 11.29.2023"
    assert style.updated == "2026-01-07T15:36:59+00:00"
    assert style.csl_version == "1.0"
    assert style.citation_format == "numeric"
    assert "author" in style.macros


def test_convert_csl_file_generates_standalone_word_style(tmp_path: Path) -> None:
    output = tmp_path / "ieee.xsl"

    convert_csl_file(FIXTURE, output)

    xml_text = output.read_text(encoding="utf-8")
    root = ElementTree.fromstring(xml_text)

    assert root.tag.endswith("stylesheet")
    assert 'omit-xml-declaration="yes"' in xml_text
    assert 'match="b:StyleName"' in xml_text
    assert "IEEE Reference Guide version 11.29.2023" in xml_text
    assert "2026-01-07T15:36:59+00:00" in xml_text
    assert 'match="b:GetImportantFields"' in xml_text
    assert "IEEE2006OfficeOnline" not in xml_text
    assert "b:Author/b:Author/b:NameList" in xml_text
    assert "b:JournalName" in xml_text
    assert "<b:ImportantField>Author</b:ImportantField>" not in xml_text


def test_generated_xsl_uses_csl_metadata_fields(tmp_path: Path) -> None:
    output = tmp_path / "ieee.xsl"

    convert_csl_file(FIXTURE, output)

    xml_text = output.read_text(encoding="utf-8")

    assert (
        '<xsl:template match="b:Version"><xsl:text>'
        "2026-01-07T15:36:59+00:00"
        "</xsl:text></xsl:template>" in xml_text
    )
    assert (
        '<xsl:template match="b:XslVersion"><xsl:text>2006</xsl:text></xsl:template>' in xml_text
    )
    assert (
        '<xsl:template match="b:StyleNameLocalized"><xsl:text>'
        "IEEE Reference Guide version 11.29.2023"
        "</xsl:text></xsl:template>" in xml_text
    )
    assert 'match="b:Citation"' in xml_text
    assert 'name="display-page-or-pages"' in xml_text
    assert "/*/b:Locals/b:Local[1]/b:APA/b:SecondaryOpen" in xml_text
    assert '<xsl:sort select="b:RefOrder" order="ascending" data-type="number"/>' in xml_text


def test_generated_xsl_uses_bound_variable_names_for_et_al_logic(tmp_path: Path) -> None:
    output = tmp_path / "ieee.xsl"

    convert_csl_file(FIXTURE, output)

    xml_text = output.read_text(encoding="utf-8")

    assert "number($display_count)" not in xml_text


def test_generated_xsl_only_uses_valid_choose_children(tmp_path: Path) -> None:
    output = tmp_path / "ieee.xsl"

    convert_csl_file(FIXTURE, output)

    root = ElementTree.fromstring(output.read_text(encoding="utf-8"))

    for choose in root.findall(".//{http://www.w3.org/1999/XSL/Transform}choose"):
        child_tags = {child.tag for child in choose}
        assert child_tags <= {
            "{http://www.w3.org/1999/XSL/Transform}when",
            "{http://www.w3.org/1999/XSL/Transform}otherwise",
        }


def test_generated_xsl_does_not_emit_author_label_artifact(tmp_path: Path) -> None:
    output = tmp_path / "ieee.xsl"

    convert_csl_file(FIXTURE, output)

    xml_text = output.read_text(encoding="utf-8")

    assert ", author" not in xml_text
    assert ">author<" not in xml_text
    assert ">ed.<" in xml_text


def test_generated_xsl_uses_ref_order_not_tag_for_citation_numbers(tmp_path: Path) -> None:
    output = tmp_path / "ieee.xsl"

    convert_csl_file(FIXTURE, output)

    xml_text = output.read_text(encoding="utf-8")

    assert "b:Tag" not in xml_text
    assert "b:RefOrder" in xml_text


def test_generated_bibliography_outputs_html_paragraphs(tmp_path: Path) -> None:
    output = tmp_path / "ieee.xsl"

    convert_csl_file(FIXTURE, output)

    xml_text = output.read_text(encoding="utf-8")

    assert '<xsl:template match="b:Bibliography">' in xml_text
    assert '<html xmlns="http://www.w3.org/TR/REC-html40">' in xml_text
    assert '<table class="MsoBibliography" width="100%">' in xml_text
    assert '<td style="text-align:right" valign="top">' in xml_text
    assert 'name="bib-ref-order"' in xml_text
    assert '<p class="MsoBibliography">' in xml_text


def test_generated_xsl_uses_citation_level_locator_paths(tmp_path: Path) -> None:
    output = tmp_path / "ieee.xsl"

    convert_csl_file(FIXTURE, output)

    xml_text = output.read_text(encoding="utf-8")

    assert "../b:Pages" in xml_text
    assert "../b:PageRange" in xml_text
    assert "../b:LocatorType" in xml_text


def test_cli_writes_output_file(tmp_path: Path) -> None:
    output = tmp_path / "cli-output.xsl"

    exit_code = main([str(FIXTURE), "--output", str(output)])

    assert exit_code == 0
    assert output.exists()

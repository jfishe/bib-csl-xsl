from __future__ import annotations

from pathlib import Path

from defusedxml import ElementTree

from bib_csl_xsl.__main__ import main
from bib_csl_xsl.converter import BibliographyFormat, convert_csl_file, parse_csl_style

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


def test_generated_xsl_wraps_corporate_author_unions_before_predicates(tmp_path: Path) -> None:
    output = tmp_path / "ieee.xsl"

    convert_csl_file(FIXTURE, output)

    xml_text = output.read_text(encoding="utf-8")

    assert (
        'select="count((b:Author/b:Author/b:NameList/b:Person | '
        'b:Author/b:Author/b:Corporate))"' in xml_text
    )
    assert (
        '<xsl:for-each select="(b:Author/b:Author/b:NameList/b:Person | '
        "b:Author/b:Author/b:Corporate)[position() &lt;= number($display_count_" in xml_text
    )


def test_generated_xsl_uses_direct_corporate_author_paths(tmp_path: Path) -> None:
    output = tmp_path / "ieee.xsl"

    convert_csl_file(FIXTURE, output)

    xml_text = output.read_text(encoding="utf-8")

    assert "b:Author/b:Author/b:Corporate" in xml_text
    assert "b:Author/b:Author/b:NameList/b:Corporate" not in xml_text


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


def test_reference_table_bibliography_format_is_opt_in(tmp_path: Path) -> None:
    output = tmp_path / "ieee-reference-table.xsl"

    convert_csl_file(FIXTURE, output, bibliography_format=BibliographyFormat.REFERENCE_TABLE)

    xml_text = output.read_text(encoding="utf-8")

    assert "IeeeReferenceGuideVersion11292023ReferenceTable" in xml_text
    assert "IEEE Reference Guide version 11.29.2023 (Reference Table)" in xml_text
    assert "Reference Number</td>" in xml_text
    assert "Issue Date, Edition or Revision</td>" in xml_text
    assert "Document Number</td>" in xml_text
    assert '<td class="MsoBibliographyRef" style="width:9.68%">' in xml_text
    assert '<xsl:value-of select="b:RefOrder"/>' in xml_text
    assert '<xsl:call-template name="bib-ref-order"/>' not in xml_text
    assert '<td class="MsoBibliographyCell" style="width:23.40%">' in xml_text
    assert '<xsl:attribute name="href">' in xml_text


def test_reference_table_revision_column_prefers_revision_then_edition_then_date(
    tmp_path: Path,
) -> None:
    output = tmp_path / "ieee-reference-table.xsl"

    convert_csl_file(FIXTURE, output, bibliography_format=BibliographyFormat.REFERENCE_TABLE)

    xml_text = output.read_text(encoding="utf-8")

    cell_start = xml_text.index('<td class="MsoBibliographyCell" style="width:11.68%">')
    cell_end = xml_text.index("</td>", cell_start)
    cell_text = xml_text[cell_start:cell_end]

    version_index = cell_text.index('test="string-length(normalize-space(string($text_')
    edition_index = cell_text.index('test="(string-length(normalize-space(string($choose_')
    issued_index = cell_text.rindex('test="(string-length(normalize-space(string($choose_')

    assert version_index < edition_index < issued_index
    assert 'select="b:Version"' in cell_text


def test_generated_xsl_uses_citation_level_locator_paths(tmp_path: Path) -> None:
    output = tmp_path / "ieee.xsl"

    convert_csl_file(FIXTURE, output)

    xml_text = output.read_text(encoding="utf-8")

    assert "../b:Pages" in xml_text
    assert "../b:PageRange" in xml_text
    assert "../b:LocatorType" in xml_text


def test_generated_xsl_does_not_duplicate_available_colon(tmp_path: Path) -> None:
    standard_output = tmp_path / "ieee-standard.xsl"
    reference_output = tmp_path / "ieee-reference-table.xsl"

    convert_csl_file(FIXTURE, standard_output)
    convert_csl_file(
        FIXTURE,
        reference_output,
        bibliography_format=BibliographyFormat.REFERENCE_TABLE,
    )

    standard_xml = standard_output.read_text(encoding="utf-8")
    reference_xml = reference_output.read_text(encoding="utf-8")

    assert ">available:<" not in standard_xml
    assert ">available:<" not in reference_xml
    assert "Available::" not in standard_xml
    assert "Available::" not in reference_xml


def test_reference_table_title_column_omits_available_label(tmp_path: Path) -> None:
    output = tmp_path / "ieee-reference-table.xsl"

    convert_csl_file(FIXTURE, output, bibliography_format=BibliographyFormat.REFERENCE_TABLE)

    xml_text = output.read_text(encoding="utf-8")
    title_cell_start = xml_text.index('<td class="MsoBibliographyCell" style="width:39.94%">')
    title_cell_end = xml_text.index("</td>", title_cell_start)
    title_cell = xml_text[title_cell_start:title_cell_end]

    assert "Available" not in title_cell
    assert 'call-template name="macro_access"' not in title_cell
    assert '<xsl:attribute name="href">' not in title_cell
    assert 'call-template name="macro_title"' in title_cell


def test_reference_table_document_number_column_hides_url_text_and_links_it(
    tmp_path: Path,
) -> None:
    output = tmp_path / "ieee-reference-table.xsl"

    convert_csl_file(FIXTURE, output, bibliography_format=BibliographyFormat.REFERENCE_TABLE)

    xml_text = output.read_text(encoding="utf-8")
    cell_start = xml_text.index('<td class="MsoBibliographyCell" style="width:23.40%">')
    cell_end = xml_text.index("</td>", cell_start)
    cell_text = xml_text[cell_start:cell_end]

    assert 'select="b:URL"' in cell_text
    assert "normalize-space(string($text_" in cell_text
    assert '<xsl:attribute name="href">' in cell_text
    assert "https://doi.org/" not in cell_text
    assert 'call-template name="macro_title"' not in cell_text
    assert 'call-template name="macro_issued"' in cell_text


def test_cli_writes_output_file(tmp_path: Path) -> None:
    output = tmp_path / "cli-output.xsl"

    exit_code = main([str(FIXTURE), "--output", str(output)])

    assert exit_code == 0
    assert output.exists()


def test_cli_can_generate_reference_table_output(tmp_path: Path) -> None:
    output = tmp_path / "cli-reference-table.xsl"

    exit_code = main(
        [
            str(FIXTURE),
            "--output",
            str(output),
            "--bibliography-format",
            BibliographyFormat.REFERENCE_TABLE.value,
        ]
    )

    assert exit_code == 0
    assert "Reference Number</td>" in output.read_text(encoding="utf-8")

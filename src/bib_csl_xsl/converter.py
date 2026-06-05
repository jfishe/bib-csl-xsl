from __future__ import annotations

import re
from collections.abc import Iterable
from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from xml.etree import ElementTree as XmlElementTree
from xml.sax.saxutils import escape

from defusedxml import ElementTree as SafeElementTree

CSL_NS = "http://purl.org/net/xbiblio/csl"
WORD_BIBLIOGRAPHY_NS = "http://schemas.openxmlformats.org/officeDocument/2006/bibliography"
WORD_BIBLIOGRAPHY_XSL_VERSION = "2006"
NS = {"csl": CSL_NS}

PERSON_ROLE_PATHS = {
    "author": "b:Author/b:Author/b:NameList/b:Person | b:Author/b:Author/b:NameList/b:Corporate",
    "editor": "b:Editor/b:Editor/b:NameList/b:Person | b:Editor/b:Editor/b:NameList/b:Corporate",
    "translator": "b:Translator/b:Translator/b:NameList/b:Person | b:Translator/b:Translator/b:NameList/b:Corporate",
    "director": "b:Director/b:Director/b:NameList/b:Person | b:Director/b:Director/b:NameList/b:Corporate",
    "composer": "b:Composer/b:Composer/b:NameList/b:Person | b:Composer/b:Composer/b:NameList/b:Corporate",
}

TEXT_VARIABLE_PATHS = {
    "title": ("b:Title",),
    "container-title": (
        "b:JournalName",
        "b:BookTitle",
        "b:ConferenceName",
        "b:PeriodicalTitle",
        "b:InternetSiteTitle",
        "b:PublicationTitle",
    ),
    "volume": ("b:Volume",),
    "issue": ("b:Issue",),
    "page": ("b:Pages", "b:PageRange"),
    "publisher": ("b:Publisher",),
    "URL": ("b:URL",),
    "DOI": ("b:DOI",),
    "edition": ("b:Edition",),
    "number": ("b:Number", "b:PatentNumber"),
    "genre": ("b:Type",),
    "medium": ("b:Medium",),
    "collection-title": ("b:SeriesTitle",),
    "collection-number": ("b:SeriesNumber",),
    "chapter-number": ("b:ChapterNumber",),
    "event": ("b:ConferenceName",),
    "archive": ("b:Archive",),
    "archive_location": ("b:ArchiveLocation",),
    "locator": ("../b:Pages", "../b:PageRange", "b:Pages", "b:PageRange"),
    "note": ("b:Comments",),
    "number-of-volumes": ("b:NumberOfVolumes",),
    "status": ("b:Comments",),
    "standard-number": ("b:StandardNumber", "b:ISBN", "b:ISSN"),
    "version": ("b:Version",),
}

DATE_VARIABLE_PARTS = {
    "issued": {"year": "b:Year", "month": "b:Month", "day": "b:Day"},
    "accessed": {
        "year": "b:YearAccessed",
        "month": "b:MonthAccessed",
        "day": "b:DayAccessed",
    },
    "event-date": {"year": "b:Year", "month": "b:Month", "day": "b:Day"},
}

TERMS = {
    ("edition", "short"): "ed.",
    ("editor", "short"): "ed.",
    ("editor_plural", "short"): "eds.",
    ("translator", "short"): "trans.",
    ("translator_plural", "short"): "trans.",
    ("director", "short"): "dir.",
    ("director_plural", "short"): "dirs.",
    ("composer", "short"): "comp.",
    ("composer_plural", "short"): "comps.",
    ("page", "short"): "pp.",
    ("number", "short"): "no.",
    ("issue", "short"): "no.",
    ("volume", "short"): "vol.",
    ("chapter", "short"): "ch.",
    ("accessed", "long"): "accessed",
    ("available at", "long"): "available",
}

REFERENCE_TABLE_TITLE_MACROS = frozenset({"title", "event"})
REFERENCE_TABLE_TITLE_VARIABLES = frozenset(
    {"title", "container-title", "collection-title", "event"}
)

CSL_TO_WORD_TYPES = {
    "article-journal": ("JournalArticle",),
    "article-magazine": ("ArticleInAPeriodical",),
    "article-newspaper": ("ArticleInAPeriodical",),
    "book": ("Book",),
    "chapter": ("BookSection",),
    "paper-conference": ("ConferenceProceedings",),
    "report": ("Report",),
    "thesis": ("Report",),
    "webpage": ("InternetSite", "DocumentFromInternetSite"),
    "patent": ("Patent",),
    "dataset": ("Report",),
}

SUPPORTED_TAGS = {
    "bibliography",
    "choose",
    "citation",
    "date",
    "date-part",
    "else",
    "else-if",
    "et-al",
    "group",
    "id",
    "if",
    "info",
    "label",
    "layout",
    "link",
    "locale",
    "macro",
    "name",
    "names",
    "number",
    "author",
    "category",
    "contributor",
    "email",
    "key",
    "sort",
    "rights",
    "substitute",
    "summary",
    "style",
    "term",
    "terms",
    "text",
    "title",
    "title-short",
    "updated",
    "uri",
}


class ConversionError(ValueError):
    """Raised when a CSL style cannot be converted by the supported subset."""

    pass


class BibliographyFormat(StrEnum):
    """Supported bibliography output layouts."""

    STANDARD = "standard"
    REFERENCE_TABLE = "reference-table"


@dataclass(slots=True)
class CslStyle:
    """Parsed CSL metadata and the bibliography/citation layouts to compile."""

    title: str
    updated: str
    csl_version: str
    citation_format: str
    citation_layout: XmlElementTree.Element
    bibliography_layout: XmlElementTree.Element
    macros: dict[str, XmlElementTree.Element]

    @property
    def compact_title(self) -> str:
        """Return a compact Word style identifier derived from the CSL title."""
        collapsed = re.sub(r"[^A-Za-z0-9]+", " ", self.title).strip()
        if not collapsed:
            return "GeneratedStyle"
        return "".join(part.capitalize() for part in collapsed.split())[:64]


@dataclass(slots=True)
class Fragment:
    """Rendered XSL instructions plus the variable that holds their string value."""

    setup_lines: list[str]
    variable_name: str
    display_test: str
    contribution_test: str


def parse_csl_style(path: str | Path) -> CslStyle:
    """Parse a CSL file into the subset required by the converter."""
    root = SafeElementTree.parse(Path(path)).getroot()
    if root is None:
        raise ConversionError("Style document is empty.")
    _validate_supported_tags(root)

    if root.tag != f"{{{CSL_NS}}}style":
        raise ConversionError("Expected a CSL <style> document.")

    info = root.find("csl:info", NS)
    if info is None:
        raise ConversionError("Style is missing required <info> metadata.")

    title = _require_text(info, "csl:title")
    updated = _require_text(info, "csl:updated")
    citation = root.find("csl:citation", NS)
    bibliography = root.find("csl:bibliography", NS)
    if citation is None or bibliography is None:
        raise ConversionError("Style must define both <citation> and <bibliography>.")

    citation_format = citation.attrib.get(
        "citation-format", root.attrib.get("citation-format", "")
    )
    if not citation_format:
        category = info.find("csl:category[@citation-format]", NS)
        if category is not None:
            citation_format = category.attrib.get("citation-format", "")

    citation_layout = citation.find("csl:layout", NS)
    bibliography_layout = bibliography.find("csl:layout", NS)
    if citation_layout is None or bibliography_layout is None:
        raise ConversionError("Citation and bibliography sections must contain <layout>.")

    macros = {
        macro.attrib["name"]: macro
        for macro in root.findall("csl:macro", NS)
        if "name" in macro.attrib
    }
    return CslStyle(
        title=title,
        updated=updated,
        csl_version=root.attrib.get("version", "1.0"),
        citation_format=citation_format,
        citation_layout=citation_layout,
        bibliography_layout=bibliography_layout,
        macros=macros,
    )


def validate_style(style: CslStyle) -> None:
    """Validate that the parsed style is compatible with this converter."""
    if style.citation_format != "numeric":
        raise ConversionError(
            f"Unsupported citation format {style.citation_format!r}; only numeric CSL styles are supported."
        )


def convert_csl_file(
    source: str | Path,
    destination: str | Path,
    bibliography_format: BibliographyFormat = BibliographyFormat.STANDARD,
) -> Path:
    """Convert a CSL file on disk into a Word bibliography XSL file."""
    style = parse_csl_style(source)
    validate_style(style)
    output = write_word_bibliography_style(
        style, destination, bibliography_format=bibliography_format
    )
    return output


def write_word_bibliography_style(
    style: CslStyle,
    destination: str | Path,
    bibliography_format: BibliographyFormat = BibliographyFormat.STANDARD,
) -> Path:
    """Write a standalone Word bibliography XSL file for the parsed CSL style."""
    compiler = _Compiler(style, bibliography_format=bibliography_format)
    output_path = Path(destination)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(compiler.render_stylesheet(), encoding="utf-8")
    return output_path


class _Compiler:
    def __init__(
        self,
        style: CslStyle,
        bibliography_format: BibliographyFormat = BibliographyFormat.STANDARD,
    ) -> None:
        self.style = style
        self.bibliography_format = bibliography_format
        self._counter = 0

    def render_stylesheet(self) -> str:
        macros = "\n".join(
            self._render_macro_template(name, macro) for name, macro in self.style.macros.items()
        )
        bibliography_fragment = self._compile_bibliography_layout()
        style_name = self._style_name()
        style_name_localized = self._style_name_localized()
        lines = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<xsl:stylesheet version="1.0"',
            '    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"',
            f'    xmlns:b="{WORD_BIBLIOGRAPHY_NS}"',
            '    exclude-result-prefixes="b">',
            '  <xsl:output method="xml" encoding="utf-8" indent="yes" omit-xml-declaration="yes"/>',
            "",
            self._helper_templates().rstrip(),
            "",
            macros.rstrip(),
            "",
            '  <xsl:template match="/">',
            '    <xsl:apply-templates select="*"/>',
            "  </xsl:template>",
            "",
            '  <xsl:template match="b:Version"><xsl:text>'
            + escape(self.style.updated)
            + "</xsl:text></xsl:template>",
            '  <xsl:template match="b:XslVersion"><xsl:text>'
            + WORD_BIBLIOGRAPHY_XSL_VERSION
            + "</xsl:text></xsl:template>",
            '  <xsl:template match="b:StyleName"><xsl:text>'
            + escape(style_name)
            + "</xsl:text></xsl:template>",
            '  <xsl:template match="b:StyleNameLocalized"><xsl:text>'
            + escape(style_name_localized)
            + "</xsl:text></xsl:template>",
            "",
            '  <xsl:template match="b:GetImportantFields">',
            "    <b:ImportantFields>",
            "      <xsl:choose>",
            *self._important_fields_templates(),
            "        <xsl:otherwise>",
            *[
                f"          <b:ImportantField>{escape(field)}</b:ImportantField>"
                for field in self._important_fields_default()
            ],
            "        </xsl:otherwise>",
            "      </xsl:choose>",
            "    </b:ImportantFields>",
            "  </xsl:template>",
            "",
            '  <xsl:template match="b:Citation">',
            '    <html xmlns="http://www.w3.org/TR/REC-html40">',
            "      <body>",
            '        <xsl:if test="b:FirstAuthor">',
            '          <xsl:call-template name="templ_prop_SecondaryOpen"/>',
            "        </xsl:if>",
            '        <xsl:value-of select="b:Source/b:RefOrder"/>',
            '        <xsl:if test="string-length(normalize-space(b:Pages)) &gt; 0">',
            '          <xsl:call-template name="display-page-or-pages">',
            '            <xsl:with-param name="pages" select="normalize-space(b:Pages)"/>',
            "          </xsl:call-template>",
            "        </xsl:if>",
            '        <xsl:if test="b:LastAuthor">',
            '          <xsl:call-template name="templ_prop_SecondaryClose"/>',
            "        </xsl:if>",
            '        <xsl:if test="not(b:LastAuthor)">',
            '          <xsl:call-template name="templ_prop_ListSeparator"/>',
            '          <xsl:call-template name="templ_prop_Space"/>',
            "        </xsl:if>",
            "      </body>",
            "    </html>",
            "  </xsl:template>",
            "",
            *self._render_bibliography_templates(bibliography_fragment),
            "</xsl:stylesheet>",
            "",
        ]
        return "\n".join(line for line in lines if line is not None)

    def _compile_bibliography_layout(self) -> Fragment:
        layout = self.style.bibliography_layout
        children = self._bibliography_layout_children()
        fragment = self._compile_sequence(children, delimiter=layout.attrib.get("delimiter", ""))
        return self._wrap_fragment(fragment, layout)

    def _compile_reference_table_title_fragment(self) -> Fragment:
        return self._compile_reference_table_fragment(keep_title_like=True)

    def _compile_reference_table_remainder_fragment(self) -> Fragment:
        return self._compile_reference_table_fragment(keep_title_like=False)

    def _compile_reference_table_fragment(self, *, keep_title_like: bool) -> Fragment:
        layout = deepcopy(self.style.bibliography_layout)
        children: list[XmlElementTree.Element] = []
        for child in list(layout):
            filtered_child, includes_target = self._filter_reference_table_node(
                child, keep_title_like=keep_title_like
            )
            if filtered_child is not None and includes_target:
                children.append(filtered_child)
        fragment = self._compile_sequence(children, delimiter=layout.attrib.get("delimiter", ""))
        return self._wrap_fragment(fragment, layout)

    def _bibliography_layout_children(self) -> list[XmlElementTree.Element]:
        children = list(self.style.bibliography_layout)
        if children:
            first = children[0]
            if (
                _local_name(first.tag) == "text"
                and first.attrib.get("variable") == "citation-number"
            ):
                children = children[1:]
        return children

    def _compile_optional_macro_fragment(self, name: str) -> Fragment:
        macro = self.style.macros.get(name)
        if macro is None:
            return self._compile_literal_fragment("")
        return self._compile_sequence(list(macro), delimiter=macro.attrib.get("delimiter", ""))

    def _compile_bibliography_revision_fragment(self) -> Fragment:
        return self._compile_first_nonempty_fragments(
            [
                self._compile_text_variable_fragment("version"),
                self._compile_optional_macro_fragment("edition"),
                self._compile_optional_macro_fragment("issued"),
            ]
        )

    def _compile_bibliography_document_number_fragment(self) -> Fragment:
        fragments = [
            self._compile_text_variable_fragment("number"),
            self._compile_text_variable_fragment("standard-number"),
            self._compile_text_variable_fragment("DOI"),
        ]
        return self._compile_fragment_sequence(fragments, delimiter="; ")

    def _compile_literal_fragment(self, value: str) -> Fragment:
        content_name = self._new_var("text")
        lines = [f'    <xsl:variable name="{content_name}">']
        lines.extend(self._text_lines(value, 6))
        lines.append("    </xsl:variable>")
        return Fragment(
            lines,
            content_name,
            self._fragment_has_value(content_name),
            "false()",
        )

    def _compile_text_variable_fragment(self, variable: str) -> Fragment:
        node = XmlElementTree.Element(f"{{{CSL_NS}}}text", {"variable": variable})
        return self._compile_text(node)

    def _filter_reference_table_node(
        self, node: XmlElementTree.Element, *, keep_title_like: bool
    ) -> tuple[XmlElementTree.Element | None, bool]:
        tag = _local_name(node.tag)
        if tag == "text":
            macro = node.attrib.get("macro")
            if macro is not None:
                if macro in {"author", "access"}:
                    return None, False
                is_title_like = macro in REFERENCE_TABLE_TITLE_MACROS
                if is_title_like == keep_title_like:
                    return deepcopy(node), True
                return None, False
            variable = node.attrib.get("variable")
            if variable is not None:
                if variable == "citation-number":
                    return None, False
                is_title_like = variable in REFERENCE_TABLE_TITLE_VARIABLES
                if is_title_like == keep_title_like:
                    return deepcopy(node), True
                return None, False
            return deepcopy(node), False
        if tag in {"number", "label", "date", "names"}:
            variable = node.attrib.get("variable", "")
            if variable == "citation-number":
                return None, False
            is_title_like = variable in REFERENCE_TABLE_TITLE_VARIABLES
            if is_title_like == keep_title_like:
                return deepcopy(node), True
            return None, False

        filtered = XmlElementTree.Element(node.tag, node.attrib)
        filtered.text = node.text
        filtered.tail = node.tail
        includes_target = False
        for child in list(node):
            filtered_child, child_includes_target = self._filter_reference_table_node(
                child, keep_title_like=keep_title_like
            )
            if filtered_child is not None:
                filtered.append(filtered_child)
            includes_target = includes_target or child_includes_target
        if includes_target:
            return filtered, True
        return None, False

    def _compile_fragment_sequence(self, fragments: list[Fragment], delimiter: str) -> Fragment:
        active_fragments = [
            fragment for fragment in fragments if fragment.display_test != "false()"
        ]
        if not active_fragments:
            return self._compile_literal_fragment("")
        result_name = self._new_var("seq")
        lines: list[str] = []
        for fragment in active_fragments:
            lines.extend(fragment.setup_lines)
        lines.append(f'    <xsl:variable name="{result_name}">')
        for index, fragment in enumerate(active_fragments):
            prior = " or ".join(f"({item.display_test})" for item in active_fragments[:index])
            lines.append(f'      <xsl:if test="{fragment.display_test}">')
            if delimiter and prior:
                lines.append(f'        <xsl:if test="{prior}">')
                lines.extend(self._text_lines(delimiter, 10))
                lines.append("        </xsl:if>")
            lines.append(f'        <xsl:value-of select="string(${fragment.variable_name})"/>')
            lines.append("      </xsl:if>")
        lines.append("    </xsl:variable>")
        return Fragment(
            lines,
            result_name,
            self._fragment_has_value(result_name),
            self._fragment_has_value(result_name),
        )

    def _compile_first_nonempty_fragments(self, fragments: list[Fragment]) -> Fragment:
        active_fragments = [
            fragment for fragment in fragments if fragment.display_test != "false()"
        ]
        if not active_fragments:
            return self._compile_literal_fragment("")
        result_name = self._new_var("choose")
        lines: list[str] = []
        for fragment in active_fragments:
            lines.extend(fragment.setup_lines)
        lines.append(f'    <xsl:variable name="{result_name}">')
        lines.append("      <xsl:choose>")
        for fragment in active_fragments:
            lines.append(f'        <xsl:when test="{fragment.display_test}">')
            lines.append(f'          <xsl:value-of select="string(${fragment.variable_name})"/>')
            lines.append("        </xsl:when>")
        lines.append("      </xsl:choose>")
        lines.append("    </xsl:variable>")
        return Fragment(
            lines,
            result_name,
            self._fragment_has_value(result_name),
            self._fragment_has_value(result_name),
        )

    def _render_macro_template(self, name: str, macro: XmlElementTree.Element) -> str:
        fragment = self._compile_sequence(list(macro), delimiter=macro.attrib.get("delimiter", ""))
        lines = [
            f'  <xsl:template name="{self._macro_template_name(name)}">',
            *self._indent(fragment.setup_lines, 2),
            f'    <xsl:if test="{fragment.display_test}">',
            f'      <xsl:value-of select="string(${fragment.variable_name})"/>',
            "    </xsl:if>",
            "  </xsl:template>",
        ]
        return "\n".join(lines)

    def _compile_node(self, node: XmlElementTree.Element) -> Fragment:
        tag = _local_name(node.tag)
        if tag == "layout":
            return self._wrap_fragment(
                self._compile_sequence(list(node), delimiter=node.attrib.get("delimiter", "")),
                node,
            )
        if tag == "group":
            return self._wrap_fragment(
                self._compile_sequence(list(node), delimiter=node.attrib.get("delimiter", "")),
                node,
            )
        if tag == "text":
            return self._compile_text(node)
        if tag == "number":
            return self._compile_number(node)
        if tag == "label":
            return self._compile_label(node)
        if tag == "date":
            return self._compile_date(node)
        if tag == "names":
            return self._compile_names(node)
        if tag == "choose":
            return self._compile_choose(node)
        raise ConversionError(f"Unsupported CSL element <{tag}>.")

    def _compile_sequence(
        self, children: list[XmlElementTree.Element], delimiter: str
    ) -> Fragment:
        child_fragments = [self._compile_node(child) for child in children]
        result_name = self._new_var("seq")
        lines: list[str] = []
        for fragment in child_fragments:
            lines.extend(fragment.setup_lines)
        lines.append(f'    <xsl:variable name="{result_name}">')
        for index, fragment in enumerate(child_fragments):
            condition = fragment.display_test
            prior = " or ".join(f"({f.display_test})" for f in child_fragments[:index])
            lines.append(f'      <xsl:if test="{condition}">')
            if delimiter and prior:
                lines.append(f'        <xsl:if test="{prior}">')
                lines.extend(self._text_lines(delimiter, 10))
                lines.append("        </xsl:if>")
            lines.append(f'        <xsl:value-of select="string(${fragment.variable_name})"/>')
            lines.append("      </xsl:if>")
        lines.append("    </xsl:variable>")
        contribution_terms = [
            f"({fragment.contribution_test})"
            for fragment in child_fragments
            if fragment.contribution_test != "false()"
        ]
        contribution_test = (
            " or ".join(contribution_terms)
            if contribution_terms
            else self._fragment_has_value(result_name)
        )
        return Fragment(lines, result_name, contribution_test, contribution_test)

    def _compile_text(self, node: XmlElementTree.Element) -> Fragment:
        content_name = self._new_var("text")
        lines = [f'    <xsl:variable name="{content_name}">']
        display_test = self._fragment_has_value(content_name)
        contribution_test = "false()"
        if "value" in node.attrib:
            lines.extend(self._text_lines(node.attrib["value"], 6))
        elif "macro" in node.attrib:
            lines.append(
                f'      <xsl:call-template name="{self._macro_template_name(node.attrib["macro"])}"/>'
            )
            contribution_test = self._fragment_has_value(content_name)
        elif "term" in node.attrib:
            term_value = self._resolve_term(node.attrib["term"], node.attrib.get("form", "long"))
            lines.extend(self._text_lines(term_value, 6))
        elif "variable" in node.attrib:
            lines.extend(self._emit_variable_value(node.attrib["variable"], indent=6))
            contribution_test = self._variable_presence(node.attrib["variable"])
        else:
            raise ConversionError("<text> must provide value, macro, term, or variable.")
        lines.append("    </xsl:variable>")
        return self._apply_text_decorations(
            content_name, node, lines, display_test, contribution_test
        )

    def _compile_number(self, node: XmlElementTree.Element) -> Fragment:
        variable = node.attrib.get("variable")
        if not variable:
            raise ConversionError("<number> requires a variable attribute.")
        content_name = self._new_var("number")
        lines = [f'    <xsl:variable name="{content_name}">']
        if node.attrib.get("form") == "ordinal":
            raw_name = self._new_var("number_raw")
            lines.append(f'      <xsl:variable name="{raw_name}">')
            lines.extend(self._emit_variable_value(variable, indent=8))
            lines.append("      </xsl:variable>")
            lines.append('      <xsl:call-template name="ordinalize">')
            lines.append(f'        <xsl:with-param name="value" select="string(${raw_name})"/>')
            lines.append("      </xsl:call-template>")
        else:
            lines.extend(self._emit_variable_value(variable, indent=6))
        lines.append("    </xsl:variable>")
        display_test = self._fragment_has_value(content_name)
        return self._apply_text_decorations(
            content_name, node, lines, display_test, self._variable_presence(variable)
        )

    def _compile_label(self, node: XmlElementTree.Element) -> Fragment:
        variable = node.attrib.get("variable", "")
        content_name = self._new_var("label")
        term = self._resolve_label_term(variable, node.attrib.get("form", "long"))
        lines = [f'    <xsl:variable name="{content_name}">']
        if term:
            lines.extend(self._text_lines(term, 6))
        lines.append("    </xsl:variable>")
        return self._apply_text_decorations(
            content_name,
            node,
            lines,
            self._fragment_has_value(content_name),
            "false()",
        )

    def _compile_date(self, node: XmlElementTree.Element) -> Fragment:
        variable = node.attrib.get("variable")
        if not variable:
            raise ConversionError("<date> requires a variable attribute.")
        parts = DATE_VARIABLE_PARTS.get(variable)
        if parts is None:
            raise ConversionError(f"Unsupported date variable {variable!r}.")
        content_name = self._new_var("date")
        lines = [f'    <xsl:variable name="{content_name}">']
        rendered_parts: list[tuple[str, list[str]]] = []
        for child in node.findall("csl:date-part", NS):
            part_name = child.attrib.get("name")
            if not part_name or part_name not in parts:
                continue
            part_var = self._new_var(f"date_{part_name}")
            part_lines = [f'      <xsl:variable name="{part_var}">']
            path = parts[part_name]
            if part_name == "month":
                form = child.attrib.get("form", "long")
                part_lines.append('        <xsl:call-template name="month-name">')
                part_lines.append(f'          <xsl:with-param name="value" select="{path}"/>')
                part_lines.append(f'          <xsl:with-param name="form" select="\'{form}\'"/>')
                part_lines.append("        </xsl:call-template>")
            else:
                part_lines.append(f'        <xsl:value-of select="{path}"/>')
            part_lines.append("      </xsl:variable>")
            wrapped = self._wrap_existing_var(
                part_var,
                child,
                self._fragment_has_value(part_var),
                self._fragment_has_value(part_var),
            )
            rendered_parts.append((wrapped.variable_name, part_lines + wrapped.setup_lines))

        for _, part_lines in rendered_parts:
            lines.extend(part_lines)

        for index, (name, _) in enumerate(rendered_parts):
            prior = " or ".join(
                self._fragment_has_value(existing_name)
                for existing_name, _ in rendered_parts[:index]
            )
            lines.append(f'      <xsl:if test="{self._fragment_has_value(name)}">')
            if index > 0:
                lines.append(f'        <xsl:if test="{prior}">')
                lines.extend(self._text_lines(" ", 10))
                lines.append("        </xsl:if>")
            lines.append(f'        <xsl:value-of select="string(${name})"/>')
            lines.append("      </xsl:if>")
        lines.append("    </xsl:variable>")
        display_test = self._fragment_has_value(content_name)
        return self._apply_text_decorations(
            content_name, node, lines, display_test, self._variable_presence(variable)
        )

    def _compile_names(self, node: XmlElementTree.Element) -> Fragment:
        variables = [part for part in node.attrib.get("variable", "").split() if part]
        if not variables:
            raise ConversionError("<names> requires at least one variable.")
        name_element = node.find("csl:name", NS)
        label_element = node.find("csl:label", NS)
        substitute = node.find("csl:substitute", NS)
        lines: list[str] = []
        content_name = self._new_var("names")
        lines.append(f'    <xsl:variable name="{content_name}">')
        when_clauses: list[tuple[str, str]] = []
        for variable in variables:
            role_path = PERSON_ROLE_PATHS.get(variable)
            if role_path is None:
                continue
            list_fragment = self._compile_name_list(
                variable, role_path, name_element, label_element
            )
            lines.extend(self._indent(list_fragment.setup_lines, 2))
            when_clauses.append((variable, list_fragment.variable_name))

        if when_clauses:
            lines.append("      <xsl:choose>")
            for variable, fragment_name in when_clauses:
                lines.append(
                    f'        <xsl:when test="count({PERSON_ROLE_PATHS[variable]}) &gt; 0">'
                )
                lines.append(f'          <xsl:value-of select="string(${fragment_name})"/>')
                lines.append("        </xsl:when>")
            if substitute is not None:
                substitute_fragment = self._compile_sequence(
                    list(substitute), delimiter=substitute.attrib.get("delimiter", "")
                )
                lines.append("        <xsl:otherwise>")
                lines.extend(self._indent(substitute_fragment.setup_lines, 4))
                lines.append(
                    f'          <xsl:value-of select="string(${substitute_fragment.variable_name})"/>'
                )
                lines.append("        </xsl:otherwise>")
            lines.append("      </xsl:choose>")
        lines.append("    </xsl:variable>")
        contribution_terms = [
            f"(count({PERSON_ROLE_PATHS[variable]}) &gt; 0)" for variable, _ in when_clauses
        ]
        if substitute is not None:
            contribution_terms.append(self._fragment_has_value(content_name))
        contribution_test = (
            " or ".join(contribution_terms)
            if contribution_terms
            else self._fragment_has_value(content_name)
        )
        return self._apply_text_decorations(
            content_name,
            node,
            lines,
            self._fragment_has_value(content_name),
            contribution_test,
        )

    def _compile_name_list(
        self,
        variable: str,
        role_path: str,
        name_element: XmlElementTree.Element | None,
        label_element: XmlElementTree.Element | None,
    ) -> Fragment:
        delimiter = ", "
        and_mode = "text"
        initialize_with = ""
        et_al_min: int | None = None
        et_al_use_first: int | None = None
        if name_element is not None:
            delimiter = name_element.attrib.get("delimiter", delimiter)
            and_mode = name_element.attrib.get("and", and_mode)
            initialize_with = name_element.attrib.get("initialize-with", "")
            if "et-al-min" in name_element.attrib:
                et_al_min = int(name_element.attrib["et-al-min"])
            if "et-al-use-first" in name_element.attrib:
                et_al_use_first = int(name_element.attrib["et-al-use-first"])

        all_count = self._new_var("name_count")
        display_count = self._new_var("display_count")
        rendered = self._new_var("rendered_names")
        lines = [
            f'    <xsl:variable name="{all_count}" select="count({role_path})"/>',
            f'    <xsl:variable name="{display_count}">',
        ]
        if et_al_min is not None and et_al_use_first is not None:
            lines.append(
                f'      <xsl:choose><xsl:when test="${all_count} &gt;= {et_al_min}">{et_al_use_first}</xsl:when><xsl:otherwise><xsl:value-of select="${all_count}"/></xsl:otherwise></xsl:choose>'
            )
        else:
            lines.append(f'      <xsl:value-of select="${all_count}"/>')
        lines.extend(
            [
                "    </xsl:variable>",
                f'    <xsl:variable name="{rendered}">',
                f'      <xsl:for-each select="{role_path}[position() &lt;= number(${display_count})]">',
                '        <xsl:if test="position() &gt; 1">',
                "          <xsl:choose>",
            ]
        )
        if and_mode == "text":
            lines.extend(
                [
                    '            <xsl:when test="position() = last()">',
                    *self._text_lines(" and ", 14),
                    "            </xsl:when>",
                    "            <xsl:otherwise>",
                    *self._text_lines(delimiter, 14),
                    "            </xsl:otherwise>",
                ]
            )
        else:
            lines.extend(self._text_lines(delimiter, 12))
        lines.extend(
            [
                "          </xsl:choose>",
                "        </xsl:if>",
                "        <xsl:choose>",
                '          <xsl:when test="self::b:Person">',
            ]
        )
        lines.extend(self._render_person_name(initialize_with, 12))
        lines.extend(
            [
                "          </xsl:when>",
                "          <xsl:otherwise>",
                '            <xsl:value-of select="normalize-space(.)"/>',
                "          </xsl:otherwise>",
                "        </xsl:choose>",
                "      </xsl:for-each>",
            ]
        )
        if et_al_min is not None and et_al_use_first is not None:
            lines.extend(
                [
                    f'      <xsl:if test="${all_count} &gt; number(${display_count})">',
                    f'        <xsl:if test="number(${display_count}) &gt; 0">',
                    *self._text_lines(delimiter, 10),
                    "        </xsl:if>",
                    *self._text_lines("et al.", 8),
                    "      </xsl:if>",
                ]
            )
        if label_element is not None and variable != "author":
            label_fragment = self._compile_label(label_element)
            lines.extend(label_fragment.setup_lines)
            lines.append(
                f'      <xsl:if test="{self._fragment_has_value(label_fragment.variable_name)}">'
            )
            lines.append(
                f'        <xsl:value-of select="string(${label_fragment.variable_name})"/>'
            )
            lines.append("      </xsl:if>")
        lines.append("    </xsl:variable>")
        return Fragment(
            lines,
            rendered,
            self._fragment_has_value(rendered),
            f"count({role_path}) &gt; 0",
        )

    def _compile_choose(self, node: XmlElementTree.Element) -> Fragment:
        result_name = self._new_var("choose")
        lines = [f'    <xsl:variable name="{result_name}">', "      <xsl:choose>"]
        for child in list(node):
            tag = _local_name(child.tag)
            if tag == "if" or tag == "else-if":
                lines.append(f'        <xsl:when test="{self._build_condition(child)}">')
            elif tag == "else":
                lines.append("        <xsl:otherwise>")
            else:
                raise ConversionError(f"Unsupported <choose> child <{tag}>.")
            branch = self._compile_sequence(
                list(child), delimiter=child.attrib.get("delimiter", "")
            )
            lines.extend(self._indent(branch.setup_lines, 4))
            lines.append(f'          <xsl:value-of select="string(${branch.variable_name})"/>')
            lines.append("        </xsl:otherwise>" if tag == "else" else "        </xsl:when>")
        lines.extend(["      </xsl:choose>", "    </xsl:variable>"])
        result_test = self._fragment_has_value(result_name)
        return self._wrap_fragment(Fragment(lines, result_name, result_test, result_test), node)

    def _emit_variable_value(self, variable: str, indent: int) -> list[str]:
        if variable == "citation-number":
            return self._first_nonempty(("b:RefOrder", "b:Source/b:RefOrder"), indent)
        if variable in TEXT_VARIABLE_PATHS:
            return self._first_nonempty(TEXT_VARIABLE_PATHS[variable], indent)
        if variable in {"publisher-place", "event-place"}:
            return self._emit_joined_fields(
                ("b:City", "b:StateProvince", "b:CountryRegion"), ", ", indent
            )
        if variable in PERSON_ROLE_PATHS:
            return [
                f'{" " * indent}<xsl:value-of select="normalize-space({PERSON_ROLE_PATHS[variable]}[1])"/>'
            ]
        raise ConversionError(f"Unsupported variable {variable!r}.")

    def _resolve_term(self, term: str, form: str) -> str:
        return TERMS.get((term, form), TERMS.get((term, "long"), term))

    def _resolve_label_term(self, variable: str, form: str) -> str:
        if variable == "author":
            return ""
        if variable in {"editor", "translator", "director", "composer"}:
            return TERMS.get((variable, form), variable)
        if variable == "locator":
            return TERMS.get(("page", form), "p." if form == "short" else "page")
        if variable == "chapter-number":
            return TERMS.get(("chapter", form), "ch." if form == "short" else "chapter")
        return TERMS.get((variable, form), variable)

    def _apply_text_decorations(
        self,
        content_name: str,
        node: XmlElementTree.Element,
        lines: list[str],
        display_test: str,
        contribution_test: str,
    ) -> Fragment:
        decorated = self._wrap_existing_var(content_name, node, display_test, contribution_test)
        return Fragment(
            lines + decorated.setup_lines,
            decorated.variable_name,
            decorated.display_test,
            contribution_test,
        )

    def _wrap_fragment(self, fragment: Fragment, node: XmlElementTree.Element) -> Fragment:
        wrapped = self._wrap_existing_var(
            fragment.variable_name,
            node,
            fragment.display_test,
            fragment.contribution_test,
        )
        return Fragment(
            fragment.setup_lines + wrapped.setup_lines,
            wrapped.variable_name,
            wrapped.display_test,
            fragment.contribution_test,
        )

    def _wrap_existing_var(
        self,
        content_name: str,
        node: XmlElementTree.Element,
        display_test: str,
        contribution_test: str,
    ) -> Fragment:
        final_name = self._new_var("wrapped")
        lines = [f'    <xsl:variable name="{final_name}">']
        lines.append(f'      <xsl:if test="{self._fragment_has_value(content_name)}">')
        prefix = node.attrib.get("prefix", "")
        suffix = node.attrib.get("suffix", "")
        quotes = node.attrib.get("quotes") == "true"
        if prefix:
            lines.extend(self._text_lines(prefix, 8))
        if quotes:
            lines.extend(self._text_lines('"', 8))
        text_case = node.attrib.get("text-case")
        if text_case:
            lines.append('        <xsl:call-template name="apply-text-case">')
            lines.append(
                f'          <xsl:with-param name="value" select="string(${content_name})"/>'
            )
            lines.append(
                f'          <xsl:with-param name="mode" select="\'{escape(text_case)}\'"/>'
            )
            lines.append("        </xsl:call-template>")
        else:
            lines.append(f'        <xsl:value-of select="string(${content_name})"/>')
        if quotes:
            lines.extend(self._text_lines('"', 8))
        if suffix:
            lines.extend(self._text_lines(suffix, 8))
        lines.append("      </xsl:if>")
        lines.append("    </xsl:variable>")
        return Fragment(lines, final_name, display_test, contribution_test)

    def _build_condition(self, node: XmlElementTree.Element) -> str:
        clauses: list[str] = []
        match = node.attrib.get("match", "any")
        if "type" in node.attrib:
            word_types: list[str] = []
            for csl_type in node.attrib["type"].split():
                word_types.extend(CSL_TO_WORD_TYPES.get(csl_type, ()))
            if not word_types:
                clauses.append("false()")
            else:
                type_checks = [f"b:SourceType='{escape(word_type)}'" for word_type in word_types]
                clauses.append(self._wrap_match(type_checks, match))
        if "variable" in node.attrib:
            checks = [
                self._variable_presence(variable) for variable in node.attrib["variable"].split()
            ]
            clauses.append(self._wrap_match(checks, match))
        if "is-numeric" in node.attrib:
            checks = [
                f"string(number(normalize-space(({self._value_expression(variable)})))) != 'NaN'"
                for variable in node.attrib["is-numeric"].split()
            ]
            clauses.append(self._wrap_match(checks, match))
        if "locator" in node.attrib:
            locator_checks = [
                f"normalize-space(@locator)='{escape(locator)}' "
                f"or normalize-space(b:LocatorType)='{escape(locator)}' "
                f"or normalize-space(../@locator)='{escape(locator)}' "
                f"or normalize-space(../b:LocatorType)='{escape(locator)}'"
                for locator in node.attrib["locator"].split()
            ]
            clauses.append(self._wrap_match(locator_checks, match))
        if not clauses:
            return "true()"
        return " and ".join(f"({clause})" for clause in clauses)

    def _variable_presence(self, variable: str) -> str:
        if variable in PERSON_ROLE_PATHS:
            return f"count({PERSON_ROLE_PATHS[variable]}) &gt; 0"
        if variable == "citation-number":
            return " or ".join(
                (
                    "string-length(normalize-space(b:RefOrder)) &gt; 0",
                    "string-length(normalize-space(b:Source/b:RefOrder)) &gt; 0",
                )
            )
        if variable == "locator":
            return " or ".join(
                (
                    "string-length(normalize-space(../b:Pages)) &gt; 0",
                    "string-length(normalize-space(../b:PageRange)) &gt; 0",
                    "string-length(normalize-space(b:Pages)) &gt; 0",
                    "string-length(normalize-space(b:PageRange)) &gt; 0",
                )
            )
        if variable in DATE_VARIABLE_PARTS:
            fields = DATE_VARIABLE_PARTS[variable].values()
            return " or ".join(
                f"string-length(normalize-space({field})) &gt; 0" for field in fields
            )
        if variable in {"publisher-place", "event-place"}:
            return " or ".join(
                f"string-length(normalize-space({field})) &gt; 0"
                for field in ("b:City", "b:StateProvince", "b:CountryRegion")
            )
        if variable in TEXT_VARIABLE_PATHS:
            return " or ".join(
                f"string-length(normalize-space({path})) &gt; 0"
                for path in TEXT_VARIABLE_PATHS[variable]
            )
        return "false()"

    def _value_expression(self, variable: str) -> str:
        if variable in TEXT_VARIABLE_PATHS:
            return TEXT_VARIABLE_PATHS[variable][0]
        if variable in {"publisher-place", "event-place"}:
            return "b:City"
        raise ConversionError(f"Unsupported variable {variable!r} in condition.")

    def _wrap_match(self, clauses: Iterable[str], match: str) -> str:
        values = [clause for clause in clauses if clause]
        if not values:
            return "false()"
        if match == "all":
            return " and ".join(f"({clause})" for clause in values)
        if match == "none":
            return " and ".join(f"not({clause})" for clause in values)
        return " or ".join(f"({clause})" for clause in values)

    def _first_nonempty(self, paths: Iterable[str], indent: int) -> list[str]:
        lines = [f"{' ' * indent}<xsl:choose>"]
        for path in paths:
            lines.append(
                f'{" " * (indent + 2)}<xsl:when test="string-length(normalize-space({path})) &gt; 0">'
            )
            lines.append(f'{" " * (indent + 4)}<xsl:value-of select="{path}"/>')
            lines.append(f"{' ' * (indent + 2)}</xsl:when>")
        lines.append(f"{' ' * indent}</xsl:choose>")
        return lines

    def _emit_joined_fields(self, paths: Iterable[str], delimiter: str, indent: int) -> list[str]:
        field_list = list(paths)
        lines = []
        for index, path in enumerate(field_list):
            lines.append(
                f'{" " * indent}<xsl:if test="string-length(normalize-space({path})) &gt; 0">'
            )
            if index > 0:
                prior = " or ".join(
                    f"string-length(normalize-space({existing})) &gt; 0"
                    for existing in field_list[:index]
                )
                lines.append(f'{" " * (indent + 2)}<xsl:if test="{prior}">')
                lines.extend(self._text_lines(delimiter, indent + 4))
                lines.append(f"{' ' * (indent + 2)}</xsl:if>")
            lines.append(f'{" " * (indent + 2)}<xsl:value-of select="{path}"/>')
            lines.append(f"{' ' * indent}</xsl:if>")
        return lines

    def _render_person_name(self, initialize_with: str, indent: int) -> list[str]:
        if initialize_with:
            return [
                f'{" " * indent}<xsl:call-template name="render-given-name-initials">',
                f'{" " * (indent + 2)}<xsl:with-param name="first" select="b:First"/>',
                f'{" " * (indent + 2)}<xsl:with-param name="middle" select="b:Middle"/>',
                f'{" " * (indent + 2)}<xsl:with-param name="initializeWith" select="\'{escape(initialize_with)}\'"/>',
                f"{' ' * indent}</xsl:call-template>",
                f'{" " * indent}<xsl:if test="string-length(normalize-space(b:Last)) &gt; 0">',
                *self._text_lines(" ", indent + 2),
                f"{' ' * indent}</xsl:if>",
                f'{" " * indent}<xsl:value-of select="normalize-space(b:Last)"/>',
            ]
        return [
            f"{' ' * indent}<xsl:value-of select=\"normalize-space(concat(b:First, ' ', b:Middle, ' ', b:Last))\"/>"
        ]

    def _important_fields_templates(self) -> list[str]:
        field_map: dict[str, tuple[str, ...]] = {
            "Book": (
                "b:Author/b:Author/b:NameList",
                "b:Year",
                "b:Title",
                "b:City",
                "b:Publisher",
            ),
            "BookSection": (
                "b:Author/b:Author/b:NameList",
                "b:Year",
                "b:Title",
                "b:BookTitle",
                "b:Pages",
                "b:City",
                "b:Publisher",
            ),
            "JournalArticle": (
                "b:Author/b:Author/b:NameList",
                "b:Year",
                "b:Title",
                "b:JournalName",
                "b:Volume",
                "b:Issue",
                "b:Pages",
            ),
            "ArticleInAPeriodical": (
                "b:Author/b:Author/b:NameList",
                "b:Year",
                "b:Title",
                "b:JournalName",
                "b:Volume",
                "b:Issue",
                "b:Pages",
            ),
            "ConferenceProceedings": (
                "b:Author/b:Author/b:NameList",
                "b:Year",
                "b:Title",
                "b:City",
                "b:ConferenceName",
            ),
            "Report": (
                "b:Author/b:Author/b:NameList",
                "b:Year",
                "b:Title",
                "b:Publisher",
                "b:Number",
            ),
            "InternetSite": (
                "b:Author/b:Author/b:NameList",
                "b:Title",
                "b:Year",
                "b:Month",
                "b:Day",
                "b:URL",
            ),
            "DocumentFromInternetSite": (
                "b:Author/b:Author/b:NameList",
                "b:Title",
                "b:Year",
                "b:Month",
                "b:Day",
                "b:URL",
            ),
            "Patent": (
                "b:Author/b:Inventor/b:NameList",
                "b:Year",
                "b:Title",
                "b:CountryRegion",
                "b:PatentNumber",
                "b:Day",
                "b:Month",
            ),
        }
        lines: list[str] = []
        for source_type, fields in field_map.items():
            lines.append(f"        <xsl:when test=\"b:SourceType='{escape(source_type)}'\">")
            lines.extend(
                [
                    f"          <b:ImportantField>{escape(field)}</b:ImportantField>"
                    for field in fields
                ]
            )
            lines.append("        </xsl:when>")
        return lines

    def _important_fields_default(self) -> tuple[str, ...]:
        return (
            "b:Author/b:Author/b:NameList",
            "b:Title",
            "b:Year",
        )

    def _macro_template_name(self, name: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9_]+", "_", name)
        return f"macro_{safe}"

    def _fragment_has_value(self, variable_name: str) -> str:
        return f"string-length(normalize-space(string(${variable_name}))) &gt; 0"

    def _new_var(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}_{self._counter}"

    def _text_lines(self, value: str, indent: int) -> list[str]:
        if not value:
            return []
        return [f"{' ' * indent}<xsl:text>{escape(value)}</xsl:text>"]

    def _indent(self, lines: Iterable[str], spaces: int) -> list[str]:
        prefix = " " * spaces
        return [f"{prefix}{line}" if line else "" for line in lines]

    def _render_bibliography_cell(
        self, fragment: Fragment, *, cell_class: str, width: str
    ) -> list[str]:
        return [
            f'      <td class="{cell_class}" style="width:{width}">',
            '        <p class="MsoBibliography">',
            *self._indent(fragment.setup_lines, 4),
            f'          <xsl:value-of select="normalize-space(string(${fragment.variable_name}))"/>',
            "        </p>",
            "      </td>",
        ]

    def _render_reference_table_title_cell(self, fragment: Fragment) -> list[str]:
        return [
            '      <td class="MsoBibliographyCell" style="width:39.94%">',
            '        <p class="MsoBibliography">',
            *self._indent(fragment.setup_lines, 4),
            f'          <xsl:value-of select="normalize-space(string(${fragment.variable_name}))"/>',
            "        </p>",
            "      </td>",
        ]

    def _render_reference_table_document_number_cell(self, fragment: Fragment) -> list[str]:
        url_fragment = self._compile_text_variable_fragment("URL")
        return [
            '      <td class="MsoBibliographyCell" style="width:23.40%">',
            '        <p class="MsoBibliography">',
            *self._indent(fragment.setup_lines, 4),
            *self._indent(url_fragment.setup_lines, 4),
            "          <xsl:choose>",
            f'            <xsl:when test="{fragment.display_test} and {url_fragment.display_test}">',
            "              <a>",
            f'                <xsl:attribute name="href"><xsl:value-of select="normalize-space(string(${url_fragment.variable_name}))"/></xsl:attribute>',
            f'                <xsl:value-of select="normalize-space(string(${fragment.variable_name}))"/>',
            "              </a>",
            "            </xsl:when>",
            "            <xsl:otherwise>",
            f'              <xsl:value-of select="normalize-space(string(${fragment.variable_name}))"/>',
            "            </xsl:otherwise>",
            "          </xsl:choose>",
            "        </p>",
            "      </td>",
        ]

    def _render_bibliography_templates(self, bibliography_fragment: Fragment) -> list[str]:
        if self.bibliography_format is BibliographyFormat.REFERENCE_TABLE:
            return self._render_reference_table_bibliography_templates()
        return self._render_standard_bibliography_templates(bibliography_fragment)

    def _style_name(self) -> str:
        if self.bibliography_format is BibliographyFormat.REFERENCE_TABLE:
            return f"{self.style.compact_title}ReferenceTable"
        return self.style.compact_title

    def _style_name_localized(self) -> str:
        if self.bibliography_format is BibliographyFormat.REFERENCE_TABLE:
            return f"{self.style.title} (Reference Table)"
        return self.style.title

    def _render_standard_bibliography_templates(
        self, bibliography_fragment: Fragment
    ) -> list[str]:
        return [
            '  <xsl:template match="b:Bibliography">',
            '    <html xmlns="http://www.w3.org/TR/REC-html40">',
            "      <head>",
            "        <style>",
            "          p.MsoBibliography, li.MsoBibliography, div.MsoBibliography",
            "        </style>",
            "      </head>",
            "      <body>",
            '        <table class="MsoBibliography" width="100%">',
            '          <xsl:apply-templates select="b:Source">',
            '            <xsl:sort select="b:RefOrder" order="ascending" data-type="number"/>',
            "          </xsl:apply-templates>",
            "        </table>",
            "      </body>",
            "    </html>",
            "  </xsl:template>",
            "",
            '  <xsl:template match="b:Source">',
            "    <tr>",
            '      <td style="text-align:right" valign="top">',
            '        <p class="MsoBibliography">',
            '          <xsl:call-template name="bib-ref-order"/>',
            "        </p>",
            "      </td>",
            '      <td style="text-align:left" valign="top">',
            '        <p class="MsoBibliography">',
            *self._indent(bibliography_fragment.setup_lines, 4),
            f'          <xsl:value-of select="normalize-space(string(${bibliography_fragment.variable_name}))"/>',
            "        </p>",
            "      </td>",
            "    </tr>",
            "  </xsl:template>",
            "",
        ]

    def _render_reference_table_bibliography_templates(self) -> list[str]:
        bibliography_author_fragment = self._compile_optional_macro_fragment("author")
        bibliography_revision_fragment = self._compile_bibliography_revision_fragment()
        bibliography_title_fragment = self._compile_reference_table_title_fragment()
        bibliography_document_number_fragment = self._compile_reference_table_remainder_fragment()
        return [
            '  <xsl:template match="b:Bibliography">',
            '    <html xmlns="http://www.w3.org/TR/REC-html40">',
            "      <head>",
            "        <style>",
            "          p.MsoBibliography, li.MsoBibliography, div.MsoBibliography { margin: 0; font-family: Arial; font-size: 10pt; }",
            "          table.MsoBibliography { width: 100%; border-collapse: collapse; border: 1pt solid black; }",
            "          td.MsoBibliographyHeader { border: 1pt solid black; background: #D9D9D9; font-family: Arial; font-size: 10pt; font-weight: bold; text-align: center; vertical-align: bottom; padding: 3pt; }",
            "          td.MsoBibliographyCell { border: 1pt solid black; font-family: Arial; font-size: 10pt; text-align: left; vertical-align: bottom; padding: 3pt; }",
            "          td.MsoBibliographyRef { border: 1pt solid black; font-family: Arial; font-size: 10pt; text-align: center; vertical-align: bottom; padding: 3pt; }",
            "        </style>",
            "      </head>",
            "      <body>",
            '        <table class="MsoBibliography" width="100%">',
            "          <tr>",
            '            <td class="MsoBibliographyHeader" style="width:9.68%">Reference Number</td>',
            '            <td class="MsoBibliographyHeader" style="width:15.30%">Author</td>',
            '            <td class="MsoBibliographyHeader" style="width:11.68%">Issue Date, Edition or Revision</td>',
            '            <td class="MsoBibliographyHeader" style="width:39.94%">Title</td>',
            '            <td class="MsoBibliographyHeader" style="width:23.40%">Document Number</td>',
            "          </tr>",
            '          <xsl:apply-templates select="b:Source">',
            '            <xsl:sort select="b:RefOrder" order="ascending" data-type="number"/>',
            "          </xsl:apply-templates>",
            "        </table>",
            "      </body>",
            "    </html>",
            "  </xsl:template>",
            "",
            '  <xsl:template match="b:Source">',
            "    <tr>",
            '      <td class="MsoBibliographyRef" style="width:9.68%">',
            '        <p class="MsoBibliography">',
            '          <xsl:value-of select="b:RefOrder"/>',
            "        </p>",
            "      </td>",
            *self._render_bibliography_cell(
                bibliography_author_fragment,
                cell_class="MsoBibliographyCell",
                width="15.30%",
            ),
            *self._render_bibliography_cell(
                bibliography_revision_fragment,
                cell_class="MsoBibliographyCell",
                width="11.68%",
            ),
            *self._render_reference_table_title_cell(bibliography_title_fragment),
            *self._render_reference_table_document_number_cell(
                bibliography_document_number_fragment
            ),
            "    </tr>",
            "  </xsl:template>",
            "",
        ]

    def _helper_templates(self) -> str:
        return """  <xsl:template name="apply-text-case">
    <xsl:param name="value"/>
    <xsl:param name="mode"/>
    <xsl:choose>
      <xsl:when test="$mode='uppercase'">
        <xsl:value-of select="translate($value, 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')"/>
      </xsl:when>
      <xsl:when test="$mode='lowercase'">
        <xsl:value-of select="translate($value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"/>
      </xsl:when>
      <xsl:when test="$mode='capitalize-first' or $mode='sentence'">
        <xsl:variable name="first" select="substring($value, 1, 1)"/>
        <xsl:variable name="rest" select="substring($value, 2)"/>
        <xsl:value-of select="concat(translate($first, 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), $rest)"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$value"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="ordinalize">
    <xsl:param name="value"/>
    <xsl:variable name="mod100" select="number($value) mod 100"/>
    <xsl:variable name="mod10" select="number($value) mod 10"/>
    <xsl:value-of select="$value"/>
    <xsl:choose>
      <xsl:when test="$mod100 = 11 or $mod100 = 12 or $mod100 = 13">th</xsl:when>
      <xsl:when test="$mod10 = 1">st</xsl:when>
      <xsl:when test="$mod10 = 2">nd</xsl:when>
      <xsl:when test="$mod10 = 3">rd</xsl:when>
      <xsl:otherwise>th</xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="month-name">
    <xsl:param name="value"/>
    <xsl:param name="form"/>
    <xsl:choose>
      <xsl:when test="$value='1' or $value='01'"><xsl:choose><xsl:when test="$form='short'">Jan.</xsl:when><xsl:otherwise>January</xsl:otherwise></xsl:choose></xsl:when>
      <xsl:when test="$value='2' or $value='02'"><xsl:choose><xsl:when test="$form='short'">Feb.</xsl:when><xsl:otherwise>February</xsl:otherwise></xsl:choose></xsl:when>
      <xsl:when test="$value='3' or $value='03'"><xsl:choose><xsl:when test="$form='short'">Mar.</xsl:when><xsl:otherwise>March</xsl:otherwise></xsl:choose></xsl:when>
      <xsl:when test="$value='4' or $value='04'"><xsl:choose><xsl:when test="$form='short'">Apr.</xsl:when><xsl:otherwise>April</xsl:otherwise></xsl:choose></xsl:when>
      <xsl:when test="$value='5' or $value='05'">May</xsl:when>
      <xsl:when test="$value='6' or $value='06'"><xsl:choose><xsl:when test="$form='short'">Jun.</xsl:when><xsl:otherwise>June</xsl:otherwise></xsl:choose></xsl:when>
      <xsl:when test="$value='7' or $value='07'"><xsl:choose><xsl:when test="$form='short'">Jul.</xsl:when><xsl:otherwise>July</xsl:otherwise></xsl:choose></xsl:when>
      <xsl:when test="$value='8' or $value='08'"><xsl:choose><xsl:when test="$form='short'">Aug.</xsl:when><xsl:otherwise>August</xsl:otherwise></xsl:choose></xsl:when>
      <xsl:when test="$value='9' or $value='09'"><xsl:choose><xsl:when test="$form='short'">Sep.</xsl:when><xsl:otherwise>September</xsl:otherwise></xsl:choose></xsl:when>
      <xsl:when test="$value='10'"><xsl:choose><xsl:when test="$form='short'">Oct.</xsl:when><xsl:otherwise>October</xsl:otherwise></xsl:choose></xsl:when>
      <xsl:when test="$value='11'"><xsl:choose><xsl:when test="$form='short'">Nov.</xsl:when><xsl:otherwise>November</xsl:otherwise></xsl:choose></xsl:when>
      <xsl:when test="$value='12'"><xsl:choose><xsl:when test="$form='short'">Dec.</xsl:when><xsl:otherwise>December</xsl:otherwise></xsl:choose></xsl:when>
      <xsl:otherwise><xsl:value-of select="$value"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="render-given-name-initials">
    <xsl:param name="first"/>
    <xsl:param name="middle"/>
    <xsl:param name="initializeWith"/>
    <xsl:if test="string-length(normalize-space($first)) &gt; 0">
      <xsl:value-of select="substring(normalize-space($first), 1, 1)"/>
      <xsl:value-of select="$initializeWith"/>
    </xsl:if>
    <xsl:if test="string-length(normalize-space($middle)) &gt; 0">
      <xsl:if test="string-length(normalize-space($first)) &gt; 0">
        <xsl:text> </xsl:text>
      </xsl:if>
      <xsl:value-of select="substring(normalize-space($middle), 1, 1)"/>
      <xsl:value-of select="$initializeWith"/>
    </xsl:if>
  </xsl:template>

  <xsl:template name="templ_prop_SecondaryOpen">
    <xsl:value-of select="/*/b:Locals/b:Local[1]/b:APA/b:SecondaryOpen"/>
  </xsl:template>

  <xsl:template name="templ_prop_SecondaryClose">
    <xsl:value-of select="/*/b:Locals/b:Local[1]/b:APA/b:SecondaryClose"/>
  </xsl:template>

  <xsl:template name="templ_prop_ListSeparator">
    <xsl:value-of select="/*/b:Locals/b:Local[1]/b:General/b:ListSeparator"/>
  </xsl:template>

  <xsl:template name="templ_prop_Space">
    <xsl:value-of select="/*/b:Locals/b:Local[1]/b:General/b:Space"/>
  </xsl:template>

  <xsl:template name="display-page-or-pages">
    <xsl:param name="pages"/>
    <xsl:if test="string-length(normalize-space($pages)) &gt; 0">
      <xsl:call-template name="templ_prop_ListSeparator"/>
      <xsl:choose>
        <xsl:when test="contains($pages, '-') or contains($pages, ',')">
          <xsl:text>pp. </xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>p. </xsl:text>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:value-of select="$pages"/>
    </xsl:if>
  </xsl:template>

  <xsl:template name="bib-ref-order">
    <xsl:call-template name="templ_prop_SecondaryOpen"/>
    <xsl:value-of select="b:RefOrder"/>
    <xsl:call-template name="templ_prop_SecondaryClose"/>
    <xsl:call-template name="templ_prop_Space"/>
  </xsl:template>"""


def _require_text(parent: XmlElementTree.Element, path: str) -> str:
    child = parent.find(path, NS)
    if child is None or child.text is None or not child.text.strip():
        raise ConversionError(f"Style metadata is missing required element {path}.")
    return str(child.text.strip())


def _validate_supported_tags(root: XmlElementTree.Element) -> None:
    for element in root.iter():
        local_name = _local_name(element.tag)
        if local_name not in SUPPORTED_TAGS:
            raise ConversionError(f"Unsupported CSL element <{local_name}>.")


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]

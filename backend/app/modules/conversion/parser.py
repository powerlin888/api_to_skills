import logging
import re
import tempfile
from pathlib import Path
from app.core.config import get_settings

logger = logging.getLogger(__name__)

LAYOUT_CHUNK_PAGES = 15
LAYOUT_MAX_FULL_PAGES = 30


class PdfParser:
    def __init__(self, language: str = "en"):
        self.settings = get_settings()
        self.language = language
        self._nlp = None
        self._layout = None

    def _ensure_layout(self):
        if self._layout is None:
            import spacy
            from spacy_layout import spaCyLayout
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.datamodel.base_models import InputFormat
            from docling.document_converter import PdfFormatOption

            pipeline_opts = PdfPipelineOptions(force_backend_text=True, do_ocr=False, do_table_structure=False)
            docling_opts = {InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_opts)}

            self._nlp = spacy.blank(self.language)
            self._layout = spaCyLayout(self._nlp, docling_options=docling_opts)
        return self._layout

    def validate_file(self, filename: str, file_size: int) -> tuple[bool, str]:
        if not filename.lower().endswith(".pdf"):
            return False, "仅支持PDF文件"
        max_bytes = self.settings.MAX_PDF_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            return False, f"文件大小超过{self.settings.MAX_PDF_SIZE_MB}MB限制"
        return True, ""

    def parse(self, pdf_path: Path) -> str:
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)
        logger.info(f"[PDF] 总页数: {total_pages}")

        try:
            if total_pages <= LAYOUT_MAX_FULL_PAGES:
                logger.info(f"[PDF] 页数<=阈值({LAYOUT_MAX_FULL_PAGES}), 使用 spaCy-layout 全量解析")
                markdown = self._parse_with_docling(pdf_path)
            else:
                logger.info(f"[PDF] 页数>阈值({LAYOUT_MAX_FULL_PAGES}), 使用 spaCy-layout 分块解析 (每块{LAYOUT_CHUNK_PAGES}页)")
                markdown = self._parse_with_docling_chunked(pdf_path, reader, total_pages)
        except Exception as e:
            logger.warning(f"[PDF] spaCy-layout 解析失败: {e}, 降级到 pypdf")
            markdown = self._parse_with_pypdf(reader, total_pages)

        if not markdown or len(markdown.strip()) < 10:
            raise ValueError("PDF解析结果为空或内容过少")
        return self._clean_markdown(markdown)

    def _parse_with_pypdf(self, reader, total_pages: int) -> str:
        logger.info(f"[pypdf] 开始解析 {total_pages} 页...")

        pages_text = []
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text()
                if text and text.strip():
                    pages_text.append(f"## 第{i+1}页\n\n{text.strip()}")
            except Exception as e:
                logger.warning(f"[pypdf] 第{i+1}页解析失败: {e}")

        full_text = "\n\n".join(pages_text)
        logger.info(f"[pypdf] 解析完成: {total_pages} 页, {len(full_text)} 字符")
        return full_text

    def _parse_with_docling(self, pdf_path: Path) -> str:
        layout = self._ensure_layout()
        doc = layout(str(pdf_path))
        markdown = doc._.markdown
        if not markdown or len(markdown.strip()) < 10:
            raise ValueError("spaCy-layout 解析结果为空或内容过少")
        logger.info(f"[spaCy-layout] 全量解析完成: {len(markdown)} 字符")
        return markdown

    def _parse_with_docling_chunked(self, pdf_path: Path, reader, total_pages: int) -> str:
        from pypdf import PdfWriter

        layout = self._ensure_layout()
        all_markdown = []

        for start in range(0, total_pages, LAYOUT_CHUNK_PAGES):
            end = min(start + LAYOUT_CHUNK_PAGES, total_pages)
            logger.info(f"[spaCy-layout] 处理第 {start+1}-{end}/{total_pages} 页")

            writer = PdfWriter()
            for i in range(start, end):
                writer.add_page(reader.pages[i])

            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                    tmp_path = tmp.name
                writer.write(tmp_path)

                doc = layout(str(tmp_path))
                md = doc._.markdown
                if md and md.strip():
                    all_markdown.append(md.strip())
            finally:
                if tmp_path:
                    Path(tmp_path).unlink(missing_ok=True)

        result = "\n\n".join(all_markdown)
        logger.info(f"[spaCy-layout] 分块解析完成: {total_pages} 页, {len(all_markdown)} 块, {len(result)} 字符")
        return result

    @staticmethod
    def _clean_markdown(md: str) -> str:
        def _normalize_sep(match: re.Match) -> str:
            sep = match.group(0)
            sep = re.sub(r'-{10,}', '---', sep)
            sep = re.sub(r':-{10,}', ':---', sep)
            sep = re.sub(r'-{10,}:', '---:', sep)
            return sep

        md = re.sub(r'^\|[- :]+\|\s*$', _normalize_sep, md, flags=re.MULTILINE)
        return md

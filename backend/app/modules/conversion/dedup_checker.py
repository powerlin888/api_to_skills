import re
import enum
import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.shared.dao.models import PdfGuide, SkillGroup
from app.shared.dao.dao import GuideDAO, SkillDAO

logger = logging.getLogger(__name__)


class DedupMatchType(str, enum.Enum):
    NONE = "none"
    EXACT = "exact"
    SIMILAR = "similar"


class SkillsGroupNotFoundError(Exception):
    pass


@dataclass
class DedupResult:
    match_type: DedupMatchType = DedupMatchType.NONE
    existing_guide_id: Optional[str] = None
    existing_group_id: Optional[str] = None
    similarity: Optional[float] = None
    similar_guide_name: Optional[str] = None
    degraded: bool = False
    degradation_reason: Optional[str] = None


@dataclass
class SimilarGuide:
    guide_id: str
    guide_name: str
    group_id: str
    similarity: float


class DedupChecker:
    def __init__(self, db: AsyncSession, similarity_threshold: float = 0.95,
                 similarity_timeout: int = 10, max_guides_to_compare: int = 50):
        self.db = db
        self.guide_dao = GuideDAO(db)
        self.skill_dao = SkillDAO(db)
        self.similarity_threshold = similarity_threshold
        self.similarity_timeout = similarity_timeout
        self.max_guides_to_compare = max_guides_to_compare

    @staticmethod
    def compute_hash(markdown_content: str) -> str:
        normalized = markdown_content.strip()
        normalized = normalized.replace('\r\n', '\n').replace('\r', '\n')
        lines = [line.rstrip() for line in normalized.split('\n')]
        compressed = []
        prev_blank = False
        for line in lines:
            if line == '':
                if not prev_blank:
                    compressed.append('')
                prev_blank = True
            else:
                compressed.append(line)
                prev_blank = False
        result = '\n'.join(compressed)
        return hashlib.sha256(result.encode('utf-8')).hexdigest()

    @staticmethod
    def tokenize(text: str) -> set[str]:
        pattern = r'[a-zA-Z][a-zA-Z0-9_-]*|[\u4e00-\u9fff]|[0-9]+'
        tokens = re.findall(pattern, text)
        result = set()
        for t in tokens:
            if re.match(r'^[a-zA-Z]', t):
                lower = t.lower()
                if len(lower) >= 2 or re.search(r'[0-9]', t):
                    result.add(lower)
            else:
                result.add(t)
        return result

    @classmethod
    def compute_similarity(cls, text_a: str, text_b: str) -> float:
        tokens_a = cls.tokenize(text_a)
        tokens_b = cls.tokenize(text_b)
        if not tokens_a and not tokens_b:
            return 1.0
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b
        return len(intersection) / len(union)

    async def _find_similar_guides(self, markdown: str,
                                    existing_guides: list[PdfGuide]) -> list[SimilarGuide]:
        results = []
        for guide in existing_guides:
            try:
                md_path = Path(guide.markdown_path) if guide.markdown_path else None
                if not md_path or not md_path.exists():
                    logger.warning(f"Markdown文件不存在: {guide.markdown_path}")
                    continue
                existing_md = md_path.read_text(encoding='utf-8')
                sim = self.compute_similarity(markdown, existing_md)
                if sim >= self.similarity_threshold:
                    sg_result = await self.db.execute(
                        select(SkillGroup).where(SkillGroup.guide_id == guide.id)
                    )
                    group = sg_result.scalar_one_or_none()
                    if group:
                        results.append(SimilarGuide(
                            guide_id=guide.id,
                            guide_name=guide.original_name,
                            group_id=group.id,
                            similarity=sim
                        ))
            except Exception as e:
                logger.warning(f"比较指南{guide.id}时出错: {e}")
                continue
        results.sort(key=lambda x: x.similarity, reverse=True)
        return results

    async def check_dedup(self, markdown: str, user_id: str) -> DedupResult:
        try:
            content_hash = self.compute_hash(markdown)
            existing = await self.guide_dao.find_by_content_hash(user_id, content_hash)
            if existing:
                sg_result = await self.db.execute(
                    select(SkillGroup).where(SkillGroup.guide_id == existing.id).limit(1)
                )
                group = sg_result.scalar_one_or_none()
                if not group:
                    raise SkillsGroupNotFoundError(
                        f"指南{existing.id}匹配但关联Skills群不存在"
                    )
                return DedupResult(
                    match_type=DedupMatchType.EXACT,
                    existing_guide_id=existing.id,
                    existing_group_id=group.id,
                    similar_guide_name=existing.original_name,
                )

            try:
                candidates = await self.guide_dao.list_with_content_hash(
                    user_id, limit=self.max_guides_to_compare
                )
                similar_guides = await asyncio.wait_for(
                    self._find_similar_guides(markdown, candidates),
                    timeout=self.similarity_timeout
                )
            except asyncio.TimeoutError:
                return DedupResult(
                    match_type=DedupMatchType.NONE,
                    degraded=True,
                    degradation_reason="similarity_timeout"
                )

            if similar_guides:
                best = similar_guides[0]
                return DedupResult(
                    match_type=DedupMatchType.SIMILAR,
                    existing_guide_id=best.guide_id,
                    existing_group_id=best.group_id,
                    similarity=best.similarity,
                    similar_guide_name=best.guide_name,
                )

            return DedupResult(match_type=DedupMatchType.NONE)

        except SkillsGroupNotFoundError:
            raise
        except Exception as e:
            logger.warning(f"去重检查异常降级: {e}")
            return DedupResult(
                match_type=DedupMatchType.NONE,
                degraded=True,
                degradation_reason=str(e)
            )

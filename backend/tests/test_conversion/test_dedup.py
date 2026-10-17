import pytest
from app.modules.conversion.dedup_checker import (
    DedupChecker, DedupMatchType, DedupResult, SkillsGroupNotFoundError
)


class TestComputeHash:
    def test_deterministic(self):
        content = "# Hello\n\nWorld"
        h1 = DedupChecker.compute_hash(content)
        h2 = DedupChecker.compute_hash(content)
        assert h1 == h2
        assert len(h1) == 64

    def test_normalization_crlf(self):
        h1 = DedupChecker.compute_hash("hello\nworld")
        h2 = DedupChecker.compute_hash("hello\r\nworld")
        assert h1 == h2

    def test_normalization_trailing_whitespace(self):
        h1 = DedupChecker.compute_hash("hello  \nworld  ")
        h2 = DedupChecker.compute_hash("hello\nworld")
        assert h1 == h2

    def test_normalization_consecutive_blank_lines(self):
        h1 = DedupChecker.compute_hash("hello\n\n\n\nworld")
        h2 = DedupChecker.compute_hash("hello\n\nworld")
        assert h1 == h2

    def test_different_content(self):
        h1 = DedupChecker.compute_hash("hello")
        h2 = DedupChecker.compute_hash("world")
        assert h1 != h2


class TestTokenize:
    def test_mixed_cn_en(self):
        tokens = DedupChecker.tokenize("使用FastAPI框架编写API接口 fastapi")
        assert "fastapi" in tokens
        assert "使" in tokens
        assert "用" in tokens
        assert "api" in tokens

    def test_short_en_filtered(self):
        tokens = DedupChecker.tokenize("a x y z")
        assert "a" not in tokens

    def test_numbers_preserved(self):
        tokens = DedupChecker.tokenize("TP1 TP2 config-01")
        assert "tp1" in tokens or "TP1" in tokens or "tp" in tokens
        assert "1" in tokens


class TestComputeSimilarity:
    def test_identical(self):
        sim = DedupChecker.compute_similarity("hello world", "hello world")
        assert sim == 1.0

    def test_disjoint(self):
        sim = DedupChecker.compute_similarity("alpha beta", "gamma delta")
        assert sim == 0.0

    def test_partial(self):
        sim = DedupChecker.compute_similarity("hello world", "hello python")
        assert 0.0 < sim < 1.0

    def test_empty_both(self):
        sim = DedupChecker.compute_similarity("", "")
        assert sim == 1.0

    def test_empty_one(self):
        sim = DedupChecker.compute_similarity("hello", "")
        assert sim == 0.0


class TestCheckDedup:
    @pytest.mark.asyncio
    async def test_no_match_empty_db(self, mocker):
        mock_db = mocker.MagicMock()
        mock_guide_dao = mocker.MagicMock()
        mock_guide_dao.find_by_content_hash.return_value = None
        mock_guide_dao.list_with_content_hash.return_value = []
        mocker.patch.object(DedupChecker, '__init__', lambda self, db: None)
        checker = DedupChecker.__new__(DedupChecker)
        checker.db = mock_db
        checker.guide_dao = mock_guide_dao
        checker.similarity_threshold = 0.95
        checker.similarity_timeout = 10
        checker.max_guides_to_compare = 50
        checker.skill_dao = mocker.MagicMock()
        result = await checker.check_dedup("# New Guide", "user1")
        assert result.match_type == DedupMatchType.NONE

    @pytest.mark.asyncio
    async def test_exact_match(self, mocker):
        from app.shared.dao.models import PdfGuide, SkillGroup
        mock_db = mocker.MagicMock()
        existing = PdfGuide(id="g1", user_id="user1", filename="a.pdf",
                            original_name="a.pdf", file_size=100, content_hash="abc")
        group = SkillGroup(id="sg1", user_id="user1", name="test", dir_path="/tmp")
        mock_guide_dao = mocker.MagicMock()
        mock_guide_dao.find_by_content_hash.return_value = existing
        mock_db.execute.return_value = mocker.MagicMock(
            scalar_one_or_none=mocker.MagicMock(return_value=group)
        )
        mocker.patch.object(DedupChecker, '__init__', lambda self, db: None)
        checker = DedupChecker.__new__(DedupChecker)
        checker.db = mock_db
        checker.guide_dao = mock_guide_dao
        checker.similarity_threshold = 0.95
        checker.similarity_timeout = 10
        checker.max_guides_to_compare = 50
        result = await checker.check_dedup("# Existing", "user1")
        assert result.match_type == DedupMatchType.EXACT
        assert result.existing_guide_id == "g1"

    @pytest.mark.asyncio
    async def test_skills_group_not_found(self, mocker):
        from app.shared.dao.models import PdfGuide
        mock_db = mocker.MagicMock()
        existing = PdfGuide(id="g1", user_id="user1", filename="a.pdf",
                            original_name="a.pdf", file_size=100, content_hash="abc")
        mock_guide_dao = mocker.MagicMock()
        mock_guide_dao.find_by_content_hash.return_value = existing
        mock_db.execute.return_value = mocker.MagicMock(
            scalar_one_or_none=mocker.MagicMock(return_value=None)
        )
        mocker.patch.object(DedupChecker, '__init__', lambda self, db: None)
        checker = DedupChecker.__new__(DedupChecker)
        checker.db = mock_db
        checker.guide_dao = mock_guide_dao
        checker.similarity_threshold = 0.95
        checker.similarity_timeout = 10
        checker.max_guides_to_compare = 50
        with pytest.raises(SkillsGroupNotFoundError):
            await checker.check_dedup("# Existing", "user1")

    @pytest.mark.asyncio
    async def test_db_error_degradation(self, mocker):
        mock_db = mocker.MagicMock()
        mock_guide_dao = mocker.MagicMock()
        mock_guide_dao.find_by_content_hash.side_effect = Exception("DB error")
        mocker.patch.object(DedupChecker, '__init__', lambda self, db: None)
        checker = DedupChecker.__new__(DedupChecker)
        checker.db = mock_db
        checker.guide_dao = mock_guide_dao
        checker.similarity_threshold = 0.95
        checker.similarity_timeout = 10
        checker.max_guides_to_compare = 50
        result = await checker.check_dedup("# Guide", "user1")
        assert result.match_type == DedupMatchType.NONE
        assert result.degraded is True

import asyncio
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import async_session
from app.shared.dao.dao import GuideDAO, ConversionTaskDAO, SkillDAO
from app.modules.conversion.parser import PdfParser
from app.modules.conversion.planner import LlmPlanner
from app.modules.conversion.generator import SkillGenerator
from app.modules.conversion.validator import SkillValidator
from app.modules.conversion.dedup_checker import DedupChecker, DedupMatchType, SkillsGroupNotFoundError
from app.shared.dao.models import ConversionStatus

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


class ConversionEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.guide_dao = GuideDAO(db)
        self.task_dao = ConversionTaskDAO(db)
        self.skill_dao = SkillDAO(db)
        self.parser = PdfParser()
        self.generator = SkillGenerator()
        self.validator = SkillValidator()
        self.dedup_checker = DedupChecker(db)
        self.settings = get_settings()

    async def upload_and_convert(self, user_id: str, filename: str, original_name: str,
                                  file_size: int, file_content: bytes,
                                  base_url: str | None = None,
                                  api_key: str | None = None,
                                  model_id: str | None = None) -> dict:
        logger.info(f"[转换] 开始处理: user={user_id}, file={original_name}, size={file_size}")
        valid, msg = self.parser.validate_file(original_name, file_size)
        if not valid:
            logger.warning(f"[转换] 文件验证失败: {msg}")
            raise ValueError(msg)

        pdf_dir = Path(self.settings.PDF_STORAGE_PATH)
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_id = str(uuid.uuid4())
        pdf_path = pdf_dir / f"{pdf_id}.pdf"
        pdf_path.write_bytes(file_content)
        logger.info(f"[转换] PDF已保存: {pdf_path}")

        guide = await self.guide_dao.create(user_id, filename=pdf_path.name,
                                             original_name=original_name, file_size=file_size)
        task = await self.task_dao.create(user_id, guide_id=guide.id)
        logger.info(f"[转换] 任务已创建: task_id={task.id}, guide_id={guide.id}")

        loop = asyncio.get_event_loop()
        loop.create_task(self._run_pipeline_bg(
            task.id, guide.id, user_id, str(pdf_path),
            base_url=base_url, api_key=api_key, model_id=model_id
        ))

        return {"task_id": task.id, "guide_id": guide.id, "status": "pending", "_pdf_path": str(pdf_path)}

    async def _run_pipeline_bg(self, task_id: str, guide_id: str, user_id: str,
                                pdf_path_str: str, **llm_kwargs):
        pdf_path = Path(pdf_path_str)
        logger.info(f"[Pipeline-后台] 启动: task={task_id[:8]}, pdf={pdf_path}")
        async with async_session() as db:
            try:
                engine = ConversionEngine(db)
                await engine._run_pipeline(task_id, guide_id, user_id, pdf_path, **llm_kwargs)
                await db.commit()
            except Exception as e:
                await db.rollback()
                logger.exception(f"[Pipeline-后台] 未捕获异常: task={task_id[:8]}, error={e}")
                try:
                    from app.shared.dao.dao import ConversionTaskDAO
                    from app.shared.dao.models import ConversionStatus
                    dao = ConversionTaskDAO(db)
                    await dao.update(task_id, status=ConversionStatus.FAILED, error_message=str(e))
                    await db.commit()
                except Exception:
                    pass

    async def _run_pipeline(self, task_id: str, guide_id: str, user_id: str,
                            pdf_path: Path, **llm_kwargs):
        try:
            logger.info(f"[Pipeline] 开始: task={task_id[:8]}, guide={guide_id[:8]}")
            # PARSING阶段
            await self.task_dao.update(task_id, status=ConversionStatus.PARSING,
                                       current_stage="parsing", stage_info={"parsing": {"status": "running"}})
            await self.db.commit()
            markdown = self.parser.parse(pdf_path)
            logger.info(f"[Pipeline] PDF解析完成, 内容长度={len(markdown)}")
            md_path = pdf_path.with_suffix(".md")
            md_path.write_text(markdown, encoding="utf-8")
            await self.guide_dao.update(guide_id, markdown_path=str(md_path), status=ConversionStatus.PARSING)
            await self.db.commit()

            # DEDUP_CHECK阶段
            stage_info = {"parsing": {"status": "done"}, "dedup_check": {"status": "running", "message": "正在比对..."}}
            await self.task_dao.update(task_id, status=ConversionStatus.DEDUP_CHECK,
                                       current_stage="dedup_check", stage_info=stage_info)
            await self.db.commit()

            content_hash = DedupChecker.compute_hash(markdown)
            await self.guide_dao.update(guide_id, content_hash=content_hash)
            await self.db.commit()

            try:
                dedup_result = await self.dedup_checker.check_dedup(markdown, user_id)
                logger.info(f"[Pipeline] 去重结果: match_type={dedup_result.match_type}, similarity={dedup_result.similarity}")
            except SkillsGroupNotFoundError as e:
                await self.task_dao.update(task_id, status=ConversionStatus.FAILED,
                                           error_message=str(e))
                await self.guide_dao.update(guide_id, status=ConversionStatus.FAILED)
                await self.db.commit()
                return

            if dedup_result.degraded:
                logger.warning(f"去重检查降级跳过: {dedup_result.degradation_reason}")
                stage_info["dedup_check"] = {"status": "done", "message": f"去重检查降级跳过: {dedup_result.degradation_reason}"}
                await self.task_dao.update(task_id, stage_info=stage_info)
                await self.db.commit()
            elif dedup_result.match_type == DedupMatchType.EXACT:
                stage_info["dedup_check"] = {"status": "done", "message": "内容完全重复"}
                await self.task_dao.update(task_id, status=ConversionStatus.DUPLICATE,
                                           current_stage="duplicate",
                                           result_skill_group_id=dedup_result.existing_group_id,
                                           stage_info=stage_info)
                await self.guide_dao.update(guide_id, status=ConversionStatus.DUPLICATE)
                await self.db.commit()
                return
            elif dedup_result.match_type == DedupMatchType.SIMILAR:
                dedup_pending = {
                    "match_type": "similar",
                    "existing_guide_id": dedup_result.existing_guide_id,
                    "existing_group_id": dedup_result.existing_group_id,
                    "similarity": dedup_result.similarity,
                    "similar_guide_name": dedup_result.similar_guide_name,
                }
                stage_info["dedup_check"] = {"status": "waiting", "message": "发现相似指南，等待用户确认"}
                await self.task_dao.update(task_id, status=ConversionStatus.DEDUP_CHECK,
                                           dedup_pending_info=dedup_pending, stage_info=stage_info)
                await self.db.commit()
                return
            else:
                stage_info["dedup_check"] = {"status": "done", "message": "内容不重复"}
                await self.task_dao.update(task_id, stage_info=stage_info)
                await self.db.commit()

            # ANALYZING及后续阶段
            logger.info(f"[Pipeline] 进入LLM分析阶段")
            await self._run_from_analyzing(task_id, guide_id, user_id, markdown, **llm_kwargs)

        except Exception as e:
            logger.exception(f"[Pipeline] 任务失败: task={task_id[:8]}, error={e}")
            await self.task_dao.update(task_id, status=ConversionStatus.FAILED,
                                       error_message=str(e))
            try:
                await self.guide_dao.update(guide_id, status=ConversionStatus.FAILED)
            except Exception:
                pass

    async def _run_from_analyzing(self, task_id: str, guide_id: str, user_id: str,
                                   markdown: str, **llm_kwargs):
        try:
            logger.info(f"[Pipeline] LLM分析开始: task={task_id[:8]}")
            await self.task_dao.update(task_id, status=ConversionStatus.ANALYZING,
                                       current_stage="analyzing",
                                       stage_info={"dedup_check": {"status": "done"}, "analyzing": {"status": "running"}})
            await self.db.commit()
            planner = LlmPlanner(**llm_kwargs)
            from app.modules.conversion.planner import _split_by_headings
            chunks = _split_by_headings(markdown)
            logger.info(f"[Pipeline] LLM分析开始: task={task_id[:8]}, 文档分为{len(chunks)}段处理")
            plan = await planner.analyze_structure(markdown)
            logger.info(f"[Pipeline] LLM分析完成, plan={plan}")
            skills_plan = planner.plan_skills(plan)
            logger.info(f"[Pipeline] Skills规划完成, 数量={len(skills_plan) if skills_plan else 0}")
            if not skills_plan:
                await self.task_dao.update(task_id, status=ConversionStatus.FAILED,
                                           error_message="LLM未生成任何Skills规划")
                await self.db.commit()
                return

            await self.task_dao.update(task_id, status=ConversionStatus.GENERATING,
                                       current_stage="generating")
            await self.db.commit()
            guide = await self.guide_dao.get_by_id(guide_id)
            guide_name = guide.original_name.replace(".pdf", "") if guide else "guide"
            output_dir = Path(self.settings.SKILLS_STORAGE_PATH) / guide_name
            skill_dirs = self.generator.generate_skills(skills_plan, output_dir, guide_name)

            await self.task_dao.update(task_id, status=ConversionStatus.ENRICHING,
                                       current_stage="enriching",
                                       stage_info={"generating": {"status": "done"}, "enriching": {"status": "running"}})
            await self.db.commit()
            from app.modules.conversion.enricher import enrich_all_skills
            enriched_count = await enrich_all_skills(
                skill_dirs, markdown,
                base_url=llm_kwargs.get("base_url"),
                api_key=llm_kwargs.get("api_key"),
                model_id=llm_kwargs.get("model_id"),
            )
            logger.info(f"[Pipeline] Skills完善完成: {enriched_count}/{len(skill_dirs)}")

            await self.task_dao.update(task_id, status=ConversionStatus.VALIDATING,
                                       current_stage="validating",
                                       stage_info={"enriching": {"status": "done", "enriched": enriched_count}, "validating": {"status": "running"}})
            await self.db.commit()
            for sd in skill_dirs:
                self.validator.validate_all(sd)

            group = await self.skill_dao.create_group(
                user_id=user_id, name=guide_name, dir_path=str(output_dir),
                guide_id=guide_id
            )
            for sd in skill_dirs:
                meta = {}
                skill_md = sd / "SKILL.md"
                if skill_md.exists():
                    import yaml
                    content = skill_md.read_text(encoding="utf-8")
                    if content.startswith("---"):
                        end = content.find("---", 3)
                        if end != -1:
                            try:
                                meta = yaml.safe_load(content[3:end]) or {}
                            except yaml.YAMLError:
                                pass
                await self.skill_dao.create_skill(
                    group_id=group.id, name=sd.name, dir_path=str(sd),
                    description=meta.get("description"), tags=meta.get("tags", [])
                )

            await self.task_dao.update(task_id, status=ConversionStatus.COMPLETED,
                                       current_stage="completed",
                                       result_skill_group_id=group.id)
            await self.guide_dao.update(guide_id, status=ConversionStatus.COMPLETED)
            await self.db.commit()
            logger.info(f"[Pipeline] 全部完成: task={task_id[:8]}, group_id={group.id}")

        except Exception as e:
            logger.exception(f"[Pipeline] 分析/生成阶段失败: task={task_id[:8]}, error={e}")
            await self.task_dao.update(task_id, status=ConversionStatus.FAILED,
                                       error_message=str(e))

    async def _run_from_analyzing_bg(self, task_id: str, guide_id: str, user_id: str,
                                      markdown: str, **llm_kwargs):
        async with async_session() as db:
            try:
                engine = ConversionEngine(db)
                await engine._run_from_analyzing(task_id, guide_id, user_id, markdown, **llm_kwargs)
            except Exception as e:
                logger.exception(f"[Pipeline-后台] 分析阶段未捕获异常: task={task_id[:8]}, error={e}")

    async def continue_conversion(self, task_id: str) -> dict:
        task = await self.task_dao.get_by_id(task_id)
        if not task:
            raise ValueError("任务不存在")
        if task.status != ConversionStatus.DEDUP_CHECK or not task.dedup_pending_info:
            raise ValueError("任务不在等待去重确认状态")
        await self.task_dao.update(task_id, dedup_pending_info=None)
        guide = await self.guide_dao.get_by_id(task.guide_id)
        if not guide or not guide.markdown_path:
            raise ValueError("指南或Markdown文件不存在")
        markdown = Path(guide.markdown_path).read_text(encoding="utf-8")
        asyncio.create_task(self._run_from_analyzing_bg(task_id, task.guide_id, task.user_id, markdown))
        return {"task_id": task_id, "status": "analyzing"}

    async def cancel_as_duplicate(self, task_id: str) -> dict:
        task = await self.task_dao.get_by_id(task_id)
        if not task:
            raise ValueError("任务不存在")
        if task.status != ConversionStatus.DEDUP_CHECK or not task.dedup_pending_info:
            raise ValueError("任务不在等待去重确认状态")
        existing_group_id = task.dedup_pending_info.get("existing_group_id")
        if existing_group_id:
            group = await self.skill_dao.get_group_by_id(existing_group_id)
            if not group:
                await self.task_dao.update(task_id, status=ConversionStatus.FAILED,
                                           error_message=f"关联Skills群{existing_group_id}不存在")
                return {"task_id": task_id, "status": "failed"}
        await self.task_dao.update(task_id, status=ConversionStatus.DUPLICATE,
                                   result_skill_group_id=existing_group_id,
                                   dedup_pending_info=None,
                                   current_stage="duplicate")
        await self.guide_dao.update(task.guide_id, status=ConversionStatus.DUPLICATE)
        return {"task_id": task_id, "status": "duplicate", "existing_group_id": existing_group_id}

    async def get_task_status(self, task_id: str) -> dict | None:
        task = await self.task_dao.get_by_id(task_id)
        if not task:
            return None
        result = {
            "id": task.id, "status": task.status.value if task.status else "unknown",
            "current_stage": task.current_stage, "stage_info": task.stage_info,
            "error_message": task.error_message, "created_at": task.created_at
        }
        if task.status in (ConversionStatus.DEDUP_CHECK, ConversionStatus.DUPLICATE):
            dedup_info = None
            if task.status == ConversionStatus.DUPLICATE and task.result_skill_group_id:
                dedup_info = {"match_type": "exact", "existing_group_id": task.result_skill_group_id}
            elif task.dedup_pending_info:
                dedup_info = {
                    "match_type": task.dedup_pending_info.get("match_type", "similar"),
                    "similar_guide_name": task.dedup_pending_info.get("similar_guide_name"),
                    "similarity": task.dedup_pending_info.get("similarity"),
                    "existing_group_id": task.dedup_pending_info.get("existing_group_id"),
                }
            if dedup_info:
                result["dedup_info"] = dedup_info
        return result

    async def get_task_result(self, task_id: str) -> dict | None:
        task = await self.task_dao.get_by_id(task_id)
        if not task:
            return None
        return {
            "task_id": task.id, "skill_group_id": task.result_skill_group_id,
            "status": task.status.value if task.status else "unknown"
        }

    async def list_tasks(self, user_id: str) -> list[dict]:
        tasks = await self.task_dao.list_by_user(user_id)
        return [{"id": t.id, "status": t.status.value, "current_stage": t.current_stage,
                 "created_at": t.created_at} for t in tasks]

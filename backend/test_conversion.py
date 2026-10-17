"""
独立测试脚本：PDF→MD 解析 和 MD→Skills 生成
用法:
  python test_conversion.py parse <pdf_path>          # 只测试PDF→MD
  python test_conversion.py plan <md_path>             # 只测试MD→Skills规划(LLM)
  python test_conversion.py full <pdf_path>            # 完整流程: PDF→MD→Skills
  python test_conversion.py full <pdf_path> --no-llm   # 完整流程但跳过LLM(只到MD)
  python test_conversion.py list                       # 列出已上传的PDF文件
"""
import sys
import json
import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("test")

BACKEND_DIR = Path(__file__).resolve().parent


def test_parse(pdf_path: str) -> str:
    from app.modules.conversion.parser import PdfParser
    parser = PdfParser()
    path = Path(pdf_path)
    if not path.is_absolute():
        path = BACKEND_DIR / path
    logger.info(f"=== PDF→MD 解析开始 ===")
    logger.info(f"输入: {path} (大小: {path.stat().st_size / 1024:.1f} KB)")
    markdown = parser.parse(path)
    logger.info(f"输出: Markdown 长度={len(markdown)} 字符, 行数={len(markdown.splitlines())}")
    md_path = path.with_suffix(".md")
    md_path.write_text(markdown, encoding="utf-8")
    logger.info(f"已保存: {md_path}")
    print(f"\n--- Markdown 前500字 ---\n{markdown[:500]}\n--- END ---")
    return markdown


async def test_plan(markdown: str, output_dir: str | None = None) -> list[dict]:
    from app.modules.conversion.planner import LlmPlanner, _split_by_headings
    from app.modules.conversion.generator import SkillGenerator
    from app.core.config import get_settings

    settings = get_settings()
    logger.info(f"=== MD→Skills 规划开始 ===")
    logger.info(f"模型: {settings.LLM_DEFAULT_MODEL_ID}")
    logger.info(f"Base URL: {settings.LLM_DEFAULT_BASE_URL}")

    chunks = _split_by_headings(markdown)
    logger.info(f"文档分为 {len(chunks)} 段, 各段长度: {[len(c) for c in chunks]}")

    planner = LlmPlanner()
    plan = await planner.analyze_structure(markdown)
    skills_plan = planner.plan_skills(plan)
    logger.info(f"LLM规划结果: {len(skills_plan)} 个Skills")

    if plan.get("error"):
        logger.error(f"规划错误: {plan['error']}")

    for i, skill in enumerate(skills_plan):
        logger.info(f"  Skill[{i}]: name={skill.get('name')}, tags={skill.get('tags', [])}")

    if output_dir and skills_plan:
        generator = SkillGenerator()
        out = Path(output_dir)
        if not out.is_absolute():
            out = BACKEND_DIR / out
        skill_dirs = generator.generate_skills(skills_plan, out, "test-guide")
        logger.info(f"Skills文件已生成到: {out}")

        from app.modules.conversion.enricher import enrich_all_skills
        enriched = await enrich_all_skills(skill_dirs, markdown)
        logger.info(f"Skills完善完成: {enriched}/{len(skill_dirs)}")

        for sd in skill_dirs:
            logger.info(f"  {sd}/")
            for f in sd.rglob("*"):
                if f.is_file():
                    logger.info(f"    {f.name} ({f.stat().st_size} bytes)")

    return skills_plan


async def test_full(pdf_path: str, skip_llm: bool = False):
    markdown = test_parse(pdf_path)
    if skip_llm:
        logger.info("跳过LLM分析 (--no-llm)")
        return
    guide_name = Path(pdf_path).stem
    output_dir = str(BACKEND_DIR / "data" / "skills" / guide_name)
    await test_plan(markdown, output_dir)


def list_pdfs():
    pdf_dir = BACKEND_DIR / "data" / "pdfs"
    md_dir = pdf_dir
    if not pdf_dir.exists():
        print("PDF目录不存在")
        return
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        print("没有PDF文件")
        return
    print(f"{'PDF文件':<60} {'大小(KB)':>10} {'MD已生成':>8}")
    print("-" * 80)
    for p in pdfs:
        size = p.stat().st_size / 1024
        md_exists = "是" if (md_dir / f"{p.stem}.md").exists() else "否"
        print(f"{str(p):<60} {size:>10.1f} {md_exists:>8}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        list_pdfs()
    elif command == "parse":
        if len(sys.argv) < 3:
            print("用法: python test_conversion.py parse <pdf_path>")
            sys.exit(1)
        test_parse(sys.argv[2])
    elif command == "plan":
        if len(sys.argv) < 3:
            print("用法: python test_conversion.py plan <md_path>")
            sys.exit(1)
        md = Path(sys.argv[2]).read_text(encoding="utf-8")
        asyncio.run(test_plan(md))
    elif command == "full":
        if len(sys.argv) < 3:
            print("用法: python test_conversion.py full <pdf_path> [--no-llm]")
            sys.exit(1)
        skip_llm = "--no-llm" in sys.argv
        asyncio.run(test_full(sys.argv[2], skip_llm))
    else:
        print(f"未知命令: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()

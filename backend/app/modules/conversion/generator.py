import re
import yaml
from pathlib import Path
from app.core.config import get_settings


def _normalize_ref_name(name: str) -> str:
    clean = re.sub(r'[^a-z0-9\u4e00-\u9fff_-]', '-', name.lower())
    clean = re.sub(r'-{2,}', '-', clean)
    return clean.strip('-') or "ref"


class SkillGenerator:
    def __init__(self):
        self.settings = get_settings()

    def generate_skills(self, plan_skills: list[dict], output_dir: Path, guide_name: str) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        skill_dirs = []
        for spec in plan_skills:
            name = spec.get("name", "unnamed-skill")
            if not self.validate_name_format(name):
                name = re.sub(r'[^a-z0-9-]', '-', name.lower()).strip('-')
                if not name:
                    name = "skill"
            skill_dir = output_dir / name
            skill_dir.mkdir(parents=True, exist_ok=True)

            ref_map = self._write_references(skill_dir, spec.get("references", []))
            self._write_skill_md(skill_dir, spec, ref_map)
            self._write_scripts(skill_dir, spec.get("scripts", []))

            skill_dirs.append(skill_dir)
        return skill_dirs

    def _write_skill_md(self, skill_dir: Path, spec: dict, ref_map: dict[str, str]):
        frontmatter = {
            "name": spec.get("name", skill_dir.name),
            "description": spec.get("description", ""),
        }
        if spec.get("tags"):
            frontmatter["tags"] = spec["tags"]

        instructions = spec.get("instructions", "")
        if len(instructions) < 50:
            instructions = instructions + "\n\n请参考references中的文档获取更多信息。"

        content = f"---\n{yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)}---\n\n"
        content += f"# {spec.get('name', skill_dir.name)}\n\n"
        content += f"## 核心指令\n\n{instructions}\n"

        if ref_map:
            content += "\n## 参考资源\n\n"
            for filename, summary in ref_map.items():
                content += f"- [{filename}](references/{filename})"
                if summary:
                    content += f": {summary}"
                content += "\n"

        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")

    def _write_references(self, skill_dir: Path, references: list) -> dict[str, str]:
        if not references:
            return {}
        refs_dir = skill_dir / "references"
        refs_dir.mkdir(exist_ok=True)

        ref_map = {}
        used_names = set()

        for i, ref in enumerate(references):
            if isinstance(ref, dict):
                name = _normalize_ref_name(ref.get("name", f"ref-{i + 1}"))
                content = ref.get("content", "")
                summary = ref.get("description", "")
            elif isinstance(ref, str):
                name = f"ref-{i + 1}"
                content = ref
                summary = ""
            else:
                continue

            base_name = name
            counter = 1
            while name in used_names:
                name = f"{base_name}-{counter}"
                counter += 1
            used_names.add(name)

            filename = f"{name}.md"
            (refs_dir / filename).write_text(content, encoding="utf-8")
            ref_map[filename] = summary

        return ref_map

    def _write_scripts(self, skill_dir: Path, scripts: list):
        if not scripts:
            return
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        for i, script in enumerate(scripts):
            (scripts_dir / f"script_{i + 1}.sh").write_text(script, encoding="utf-8")

    @staticmethod
    def validate_name_format(name: str) -> bool:
        return bool(re.match(r'^[a-z][a-z0-9-]*$', name))

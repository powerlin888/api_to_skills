import re
import yaml
from pathlib import Path


class SkillValidator:
    def validate_structure(self, skill_dir: Path) -> list[str]:
        errors = []
        if not skill_dir.is_dir():
            errors.append(f"不是有效目录: {skill_dir}")
            return errors
        if not (skill_dir / "SKILL.md").exists():
            errors.append(f"缺少SKILL.md: {skill_dir}")
        return errors

    def validate_skill_md(self, skill_dir: Path) -> list[str]:
        errors = []
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            return [f"SKILL.md不存在: {skill_dir}"]
        content = skill_md.read_text(encoding="utf-8")
        if not content.startswith("---"):
            errors.append("缺少YAML frontmatter")
            return errors
        end = content.find("---", 3)
        if end == -1:
            errors.append("YAML frontmatter未闭合")
            return errors
        try:
            fm = yaml.safe_load(content[3:end])
            if not fm.get("name"):
                errors.append("缺少name字段")
            if not fm.get("description"):
                errors.append("缺少description字段")
        except yaml.YAMLError as e:
            errors.append(f"YAML解析错误: {e}")
        instructions = content[end + 3:].strip()
        if len(instructions) < 50:
            errors.append(f"instructions过短({len(instructions)}字符)，需要至少50字符")
        return errors

    def validate_name_format(self, name: str) -> bool:
        return bool(re.match(r'^[a-z][a-z0-9-]*$', name))

    def validate_all(self, skill_dir: Path) -> list[str]:
        errors = self.validate_structure(skill_dir)
        errors.extend(self.validate_skill_md(skill_dir))
        name = skill_dir.name
        if not self.validate_name_format(name):
            errors.append(f"目录名格式无效: {name}，需要^[a-z][a-z0-9-]*$")
        return errors

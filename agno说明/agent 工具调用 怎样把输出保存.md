agent 工具调用 怎样把输出保存为.txt

GLM 4.7

用户在问 "agent 工具调用 怎样把输出保存为.txt"，意思是 "如何在 agent 工具调用中将输出保存为 .txt 文件"。
我需要查看一下代码库结构，了解工具调用和文件保存的相关实现。

结构获取完成
libs/agno
结构获取完成
cookbook/03_agents
结构获取完成
cookbook/17_custom_tool_development

看起来 cookbook/03_agents 和 cookbook/17_custom_tool_development 的路径不存在。让我重新查看 cookbook 的结构。
结构获取完成
cookbook
结构获取完成
libs/agno/agno/tools

很好，我看到了：
已查看文件大纲
libs/agno/agno/tools/file.py
已查看文件大纲
libs/agno/agno/tools/file_generation.py
结构获取完成
cookbook/91_tools

完美！我找到了答案。从代码来看，有两种主要方法将 agent 工具调用输出保存为 .txt 文件：
文件查看完成
cookbook/91_tools/file_tools.py
文件查看完成
cookbook/91_tools/file_generation_tools.py

太好了！我现在有足够的信息来回答用户的问题。有两种主要方法：
文件查看完成
libs/agno/agno/tools/file_generation.py

完美！现在我有足够的信息来给用户一个完整的答案了。我可以解释两种方法并提供代码示例。
将 Agent 工具调用输出保存为 .txt 文件有两种方法：

方法一：使用 FileTools（基础文件操作）
最直接的方式，让 Agent 使用 save_file 方法将内容写入文件：

from pathlib import Path
from agno.agent import Agent
from agno.tools.file import FileTools
 
# 创建 Agent，指定保存目录
agent = Agent(
    tools=[FileTools(Path("tmp/file"))],
    description="文件操作助手",
    instructions=["使用 save_file 方法保存内容到 .txt 文件"],
)
 
# 直接让 Agent 保存内容
agent.print_response(
    "总结 Python 最佳实践，并保存到 python_guide.txt",
    markdown=True,
)
或者只启用保存功能（更安全）：

agent = Agent(
    tools=[
        FileTools(
            Path("tmp/file"),
            enable_save_file=True,
            enable_read_file=False,  # 禁用读取
            enable_delete_file=False,  # 禁用删除
        )
    ],
    description="只能写文件的助手",
)
方法二：使用 FileGenerationTools（专业文件生成）
更强大的工具，支持自动生成文件名和返回文件对象：

from agno.agent import Agent
from agno.tools.file_generation import FileGenerationTools
 
agent = Agent(
    tools=[FileGenerationTools(output_directory="tmp")],
    description="文件生成助手",
    instructions=["使用 generate_text_file 方法生成 .txt 文件"],
)
 
# Agent 会自动选择工具并生成文件
response = agent.run(
    "创建一个包含远程工作最佳实践的文本文件"
)
 
# 获取生成的文件信息
if response.files:
    for file in response.files:
        print(f"生成的文件: {file.filename}")
        print(f"文件大小: {file.size} 字节")
        print(f"文件路径: {file.url}")
关键区别
特性	FileTools	FileGenerationTools
文件名控制	手动指定文件名	可自动生成 UUID 文件名
返回值	返回成功/失败消息	返回 FileArtifact 对象
适用场景	基础文件读写	批量生成、需要文件元数据
灵活性	高（可精细控制权限）	中（专注生成）
实用建议
如果只是简单保存输出，用 FileTools；如果需要批量生成文件或获取文件元数据，用 FileGenerationTools。两个工具都能让 Agent 自然地将对话内容或任务结果保存为 .txt 文件。

file_tools.py
file_generation_tools.py
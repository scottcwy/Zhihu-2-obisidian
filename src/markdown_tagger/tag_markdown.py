import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from openai import OpenAI
import json
from config import Config

# 加载环境变量
load_dotenv()

class MarkdownTagger:
    def __init__(self, config_path=None):
        """初始化 Markdown 标签处理器

        Args:
            config_path (str, optional): 配置文件路径. Defaults to None.
        """
        # 加载配置
        self.config = Config(config_path)
        self.config.validate()
        
        # 获取API配置
        self.api_key = os.getenv("AIFAB_API_KEY")
        self.api_base = os.getenv("AIFAB_API_BASE")
        
        if not self.api_key or not self.api_base:
            raise ValueError("请确保设置了 AIFAB_API_KEY 和 AIFAB_API_BASE 环境变量")
            
        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )
        
        # 获取AI配置
        self.ai_config = self.config.get_ai_config()
        self.system_prompt = self.config.get_system_prompt()

    def read_markdown_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"读取文件 {file_path} 时出错: {str(e)}")
            return None

    def generate_metadata(self, content):
        try:
            print(f"正在连接API: {self.api_base}")
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"请分析以下文章内容：\n\n{content}"}
            ]
            
            try:
                response = self.client.chat.completions.create(
                    model=self.ai_config['model'],
                    messages=messages,
                    temperature=self.ai_config['temperature']
                )
                
                if not response.choices:
                    return self._generate_error_metadata(content, "API 返回结果为空")
                    
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                print(f"API调用错误: {str(e)}")
                return self._generate_error_metadata(content, f"API调用错误: {str(e)}")
            
        except Exception as e:
            print(f"其他错误: {str(e)}")
            return self._generate_error_metadata(content, str(e))

    def _generate_error_metadata(self, content, error_message):
        """生成错误情况下的元数据"""
        return f"""# 处理出错的文档
**日期**: {datetime.now().strftime('%Y-%m-%d')}
**分类**: [ ] 待分类
**主标签**: #待处理
**相关度**: low
**总结**: 文档处理失败 - {error_message[:100]}
**原始内容长度**: {len(content)} 字符
**错误详情**: {error_message}
"""

    def update_markdown_with_metadata(self, content, metadata):
        return f"{metadata}\n\n{content}"

    def process_files(self):
        # 获取目录配置
        input_dir = self.config.get_input_dir()
        output_dir = self.config.get_output_dir()
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取所有 markdown 文件
        markdown_files = list(Path(input_dir).glob('*.md'))
        
        if not markdown_files:
            print(f"在 {input_dir} 目录中没有找到 Markdown 文件")
            return
        
        for input_file in markdown_files:
            print(f"\n开始处理文件: {input_file.name}")
            
            # 读取内容
            content = self.read_markdown_file(input_file)
            if content is None:
                continue
            
            # 生成元数据
            print("正在分析文档...")
            metadata = self.generate_metadata(content)
            
            # 更新内容
            new_content = self.update_markdown_with_metadata(content, metadata)
            
            # 创建输出文件路径
            output_file = Path(output_dir) / input_file.name
            
            # 删除已经存在的输出文件
            if os.path.exists(output_file):
                os.remove(output_file)
            
            # 保存处理后的文件
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✓ 已添加元数据")
                print(f"✓ 已保存到: {output_file}")
            except Exception as e:
                print(f"保存文件 {output_file} 时出错: {str(e)}")

        print("\n处理完成！")


def main():
    print("=== AI创业文档分析器 ===")
    
    try:
        tagger = MarkdownTagger()
        print(f"输入目录: {tagger.config.get_input_dir()}")
        print(f"输出目录: {tagger.config.get_output_dir()}")
        print("开始处理...\n")
        
        tagger.process_files()
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")

    print("\n处理完成！")

if __name__ == "__main__":
    main()
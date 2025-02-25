import os
import yaml
from pathlib import Path

class Config:
    def __init__(self, config_path=None):
        """初始化配置管理器

        Args:
            config_path (str, optional): 配置文件路径. Defaults to None.
        """
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), 'config.yaml')
        self.config = self._load_config()

    def _load_config(self):
        """加载配置文件

        Returns:
            dict: 配置信息
        """
        if not os.path.exists(self.config_path):
            example_path = os.path.join(os.path.dirname(__file__), 'config.example.yaml')
            if os.path.exists(example_path):
                print(f"配置文件 {self.config_path} 不存在，将从示例配置创建...")
                with open(example_path, 'r', encoding='utf-8') as f:
                    config_content = f.read()
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    f.write(config_content)
            else:
                raise FileNotFoundError(f"配置文件 {self.config_path} 和示例配置文件都不存在！")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_input_dir(self):
        """获取输入目录的绝对路径"""
        input_dir = self.config['directories']['input']
        if not os.path.isabs(input_dir):
            input_dir = os.path.join(os.path.dirname(__file__), input_dir)
        return input_dir

    def get_output_dir(self):
        """获取输出目录的绝对路径"""
        output_dir = self.config['directories']['output']
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(os.path.dirname(__file__), output_dir)
        return output_dir

    def get_ai_config(self):
        """获取AI相关配置"""
        return self.config['ai']

    def get_system_prompt(self):
        """获取系统提示词"""
        return self.config['metadata']['system_prompt']

    def validate(self):
        """验证配置的有效性"""
        required_keys = {
            'ai': ['model', 'temperature'],
            'directories': ['input', 'output'],
            'metadata': ['system_prompt']
        }

        for section, keys in required_keys.items():
            if section not in self.config:
                raise ValueError(f"配置文件缺少 {section} 部分")
            for key in keys:
                if key not in self.config[section]:
                    raise ValueError(f"配置文件在 {section} 部分缺少 {key} 配置项")

        # 验证目录是否存在或可创建
        input_dir = self.get_input_dir()
        if not os.path.exists(input_dir):
            raise ValueError(f"输入目录 {input_dir} 不存在")

        output_dir = self.get_output_dir()
        output_parent = os.path.dirname(output_dir)
        if not os.path.exists(output_parent):
            raise ValueError(f"输出目录的父目录 {output_parent} 不存在")

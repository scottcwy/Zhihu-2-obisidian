# 知乎收藏转个人知识库方案

**项目概述**：
一个将知乎收藏内容导出并智能整理的工具，帮助构建个人知识库。支持导出知乎收藏夹内容为Markdown格式，并使用AI自动生成标签、摘要等元数据，特别适合需要整理知乎优质内容到Notion或Obsidian等知识库的用户。

## 主要功能

### 1. 知乎导出
- ✅ 支持公开和私密收藏夹
- ✅ 转换为Markdown格式
- ✅ 适配Obsidian
- ✅ 保留原文引用
- ✅ 支持断点续传

### 2. AI智能标签
- 🤖 自动生成标签和摘要
- 📊 智能分类和评估
- 🎯 主题识别
- ⚙️ 自定义分析规则
- 📝 生成YAML元数据

## 使用方法

### 1. 环境准备
```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量(.env)
AIFAB_API_KEY=your_api_key_here    # OpenAI API密钥
AIFAB_API_BASE=your_api_base_here  # API基础URL
ZHIHU_COOKIE=your_cookie_here      # 知乎Cookie(可选)
```

### 2. 导出收藏
```bash
python src/zhihu_exporter/main.py --collection_url <收藏夹URL>
```

### 3. 生成标签
```bash
python src/markdown_tagger/tag_markdown.py
```

## 效果展示

### 1. 知识图谱
![知识关系图谱](docs/images/graph.png)

### 2. 标签示例
```yaml
---
tags: 
  - 经济分析
  - 市场竞争
  - 商业模式
summary: 本文分析了电商平台竞争格局的演变...
topic: 商业竞争分析
difficulty: 中级
type: 案例分析
created: 2024-02-25
---
```

### 3. 文章示例
![文章示例](docs/images/article.png)

## 项目结构
```
src/
├── zhihu_exporter/     # 知乎导出模块
│   ├── main.py        # 导出主程序
│   └── utils.py       # 工具函数
└── markdown_tagger/    # 标签处理模块
    ├── tag_markdown.py # 标签处理主程序
    ├── config.py      # 配置处理
    └── config.yaml    # 标签系统配置
```

## 注意事项
- 遵守知乎用户协议，仅供个人学习使用
- OpenAI API调用会产生费用，请注意使用量
- 支持所有OpenAI API兼容的服务商(如硅基流动等)

## License
MIT License © 2025 [Weiyu Cheng]

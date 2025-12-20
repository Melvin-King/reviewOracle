"""
数据下载脚本
从 NIPS 2024 下载论文和 review
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.downloader import NIPSDownloader
import yaml


def main():
    parser = argparse.ArgumentParser(description="下载 NIPS 论文和 review")
    parser.add_argument("--num-papers", type=int, default=3, help="下载论文数量")
    parser.add_argument("--year", type=int, default=2024, help="会议年份")
    parser.add_argument("--config", type=str, default="config.yaml", help="配置文件路径")
    
    args = parser.parse_args()
    
    # 加载配置
    with open(args.config, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 初始化下载器
    downloader = NIPSDownloader(
        base_url=config['data_source'].get('openreview_base_url', 'https://api.openreview.net'),
        download_path=config['data_source'].get('download_path', 'data/raw')
    )
    
    # 下载论文
    print(f"开始下载 {args.year} 年 NIPS 的 {args.num_papers} 篇论文...")
    paper_ids = downloader.download_nips_papers(year=args.year, num_papers=args.num_papers)
    
    print(f"\n下载完成！论文 ID 列表：")
    for pid in paper_ids:
        print(f"  - {pid}")


if __name__ == "__main__":
    main()


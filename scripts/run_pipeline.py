"""
运行完整 E-V-W 流程的脚本
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import EVWPipeline


def main():
    parser = argparse.ArgumentParser(description="运行 E-V-W 评估流程")
    parser.add_argument("--paper-id", type=str, required=True, help="论文 ID")
    parser.add_argument("--config", type=str, default="config.yaml", help="配置文件路径")
    parser.add_argument("--step", type=int, choices=[1, 2, 3, 4], 
                       help="只运行指定步骤（可选）")
    
    args = parser.parse_args()
    
    # 初始化流程
    pipeline = EVWPipeline(config_path=args.config)
    
    if args.step:
        # 只运行指定步骤
        if args.step == 1:
            pipeline.step1_extraction(args.paper_id)
        elif args.step == 2:
            pipeline.step2_verification(args.paper_id)
        elif args.step == 3:
            pipeline.step3_weighting(args.paper_id)
        elif args.step == 4:
            pipeline.step4_synthesis(args.paper_id)
    else:
        # 运行完整流程
        pipeline.run_pipeline(args.paper_id)


if __name__ == "__main__":
    main()


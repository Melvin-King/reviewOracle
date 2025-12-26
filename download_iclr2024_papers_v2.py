"""
下载 ICLR 2024 的论文（包括 Accepted 和 Rejected）
使用更灵活的查询方式
"""

import sys
import io
import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Optional

# 设置UTF-8编码输出
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

base_url = "https://api2.openreview.net"
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})


def get_paper_by_forum_id(forum_id: str) -> Optional[Dict]:
    """通过forum ID获取论文信息"""
    url = f"{base_url}/notes"
    params = {
        "id": forum_id,
        "details": "writable,signatures,invitation,presentation,tags"
    }
    
    try:
        time.sleep(2)
        response = session.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        notes = data.get('notes', [])
        
        if notes:
            note = notes[0]
            content = note.get('content', {})
            venue = content.get('venue', '')
            venueid = content.get('venueid', '')
            title = content.get('title', {})
            if isinstance(title, dict):
                title = title.get('value', 'Unknown Title')
            else:
                title = str(title)
            
            # 判断状态
            status = "UNKNOWN"
            if 'Rejected' in str(venueid) or 'Rejected' in str(venue):
                status = "REJECTED"
            elif 'Accepted' in str(venueid) or 'Accepted' in str(venue):
                status = "ACCEPTED"
            elif 'Withdrawn' in str(venueid) or 'Withdrawn' in str(venue):
                status = "WITHDRAWN"
            elif 'ICLR' in str(venue) and '2024' in str(venue):
                # 如果venue包含ICLR和2024，可能是accepted
                status = "ACCEPTED"
            
            return {
                'id': forum_id,
                'forum_id': forum_id,
                'title': title,
                'venue': venue,
                'venueid': venueid,
                'status': status,
                'pdf_url': f"https://openreview.net/pdf?id={forum_id}"
            }
    except Exception as e:
        print(f"  [ERROR] 获取论文信息失败: {e}")
    
    return None


def search_iclr_papers_by_venueid(year: int = 2024, status: str = "rejected", limit: int = 10) -> List[Dict]:
    """
    通过venueid搜索论文
    """
    print("=" * 70)
    print(f"搜索 ICLR {year} {status.upper()} 论文")
    print("=" * 70)
    print()
    
    papers = []
    
    # 尝试不同的venueid格式
    venueid_patterns = [
        f"ICLR.cc/{year}/Conference/Rejected",
        f"ICLR.cc/{year}/Conference/Reject",
        f"ICLR.cc/{year}/Conference/Paper.*/Rejected",
    ] if status == "rejected" else [
        f"ICLR.cc/{year}/Conference",
        f"ICLR.cc/{year}/Conference/Paper.*",
    ]
    
    # 由于API限制，我们使用已知的forum ID列表
    # 从网页上可以看到一些rejected论文的forum ID
    known_rejected_ids = [
        "cXs5md5wAq",  # Modelling Microbial Communities with Graph Neural Networks
        "kKRbAY4CXv",  # Neural Evolutionary Kernel Method
        "ApjY32f3Xr",  # PINNacle
        "H9DYMIpz9c",  # Farzi Data
        "rp5vfyp5Np",  # BATTLE
        "miGpIhquyB",  # Understanding Large Language Models Through the Lens of Dataset Generation
        "9ceadCJY4B",  # Ask Again, Then Fail: Large Language Models' Vacillations in Judgement
        "gYcft1HIaU",  # Do Current Large Language Models Master Adequate Clinical Knowledge?
    ]
    
    known_accepted_ids = [
        "rhgIgTSSxW",  # TabR: Tabular Deep Learning Meets Nearest Neighbors
        "qBL04XXex6",  # Boosting of Thoughts: Trial-and-Error Problem Solving with Large Language Models
        "i8PjQT3Uig",  # Locality Sensitive Sparse Encoding for Learning World Models Online
        "eepoE7iLpL",  # Enhancing Neural Subset Selection: Integrating Background Information into Set Representations
        "lK2V2E2MNv",  # Bridging Vision and Language Spaces with Assignment Prediction
    ]
    
    forum_ids = known_rejected_ids if status == "rejected" else known_accepted_ids
    
    if not forum_ids:
        print(f"[WARNING] 未提供已知的{status}论文forum ID")
        print(f"[INFO] 请从OpenReview网页获取forum ID并添加到脚本中")
        return []
    
    print(f"[INFO] 检查 {len(forum_ids)} 个已知的forum ID...\n")
    
    for i, forum_id in enumerate(forum_ids[:limit], 1):
        print(f"[{i}/{min(len(forum_ids), limit)}] 检查 Forum ID: {forum_id}")
        paper_info = get_paper_by_forum_id(forum_id)
        
        if paper_info:
            # 验证状态
            if status == "rejected" and paper_info['status'] == "REJECTED":
                papers.append(paper_info)
                print(f"  ✓ [REJECTED] {paper_info['title'][:60]}...")
            elif status == "accepted" and paper_info['status'] == "ACCEPTED":
                papers.append(paper_info)
                print(f"  ✓ [ACCEPTED] {paper_info['title'][:60]}...")
            else:
                print(f"  - [状态不匹配] {paper_info['status']}")
        else:
            print(f"  - [未找到]")
        
        time.sleep(1)  # 避免请求过快
    
    print(f"\n[INFO] 找到 {len(papers)} 篇{status}论文")
    return papers


def download_paper_pdf(paper_info: Dict, save_dir: Path) -> Optional[str]:
    """下载论文PDF"""
    forum_id = paper_info['forum_id']
    pdf_url = paper_info['pdf_url']
    
    pdf_path = save_dir / f"{forum_id}.pdf"
    
    if pdf_path.exists():
        print(f"  [SKIP] PDF 已存在: {pdf_path.name}")
        return str(pdf_path)
    
    try:
        print(f"  [DOWNLOAD] 下载 PDF...")
        time.sleep(2)
        response = session.get(pdf_url, timeout=60, stream=True)
        response.raise_for_status()
        
        with open(pdf_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"  [SUCCESS] PDF 已保存: {pdf_path.name}")
        return str(pdf_path)
    except Exception as e:
        print(f"  [ERROR] PDF 下载失败: {e}")
        return None


def download_reviews(paper_info: Dict, save_dir: Path, year: int = 2024) -> Optional[List[Dict]]:
    """下载论文的reviews"""
    forum_id = paper_info['forum_id']
    
    reviews_path = save_dir / f"{forum_id}_reviews.json"
    
    if reviews_path.exists():
        print(f"  [SKIP] Reviews 已存在: {reviews_path.name}")
        try:
            with open(reviews_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    try:
        print(f"  [DOWNLOAD] 下载 Reviews...")
        time.sleep(3)
        
        url = f"{base_url}/notes"
        params = {
            "domain": f"ICLR.cc/{year}/Conference",
            "forum": forum_id,
            "details": "writable,signatures,invitation,presentation,tags",
            "trash": "true",
            "limit": 1000
        }
        
        response = session.get(url, params=params, timeout=30)
        
        if response.status_code == 429:
            print(f"  [WARNING] 遇到 429 错误，等待 15 秒...")
            time.sleep(15)
            response = session.get(url, params=params, timeout=30)
        
        response.raise_for_status()
        data = response.json()
        all_notes = data.get('notes', [])
        
        # 过滤出 Official Reviews
        reviews = []
        for note in all_notes:
            invitations = note.get('invitations', [])
            if isinstance(invitations, str):
                invitations = [invitations]
            elif not isinstance(invitations, list):
                invitations = []
            
            is_official_review = False
            for inv in invitations:
                if inv.endswith('/-/Official_Review'):
                    is_official_review = True
                    break
            
            if is_official_review:
                reviews.append(note)
        
        if reviews:
            with open(reviews_path, 'w', encoding='utf-8') as f:
                json.dump(reviews, f, ensure_ascii=False, indent=2)
            print(f"  [SUCCESS] 找到 {len(reviews)} 个 Reviews，已保存")
            return reviews
        else:
            print(f"  [WARNING] 未找到 Reviews")
            return []
            
    except Exception as e:
        print(f"  [ERROR] Reviews 下载失败: {e}")
        return None


def main():
    """主函数"""
    # 配置
    year = 2024
    num_accepted = 5  # 下载5篇accepted论文
    num_rejected = 5  # 下载5篇rejected论文
    
    # 创建保存目录
    base_dir = Path("data/raw/iclr2024")
    accepted_papers_dir = base_dir / "papers" / "accepted"
    rejected_papers_dir = base_dir / "papers" / "rejected"
    reviews_dir = base_dir / "reviews"
    
    accepted_papers_dir.mkdir(parents=True, exist_ok=True)
    rejected_papers_dir.mkdir(parents=True, exist_ok=True)
    reviews_dir.mkdir(parents=True, exist_ok=True)
    
    # 初始化
    accepted_papers = []
    rejected_papers = []
    
    # 1. 搜索并下载 Rejected 论文
    print("\n" + "=" * 70)
    print("搜索 Rejected 论文")
    print("=" * 70)
    rejected_papers = search_iclr_papers_by_venueid(year=year, status="rejected", limit=num_rejected)
    
    if rejected_papers:
        print(f"\n开始下载 {len(rejected_papers)} 篇 Rejected 论文...\n")
        for i, paper_info in enumerate(rejected_papers, 1):
            print(f"\n[{i}/{len(rejected_papers)}] {paper_info['title'][:60]}...")
            print(f"  Forum ID: {paper_info['forum_id']}")
            print(f"  Status: {paper_info['status']}")
            
            # 下载PDF
            pdf_path = download_paper_pdf(paper_info, rejected_papers_dir)
            
            # 下载Reviews
            reviews = download_reviews(paper_info, reviews_dir, year=year)
            
            # 保存论文信息
            info_path = rejected_papers_dir / f"{paper_info['forum_id']}_info.json"
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(paper_info, f, ensure_ascii=False, indent=2)
            
            if i < len(rejected_papers):
                wait_time = 5
                print(f"\n[INFO] 等待 {wait_time} 秒以避免API限制...")
                time.sleep(wait_time)
    else:
        print("\n[WARNING] 未找到 Rejected 论文")
        print("[INFO] 请从OpenReview网页获取rejected论文的forum ID并添加到脚本中")
    
    # 2. 搜索并下载 Accepted 论文
    print("\n" + "=" * 70)
    print("搜索 Accepted 论文")
    print("=" * 70)
    accepted_papers = search_iclr_papers_by_venueid(year=year, status="accepted", limit=num_accepted)
    
    if accepted_papers:
        print(f"\n开始下载 {len(accepted_papers)} 篇 Accepted 论文...\n")
        for i, paper_info in enumerate(accepted_papers, 1):
            print(f"\n[{i}/{len(accepted_papers)}] {paper_info['title'][:60]}...")
            print(f"  Forum ID: {paper_info['forum_id']}")
            print(f"  Status: {paper_info['status']}")
            
            # 下载PDF
            pdf_path = download_paper_pdf(paper_info, accepted_papers_dir)
            
            # 下载Reviews
            reviews = download_reviews(paper_info, reviews_dir, year=year)
            
            # 保存论文信息
            info_path = accepted_papers_dir / f"{paper_info['forum_id']}_info.json"
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(paper_info, f, ensure_ascii=False, indent=2)
            
            if i < len(accepted_papers):
                wait_time = 5
                print(f"\n[INFO] 等待 {wait_time} 秒以避免API限制...")
                time.sleep(wait_time)
    else:
        print("\n[WARNING] 未找到 Accepted 论文")
    
    # 总结
    print(f"\n{'=' * 70}")
    print(f"下载完成！")
    print(f"  - Accepted 论文: {len(accepted_papers)} 篇 -> {accepted_papers_dir}")
    print(f"  - Rejected 论文: {len(rejected_papers)} 篇 -> {rejected_papers_dir}")
    print(f"  - Reviews: {reviews_dir}")
    print(f"\n提示：要下载更多论文，请从OpenReview网页获取forum ID并添加到脚本中")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()


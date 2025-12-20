"""
下载被拒绝的论文 - 手动提供 Forum ID 版本
由于 OpenReview API 限制，建议从网页手动获取 rejected 论文的 forum ID
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


def check_paper_status(forum_id: str) -> Dict:
    """检查论文状态"""
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
            
            return {
                'forum_id': forum_id,
                'title': title,
                'venue': venue,
                'venueid': venueid,
                'status': status,
                'pdf_url': f"https://openreview.net/pdf?id={forum_id}"
            }
    except Exception as e:
        print(f"  [ERROR] 检查状态失败: {e}")
    
    return None


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


def download_reviews(paper_info: Dict, save_dir: Path) -> Optional[List[Dict]]:
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
            "domain": "NeurIPS.cc/2024/Conference",
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
    print("=" * 70)
    print("下载被拒绝的论文 - 手动提供 Forum ID")
    print("=" * 70)
    print()
    print("说明：")
    print("1. 从 OpenReview 网页上找到被拒绝的论文")
    print("2. 从 URL 中获取 forum ID（例如：https://openreview.net/forum?id=XXXXX）")
    print("3. 将 forum ID 添加到下面的列表中")
    print()
    
    # ============================================
    # 在这里添加被拒绝论文的 Forum ID
    # ============================================
    # 示例：从 OpenReview 网页获取 forum ID
    # 访问 https://openreview.net/group?id=NeurIPS.cc/2024/Conference
    # 筛选出 Rejected 论文，从 URL 中提取 forum ID
    rejected_forum_ids = [
        # 示例（请替换为实际的 forum ID）:
        # "example_forum_id_1",
        # "example_forum_id_2",
        # "example_forum_id_3",
    ]
    
    if not rejected_forum_ids:
        print("[INFO] 请在脚本中填写 rejected_forum_ids 列表")
        print("[INFO] 获取方法：")
        print("  1. 访问 https://openreview.net/group?id=NeurIPS.cc/2024/Conference")
        print("  2. 使用筛选功能找到 Rejected 论文")
        print("  3. 点击论文，从 URL 中提取 forum ID（?id=后面的部分）")
        print("  4. 将 forum ID 添加到 rejected_forum_ids 列表中")
        return
    
    # 创建保存目录
    base_dir = Path("data/raw")
    papers_dir = base_dir / "papers"
    reviews_dir = base_dir / "reviews"
    papers_dir.mkdir(parents=True, exist_ok=True)
    reviews_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[INFO] 准备下载 {len(rejected_forum_ids)} 篇论文")
    print()
    
    # 检查每篇论文的状态并下载
    downloaded_papers = []
    
    for i, forum_id in enumerate(rejected_forum_ids, 1):
        print(f"\n{'=' * 70}")
        print(f"[{i}/{len(rejected_forum_ids)}] Forum ID: {forum_id}")
        print(f"{'=' * 70}")
        
        # 检查论文状态
        paper_info = check_paper_status(forum_id)
        
        if not paper_info:
            print(f"  [ERROR] 无法获取论文信息")
            continue
        
        print(f"  标题: {paper_info['title'][:60]}...")
        print(f"  状态: {paper_info['status']}")
        print(f"  Venue: {paper_info['venue']}")
        
        if paper_info['status'] != 'REJECTED':
            print(f"  [WARNING] 论文状态不是 REJECTED，跳过")
            continue
        
        # 下载PDF
        pdf_path = download_paper_pdf(paper_info, papers_dir)
        
        # 下载Reviews
        reviews = download_reviews(paper_info, reviews_dir)
        
        # 保存论文信息
        info_path = papers_dir / f"{forum_id}_info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(paper_info, f, ensure_ascii=False, indent=2)
        
        downloaded_papers.append(paper_info)
        
        # 在论文之间添加延迟
        if i < len(rejected_forum_ids):
            wait_time = 5
            print(f"\n[INFO] 等待 {wait_time} 秒以避免API限制...")
            time.sleep(wait_time)
    
    print(f"\n{'=' * 70}")
    print(f"下载完成！")
    print(f"  成功下载: {len(downloaded_papers)} 篇论文")
    print(f"  - 论文PDF: {papers_dir}")
    print(f"  - Reviews: {reviews_dir}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()


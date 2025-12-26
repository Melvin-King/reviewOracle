"""
下载 ICLR 2024 的论文（包括 Accepted 和 Rejected）
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


def search_iclr_papers(year: int = 2024, status: str = "all", limit: int = 10, max_pages: int = 5) -> List[Dict]:
    """
    搜索 ICLR 论文
    
    Args:
        year: 会议年份
        status: "accepted", "rejected", "all"
        limit: 每页返回数量
        max_pages: 最多搜索页数
        
    Returns:
        论文列表
    """
    print("=" * 70)
    print(f"搜索 ICLR {year} 论文")
    print(f"状态筛选: {status.upper()}")
    print("=" * 70)
    print()
    
    papers = []
    offset = 0
    
    # ICLR 在 OpenReview 上的 domain
    domain = f"ICLR.cc/{year}/Conference"
    
    # 尝试多种查询方式
    query_methods = [
        {
            "name": "domain_any_venue",
            "params": {
                "domain": domain,
                "content.venue": f"ICLR {year}",
                "limit": limit,
                "offset": 0,
                "details": "writable,signatures,invitation,presentation,tags",
                "trash": "true"
            }
        },
        {
            "name": "domain_only",
            "params": {
                "domain": domain,
                "limit": limit,
                "offset": 0,
                "details": "writable,signatures,invitation,presentation,tags",
                "trash": "true"
            }
        }
    ]
    
    for query_info in query_methods:
        method_name = query_info["name"]
        base_params = query_info["params"]
        
        print(f"\n[INFO] 尝试查询方式: {method_name}")
        
        for page in range(max_pages):
            print(f"\n[INFO] 搜索第 {page + 1} 页 (offset={offset})...")
            
            url = f"{base_url}/notes"
            params = base_params.copy()
            params["offset"] = offset
            params["limit"] = 50  # 增加每页数量
            
            try:
                time.sleep(5)  # 避免请求过快
                response = session.get(url, params=params, timeout=30, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 429:
                    print(f"[WARNING] 遇到 429 错误，等待 15 秒...")
                    time.sleep(15)
                    response = session.get(url, params=params, timeout=30, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                
                response.raise_for_status()
                
                # 检查响应内容类型
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' not in content_type:
                    print(f"[WARNING] 响应不是 JSON 格式: {content_type}")
                    if response.status_code == 429:
                        print(f"[WARNING] 遇到 429 错误，等待更长时间...")
                        time.sleep(10)
                    continue
                
                data = response.json()
                notes = data.get('notes', [])
                
                if not notes:
                    print(f"[INFO] 没有更多论文了")
                    break
                
                print(f"[INFO] 本页找到 {len(notes)} 篇论文，检查状态...")
                
                for note in notes:
                    content = note.get('content', {})
                    venue = content.get('venue', '')
                    venueid = content.get('venueid', '')
                    
                    # 处理title字段
                    title = content.get('title', 'Unknown Title')
                    if isinstance(title, dict):
                        title = title.get('value', 'Unknown Title')
                    
                    # 判断状态
                    paper_status = "UNKNOWN"
                    if 'Rejected' in str(venueid) or 'Rejected' in str(venue):
                        paper_status = "REJECTED"
                    elif 'Accepted' in str(venueid) or 'Accepted' in str(venue):
                        paper_status = "ACCEPTED"
                    elif 'Withdrawn' in str(venueid) or 'Withdrawn' in str(venue):
                        paper_status = "WITHDRAWN"
                    elif 'ICLR' in str(venue) and str(year) in str(venue):
                        # 如果venue包含ICLR和年份，可能是accepted
                        paper_status = "ACCEPTED"
                    
                    # 根据status筛选
                    should_include = False
                    if status == "all":
                        should_include = paper_status in ["ACCEPTED", "REJECTED"]
                    elif status == "accepted":
                        should_include = paper_status == "ACCEPTED"
                    elif status == "rejected":
                        should_include = paper_status == "REJECTED"
                    
                    if should_include:
                        paper_id = note.get('id', '')
                        
                        paper_info = {
                            'id': paper_id,
                            'forum_id': paper_id,
                            'title': title,
                            'venue': venue,
                            'venueid': venueid,
                            'status': paper_status,
                            'pdf_url': f"https://openreview.net/pdf?id={paper_id}"
                        }
                        
                        papers.append(paper_info)
                        print(f"  ✓ [{paper_status}] {title[:60]}...")
                    else:
                        pass  # 静默跳过不符合条件的论文
                
                offset += params["limit"]
                
                # 如果已经找到足够的论文，可以提前停止
                if len(papers) >= limit:
                    print(f"\n[INFO] 已找到 {len(papers)} 篇论文，停止搜索")
                    return papers[:limit]
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    print(f"[WARNING] 遇到 429 错误，等待 30 秒后继续...")
                    time.sleep(30)
                    continue
                else:
                    print(f"[WARNING] HTTP 错误: {e}")
                    # 尝试下一种查询方式
                    break
            except Exception as e:
                print(f"[WARNING] 查询出错: {e}")
                # 尝试下一种查询方式
                break
        
        # 如果当前方法找到了论文，停止尝试其他方法
        if papers:
            break
        
        # 重置offset以尝试下一种方法
        offset = 0
    
    print(f"\n[INFO] 总共找到 {len(papers)} 篇论文")
    return papers[:limit]


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
    num_accepted = 3  # 下载3篇accepted论文
    num_rejected = 3  # 下载3篇rejected论文
    
    # 创建保存目录
    base_dir = Path("data/raw/iclr2024")
    accepted_papers_dir = base_dir / "papers" / "accepted"
    rejected_papers_dir = base_dir / "papers" / "rejected"
    reviews_dir = base_dir / "reviews"
    
    accepted_papers_dir.mkdir(parents=True, exist_ok=True)
    rejected_papers_dir.mkdir(parents=True, exist_ok=True)
    reviews_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 搜索并下载 Accepted 论文
    print("\n" + "=" * 70)
    print("搜索 Accepted 论文")
    print("=" * 70)
    accepted_papers = search_iclr_papers(year=year, status="accepted", limit=num_accepted, max_pages=3)
    
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
    
    # 2. 搜索并下载 Rejected 论文
    print("\n" + "=" * 70)
    print("搜索 Rejected 论文")
    print("=" * 70)
    rejected_papers = search_iclr_papers(year=year, status="rejected", limit=num_rejected, max_pages=3)
    
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
    
    # 总结
    print(f"\n{'=' * 70}")
    print(f"下载完成！")
    print(f"  - Accepted 论文: {len(accepted_papers)} 篇 -> {accepted_papers_dir}")
    print(f"  - Rejected 论文: {len(rejected_papers)} 篇 -> {rejected_papers_dir}")
    print(f"  - Reviews: {reviews_dir}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()

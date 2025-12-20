"""
下载 NeurIPS 2024 中被拒绝（Rejected）的论文
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

def search_rejected_papers(year: int = 2024, limit: int = 5, max_pages: int = 5) -> List[Dict]:
    """
    搜索被拒绝的论文
    
    Args:
        year: 会议年份
        limit: 每页返回数量
        max_pages: 最多搜索页数
        
    Returns:
        被拒绝的论文列表
    """
    print(f"=" * 70)
    print(f"搜索 NeurIPS {year} 中被拒绝的论文")
    print(f"=" * 70)
    print()
    
    rejected_papers = []
    offset = 0
    
    # 使用GET方法，参考之前成功的代码
    # 先获取一批论文，然后筛选出rejected的
    query_methods = [
        {
            "name": "domain_any_venue",
            "params": {
                "domain": f"NeurIPS.cc/{year}/Conference",
                "content.venue": f"NeurIPS {year}",
                "limit": 50,
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
        print(f"[INFO] 将获取论文并筛选出被拒绝的...")
        
        for page in range(max_pages):
            print(f"\n[INFO] 搜索第 {page + 1} 页 (offset={offset})...")
            
            url = f"{base_url}/notes"
            params = base_params.copy()
            params["offset"] = offset
            params["limit"] = 50  # 增加每页数量以提高效率
            
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
                    print(f"[INFO] 没有更多论文了，尝试下一种查询方式...")
                    break
                
                print(f"[INFO] 本页找到 {len(notes)} 篇论文，检查状态...")
                
                for note in notes:
                    content = note.get('content', {})
                    venue = content.get('venue', '')
                    venueid = content.get('venueid', '')
                    
                    # 处理title字段（可能是dict或string）
                    title = content.get('title', 'Unknown Title')
                    if isinstance(title, dict):
                        title = title.get('value', 'Unknown Title')
                    
                    # 检查是否被拒绝
                    is_rejected = False
                    if 'Rejected' in str(venueid) or 'Rejected' in str(venue):
                        is_rejected = True
                    elif 'rejected' in str(venueid).lower() or 'rejected' in str(venue).lower():
                        is_rejected = True
                    
                    # 排除已接受的论文
                    is_accepted = False
                    if 'Accepted' in str(venueid) or 'Accepted' in str(venue):
                        is_accepted = True
                    elif 'accepted' in str(venueid).lower() or 'accepted' in str(venue).lower():
                        is_accepted = True
                    
                    if is_rejected and not is_accepted:
                        paper_id = note.get('id', '')
                        
                        paper_info = {
                            'id': paper_id,
                            'forum_id': paper_id,  # OpenReview 中 id 就是 forum_id
                            'title': title,
                            'venue': venue,
                            'venueid': venueid,
                            'pdf_url': f"https://openreview.net/pdf?id={paper_id}"
                        }
                        
                        rejected_papers.append(paper_info)
                        print(f"  ✓ [REJECTED] {title[:60]}...")
                    elif is_accepted:
                        pass  # 静默跳过已接受的论文
                    else:
                        pass  # 静默跳过状态未知的论文
                
                offset += params["limit"]
                
                # 如果已经找到足够的论文，可以提前停止
                if len(rejected_papers) >= limit:
                    print(f"\n[INFO] 已找到 {len(rejected_papers)} 篇被拒绝的论文，停止搜索")
                    return rejected_papers
                    
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
                print(f"[WARNING] 搜索出错: {e}")
                # 尝试下一种查询方式
                break
        
        # 如果当前方法找到了论文，停止尝试其他方法
        if rejected_papers:
            break
        
        # 重置offset以尝试下一种方法
        offset = 0
    
    print(f"\n[INFO] 总共找到 {len(rejected_papers)} 篇被拒绝的论文")
    return rejected_papers


def download_paper_pdf(paper_info: Dict, save_dir: Path) -> Optional[str]:
    """下载论文PDF"""
    paper_id = paper_info['id']
    pdf_url = paper_info['pdf_url']
    
    pdf_path = save_dir / f"{paper_id}.pdf"
    
    if pdf_path.exists():
        print(f"  [SKIP] PDF 已存在: {pdf_path.name}")
        return str(pdf_path)
    
    try:
        print(f"  [DOWNLOAD] 下载 PDF: {pdf_url}")
        time.sleep(2)  # 避免请求过快
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
    paper_id = paper_info['id']
    
    reviews_path = save_dir / f"{paper_id}_reviews.json"
    
    if reviews_path.exists():
        print(f"  [SKIP] Reviews 已存在: {reviews_path.name}")
        try:
            with open(reviews_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    try:
        print(f"  [DOWNLOAD] 下载 Reviews...")
        time.sleep(3)  # 避免请求过快
        
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
    # 配置
    year = 2024
    num_papers = 3  # 下载3篇被拒绝的论文
    max_search_pages = 10  # 最多搜索10页
    
    # 创建保存目录
    base_dir = Path("data/raw")
    papers_dir = base_dir / "papers"
    reviews_dir = base_dir / "reviews"
    papers_dir.mkdir(parents=True, exist_ok=True)
    reviews_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 搜索被拒绝的论文
    rejected_papers = search_rejected_papers(year=year, limit=50, max_pages=max_search_pages)
    
    if not rejected_papers:
        print("\n[ERROR] 未找到被拒绝的论文")
        print("[INFO] 可能的原因：")
        print("  1. OpenReview API 限制")
        print("  2. 论文状态字段命名不同")
        print("  3. 需要更多时间等待API响应")
        return
    
    # 限制下载数量
    papers_to_download = rejected_papers[:num_papers]
    
    print(f"\n{'=' * 70}")
    print(f"开始下载 {len(papers_to_download)} 篇被拒绝的论文")
    print(f"{'=' * 70}\n")
    
    # 2. 下载每篇论文的PDF和Reviews
    for i, paper_info in enumerate(papers_to_download, 1):
        print(f"\n[{i}/{len(papers_to_download)}] {paper_info['title'][:60]}...")
        print(f"  Forum ID: {paper_info['forum_id']}")
        print(f"  Venue: {paper_info['venue']}")
        
        # 下载PDF
        pdf_path = download_paper_pdf(paper_info, papers_dir)
        
        # 下载Reviews
        reviews = download_reviews(paper_info, reviews_dir)
        
        # 保存论文信息
        info_path = papers_dir / f"{paper_info['id']}_info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(paper_info, f, ensure_ascii=False, indent=2)
        
        # 在论文之间添加延迟
        if i < len(papers_to_download):
            wait_time = 5
            print(f"\n[INFO] 等待 {wait_time} 秒以避免API限制...")
            time.sleep(wait_time)
    
    print(f"\n{'=' * 70}")
    print(f"下载完成！")
    print(f"  - 论文PDF: {papers_dir}")
    print(f"  - Reviews: {reviews_dir}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()


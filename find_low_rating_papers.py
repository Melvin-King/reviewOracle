"""
通过低 rating 推断被拒绝的论文
注意：这只是推断，不是100%准确
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


def get_paper_reviews(forum_id: str) -> List[Dict]:
    """获取论文的reviews"""
    try:
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
            
            for inv in invitations:
                if inv.endswith('/-/Official_Review'):
                    reviews.append(note)
                    break
        
        return reviews
    except Exception as e:
        print(f"    [ERROR] 获取reviews失败: {e}")
        return []


def calculate_avg_rating(reviews: List[Dict]) -> Optional[float]:
    """计算平均rating"""
    ratings = []
    for review in reviews:
        content = review.get('content', {})
        rating = content.get('rating', None)
        if rating is not None:
            try:
                rating_value = int(rating) if isinstance(rating, (int, str)) else None
                if rating_value is not None:
                    ratings.append(rating_value)
            except:
                pass
    
    if ratings:
        return sum(ratings) / len(ratings)
    return None


def search_and_filter_low_rating_papers(year: int = 2024, max_papers: int = 100, 
                                        rating_threshold: float = 5.0) -> List[Dict]:
    """搜索论文并筛选出低rating的"""
    print("=" * 70)
    print(f"搜索 NeurIPS {year} 中低 rating 的论文（可能是被拒绝的）")
    print(f"Rating 阈值: < {rating_threshold}")
    print("=" * 70)
    print()
    
    low_rating_papers = []
    offset = 0
    checked_count = 0
    
    # 使用 domain_any_venue 查询
    url = f"{base_url}/notes"
    base_params = {
        "domain": f"NeurIPS.cc/{year}/Conference",
        "content.venue": f"NeurIPS {year}",
        "limit": 10,  # 每次查询少量论文，避免API限制
        "details": "writable,signatures,invitation,presentation,tags",
        "trash": "true"
    }
    
    while len(low_rating_papers) < max_papers and checked_count < max_papers * 3:
        print(f"\n[INFO] 查询 offset={offset}...")
        
        params = base_params.copy()
        params["offset"] = offset
        
        try:
            time.sleep(5)
            response = session.get(url, params=params, timeout=30)
            
            if response.status_code == 429:
                print(f"[WARNING] 遇到 429 错误，等待 20 秒...")
                time.sleep(20)
                continue
            
            response.raise_for_status()
            data = response.json()
            notes = data.get('notes', [])
            
            if not notes:
                print(f"[INFO] 没有更多论文了")
                break
            
            print(f"[INFO] 本批找到 {len(notes)} 篇论文，检查 ratings...")
            
            for note in notes:
                checked_count += 1
                paper_id = note.get('id', '')
                content = note.get('content', {})
                title = content.get('title', {})
                if isinstance(title, dict):
                    title = title.get('value', 'Unknown Title')
                else:
                    title = str(title)
                
                print(f"  [{checked_count}] 检查: {title[:50]}...")
                
                # 获取reviews并计算平均rating
                reviews = get_paper_reviews(paper_id)
                avg_rating = calculate_avg_rating(reviews)
                
                if avg_rating is not None:
                    print(f"    平均 Rating: {avg_rating:.2f} (基于 {len(reviews)} 个reviews)")
                    
                    if avg_rating < rating_threshold:
                        venue = content.get('venue', '')
                        venueid = content.get('venueid', '')
                        
                        paper_info = {
                            'id': paper_id,
                            'forum_id': paper_id,
                            'title': title,
                            'venue': venue,
                            'venueid': venueid,
                            'avg_rating': avg_rating,
                            'num_reviews': len(reviews),
                            'pdf_url': f"https://openreview.net/pdf?id={paper_id}",
                            'status': 'LOW_RATING'  # 标记为低rating
                        }
                        
                        low_rating_papers.append(paper_info)
                        print(f"    ✓ [LOW RATING] 添加到候选列表")
                else:
                    print(f"    未找到 rating 信息")
                
                # 每检查一篇论文后稍作延迟
                time.sleep(2)
            
            offset += params["limit"]
            
            # 如果已经找到足够的论文，可以提前停止
            if len(low_rating_papers) >= max_papers:
                break
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"[WARNING] 遇到 429 错误，等待 30 秒后继续...")
                time.sleep(30)
                continue
            else:
                print(f"[ERROR] HTTP 错误: {e}")
                break
        except Exception as e:
            print(f"[ERROR] 查询出错: {e}")
            break
    
    print(f"\n[INFO] 总共找到 {len(low_rating_papers)} 篇低 rating 论文")
    return low_rating_papers


def download_paper_data(paper_info: Dict, papers_dir: Path, reviews_dir: Path):
    """下载论文的PDF和Reviews"""
    forum_id = paper_info['forum_id']
    
    # 下载PDF
    pdf_path = papers_dir / f"{forum_id}.pdf"
    if not pdf_path.exists():
        try:
            print(f"  [DOWNLOAD] 下载 PDF...")
            time.sleep(2)
            response = session.get(paper_info['pdf_url'], timeout=60, stream=True)
            response.raise_for_status()
            with open(pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"  [SUCCESS] PDF 已保存")
        except Exception as e:
            print(f"  [ERROR] PDF 下载失败: {e}")
    
    # 下载Reviews
    reviews_path = reviews_dir / f"{forum_id}_reviews.json"
    if not reviews_path.exists():
        reviews = get_paper_reviews(forum_id)
        if reviews:
            with open(reviews_path, 'w', encoding='utf-8') as f:
                json.dump(reviews, f, ensure_ascii=False, indent=2)
            print(f"  [SUCCESS] Reviews 已保存 ({len(reviews)} 个)")


def main():
    """主函数"""
    # 配置
    rating_threshold = 5.0  # rating < 5.0 的论文可能是被拒绝的
    max_papers_to_find = 3  # 最多找3篇
    
    # 创建保存目录
    base_dir = Path("data/raw")
    papers_dir = base_dir / "papers"
    reviews_dir = base_dir / "reviews"
    papers_dir.mkdir(parents=True, exist_ok=True)
    reviews_dir.mkdir(parents=True, exist_ok=True)
    
    # 搜索低rating论文
    low_rating_papers = search_and_filter_low_rating_papers(
        year=2024,
        max_papers=max_papers_to_find,
        rating_threshold=rating_threshold
    )
    
    if not low_rating_papers:
        print("\n[INFO] 未找到低 rating 论文")
        return
    
    # 显示结果
    print(f"\n{'=' * 70}")
    print(f"找到 {len(low_rating_papers)} 篇低 rating 论文（可能是被拒绝的）")
    print(f"{'=' * 70}\n")
    
    for i, paper in enumerate(low_rating_papers, 1):
        print(f"{i}. {paper['title'][:60]}...")
        print(f"   Forum ID: {paper['forum_id']}")
        print(f"   平均 Rating: {paper['avg_rating']:.2f}")
        print(f"   Reviews 数量: {paper['num_reviews']}")
        print()
    
    # 询问是否下载
    print(f"\n[INFO] 是否下载这 {len(low_rating_papers)} 篇论文？")
    print(f"[INFO] 开始下载...\n")
    
    # 下载每篇论文
    for i, paper_info in enumerate(low_rating_papers, 1):
        print(f"\n[{i}/{len(low_rating_papers)}] {paper_info['title'][:60]}...")
        download_paper_data(paper_info, papers_dir, reviews_dir)
        
        # 保存论文信息
        info_path = papers_dir / f"{paper_info['forum_id']}_info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(paper_info, f, ensure_ascii=False, indent=2)
        
        if i < len(low_rating_papers):
            wait_time = 5
            print(f"\n[INFO] 等待 {wait_time} 秒以避免API限制...")
            time.sleep(wait_time)
    
    print(f"\n{'=' * 70}")
    print(f"下载完成！")
    print(f"  - 论文PDF: {papers_dir}")
    print(f"  - Reviews: {reviews_dir}")
    print(f"\n注意：这些论文只是基于低 rating 推断的，不一定是被拒绝的")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()


"""
从 NIPS 2024 下载论文和 review 数据
支持从 OpenReview API 或 NIPS 官方网站下载
"""

import os
import json
import requests
from typing import List, Dict, Optional
from pathlib import Path
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class NIPSDownloader:
    """NIPS 论文和 review 下载器"""
    
    def __init__(self, base_url: str = "https://api2.openreview.net", 
                 download_path: str = "data/raw"):
        # 注意：OpenReview 实际使用的是 api2.openreview.net，不是 api.openreview.net！
        self.base_url = base_url
        self.download_path = Path(download_path)
        self.download_path.mkdir(parents=True, exist_ok=True)
        
        # 设置 session（对于 reviews 下载，禁用自动重试，手动控制延迟）
        self.session = requests.Session()
        # 对于 reviews，使用更保守的重试策略
        retry_strategy = Retry(
            total=1,  # 减少重试次数
            backoff_factor=5,  # 增加退避时间
            status_forcelist=[500, 502, 503, 504],  # 429 不自动重试，手动处理
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def search_nips_papers(self, year: int = 2024, limit: int = 3) -> List[Dict]:
        """
        搜索 NIPS 论文
        
        Args:
            year: 会议年份
            limit: 返回论文数量
            
        Returns:
            论文列表，每个包含 id, title, pdf_url 等信息
        """
        print(f"[INFO] 搜索 {year} 年 NeurIPS 论文...")
        print(f"[INFO] 注意：OpenReview API 可能有限制，如果 API 查询失败，")
        print(f"[INFO] 请考虑使用网页抓取方式或手动准备数据")
        
        url = f"{self.base_url}/notes"
        
        # 使用正确的 API 和查询方式
        # 关键发现：需要使用 api2.openreview.net 和 domain 参数
        query_methods = [
            {
                "method": "domain_venue",
                "params": {
                    "domain": f"NeurIPS.cc/{year}/Conference",
                    "content.venue": f"NeurIPS {year} oral",
                    "limit": limit,
                    "offset": 0,
                    "details": "writable,signatures,invitation,presentation,tags",
                    "trash": "true"
                }
            },
            {
                "method": "domain_any_venue",
                "params": {
                    "domain": f"NeurIPS.cc/{year}/Conference",
                    "content.venue": f"NeurIPS {year}",
                    "limit": limit,
                    "offset": 0,
                    "details": "writable,signatures,invitation,presentation,tags",
                    "trash": "true"
                }
            },
            {
                "method": "domain_only",
                "params": {
                    "domain": f"NeurIPS.cc/{year}/Conference",
                    "limit": limit,
                    "offset": 0,
                    "details": "writable,signatures,invitation,presentation,tags",
                    "trash": "true"
                }
            }
        ]
        
        notes = []
        
        for query_info in query_methods:
            method = query_info["method"]
            params = query_info["params"]
            
            try:
                # 添加延迟避免请求过快（OpenReview 有严格的速率限制）
                print(f"[INFO] 尝试查询方式: {method}")
                time.sleep(5)  # 增加延迟避免 429 错误
                response = self.session.get(url, params=params, timeout=30, headers={
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
                
                if notes:
                    print(f"[INFO] 找到 {len(notes)} 篇论文（使用 {method} 方式）")
                    break
                else:
                    print(f"[INFO] 该查询方式没有返回结果")
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    print(f"[WARNING] 遇到 429 错误（请求过快），等待 15 秒后重试...")
                    time.sleep(15)
                    # 重试一次
                    try:
                        response = self.session.get(url, params=params, timeout=30, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        response.raise_for_status()
                        data = response.json()
                        notes = data.get('notes', [])
                        if notes:
                            print(f"[INFO] 重试成功，找到 {len(notes)} 篇论文")
                            break
                    except:
                        pass
                print(f"[WARNING] 尝试 {method} 时出错: {e}")
                continue
            except Exception as e:
                print(f"[WARNING] 尝试 {method} 时出错: {e}")
                continue
        
        if not notes:
            print(f"[WARNING] 所有查询方式都返回空结果")
            print(f"[INFO] 请检查：")
            print(f"  1. 网络连接是否正常")
            print(f"  2. OpenReview API 是否可访问")
            print(f"  3. 可以尝试手动准备数据")
            return []
        
        try:
            papers = []
            for note in notes:
                paper_info = {
                    'id': note.get('id', ''),
                    'number': note.get('number', 0),
                    'title': note.get('content', {}).get('title', {}).get('value', 'Unknown Title'),
                    'pdf_url': None,
                    'openreview_id': note.get('id', '')
                }
                
                # 获取 PDF URL - OpenReview 的标准格式
                paper_id = note.get('id', '')
                if paper_id:
                    # OpenReview PDF URL 格式
                    paper_info['pdf_url'] = f"https://openreview.net/pdf?id={paper_id}"
                
                # 也可以尝试从 content 中获取
                if 'content' in note and 'pdf' in note['content']:
                    pdf_value = note['content']['pdf'].get('value', '')
                    if pdf_value and pdf_value.startswith('http'):
                        paper_info['pdf_url'] = pdf_value
                
                papers.append(paper_info)
                print(f"  - 找到论文: {paper_info['title'][:50]}... (ID: {paper_info['id']})")
            
            print(f"[INFO] 共找到 {len(papers)} 篇论文")
            return papers
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] API 请求失败: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON 解析失败: {e}")
            return []
        except Exception as e:
            print(f"[ERROR] 搜索论文时出错: {e}")
            return []
    
    def download_paper_pdf(self, paper_id: str, pdf_url: str) -> Optional[str]:
        """
        下载论文 PDF
        
        Args:
            paper_id: 论文 ID
            pdf_url: PDF 下载链接
            
        Returns:
            保存的文件路径，失败返回 None
        """
        papers_dir = self.download_path / "papers"
        papers_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_path = papers_dir / f"{paper_id}.pdf"
        
        try:
            print(f"[INFO] 下载论文 {paper_id}...")
            time.sleep(1)  # 添加延迟
            response = self.session.get(pdf_url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"[INFO] 论文已保存到: {pdf_path}")
            return str(pdf_path)
        except Exception as e:
            print(f"[ERROR] 下载论文失败: {e}")
            return None
    
    def download_reviews(self, paper_id: str, openreview_id: Optional[str] = None) -> Optional[List[Dict]]:
        """
        下载论文的 review
        
        Args:
            paper_id: 论文 ID（用于保存文件）
            openreview_id: OpenReview 论文 ID（用于 API 查询）
            
        Returns:
            Review 列表，每个包含 reviewer_id, content 等
        """
        reviews_dir = self.download_path / "reviews"
        reviews_dir.mkdir(parents=True, exist_ok=True)
        
        if not openreview_id:
            openreview_id = paper_id
        
        print(f"[INFO] 下载论文 {paper_id} 的 reviews...")
        
        # 使用正确的 API 参数查询 reviews（参考网页实际调用）
        # 关键：不指定 invitation，获取 forum 下的所有 notes，然后过滤出 reviews
        url = f"{self.base_url}/notes"
        
        # 方法1：获取 forum 下的所有 notes（网页实际使用的方法）
        # 注意：网页实际调用包含 count=true 参数，但这里不需要
        params_all = {
            "domain": "NeurIPS.cc/2024/Conference",
            "forum": openreview_id,
            "details": "writable,signatures,invitation,presentation,tags",
            "trash": "true",
            "limit": 1000
        }
        
        # 方法2：指定 invitation（备选）
        params_invitation = {
            "domain": "NeurIPS.cc/2024/Conference",
            "forum": openreview_id,
            "invitation": "NeurIPS.cc/2024/Conference/-/Official_Review",
            "details": "writable,signatures,invitation,presentation,tags",
            "trash": "true",
            "limit": 1000
        }
        
        reviews = []
        notes = []
        
        # 先尝试方法1（获取所有 notes，然后过滤）
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 大幅增加等待时间：第一次 5 分钟，之后每次增加 2 分钟
                wait_time = 300 + retry_count * 120  # 5分钟 + 每次增加2分钟
                wait_minutes = wait_time // 60
                print(f"  - 等待 {wait_minutes} 分钟以避免请求过快（尝试 {retry_count + 1}/{max_retries}）...")
                time.sleep(wait_time)
                
                response = self.session.get(url, params=params_all, timeout=60)
                
                if response.status_code == 429:
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"  - 遇到 429 错误，将在下次重试时等待更长时间（{wait_minutes + 2} 分钟）...")
                        continue
                    else:
                        print(f"  - 达到最大重试次数，放弃下载 reviews")
                        print(f"  - 建议：等待更长时间后手动运行，或使用网页抓取方式")
                        break
                
                response.raise_for_status()
                data = response.json()
                all_notes = data.get('notes', [])
                
                # 过滤出 reviews（只选择真正的 Official Review，排除 Rebuttal）
                for note in all_notes:
                    # invitation 可能是字符串或数组
                    invitations = note.get('invitations', [])
                    if isinstance(invitations, str):
                        invitations = [invitations]
                    elif not isinstance(invitations, list):
                        invitations = []
                    
                    # 只选择 invitation 以 "/-/Official_Review" 结尾的（真正的 Official Review）
                    # 排除 Rebuttal（如 "Official_Review1/-/Rebuttal"）
                    is_official_review = False
                    for inv in invitations:
                        if inv.endswith('/-/Official_Review') or inv.endswith('/-/Official_Review'):
                            is_official_review = True
                            break
                    
                    if is_official_review:
                        notes.append(note)
                
                if notes:
                    print(f"  - 从 {len(all_notes)} 个 notes 中过滤出 {len(notes)} 个 reviews")
                    break
                else:
                    print(f"  - 未找到 reviews，但获取到 {len(all_notes)} 个 notes")
                    # 如果方法1失败，尝试方法2
                    if retry_count == 0:  # 只在第一次尝试时使用方法2
                        print(f"  - 尝试方法2（指定 invitation）...")
                        time.sleep(30)
                        response = self.session.get(url, params=params_invitation, timeout=30)
                        if response.status_code == 200:
                            data = response.json()
                            notes = data.get('notes', [])
                            if notes:
                                print(f"  - 方法2成功，找到 {len(notes)} 个 reviews")
                                break
                    break
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    retry_count += 1
                    if retry_count < max_retries:
                        continue
                    else:
                        print(f"  - 达到最大重试次数，放弃下载 reviews")
                        break
                else:
                    print(f"  - HTTP 错误: {e}")
                    break
            except Exception as e:
                print(f"  - 请求失败: {e}")
                break
        
        try:
            # 解析 reviews
            for idx, note in enumerate(notes):
                content = note.get('content', {})
                
                # 构建完整的 review 内容
                parts = []
                
                # Summary
                if 'summary' in content and content['summary'].get('value'):
                    parts.append(f"Summary: {content['summary']['value']}")
                
                # Strengths
                if 'strengths' in content:
                    strengths = content['strengths'].get('value', '')
                    if isinstance(strengths, list):
                        strengths = '\n'.join([f"- {item}" if isinstance(item, dict) else str(item) for item in strengths])
                    if strengths:
                        parts.append(f"Strengths:\n{strengths}")
                
                # Weaknesses
                if 'weaknesses' in content:
                    weaknesses = content['weaknesses'].get('value', '')
                    if isinstance(weaknesses, list):
                        weaknesses = '\n'.join([f"- {item}" if isinstance(item, dict) else str(item) for item in weaknesses])
                    if weaknesses:
                        parts.append(f"Weaknesses:\n{weaknesses}")
                
                # Questions
                if 'questions' in content and content['questions'].get('value'):
                    parts.append(f"Questions: {content['questions']['value']}")
                
                # Limitations
                if 'limitations' in content and content['limitations'].get('value'):
                    parts.append(f"Limitations: {content['limitations']['value']}")
                
                review_data = {
                    'reviewer_id': f"R{idx+1}",
                    'review_id': note.get('id', ''),
                    'content': "\n\n".join(parts) if parts else "",
                    'summary': content.get('summary', {}).get('value', ''),
                    'strengths': content.get('strengths', {}).get('value', ''),
                    'weaknesses': content.get('weaknesses', {}).get('value', ''),
                    'rating': content.get('rating', {}).get('value', ''),
                    'confidence': content.get('confidence', {}).get('value', ''),
                    'soundness': content.get('soundness', {}).get('value', ''),
                    'presentation': content.get('presentation', {}).get('value', ''),
                    'contribution': content.get('contribution', {}).get('value', ''),
                }
                
                reviews.append(review_data)
            
            print(f"  - 成功获取 {len(reviews)} 个 reviews")
            
        except Exception as e:
            print(f"  - 获取 reviews 失败: {e}")
            print(f"  - 将创建空的 review 文件，可以手动填写")
        
        # 保存 reviews
        reviews_path = reviews_dir / f"{paper_id}_reviews.json"
        with open(reviews_path, 'w', encoding='utf-8') as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
        
        return reviews
    
    def download_nips_papers(self, year: int = 2024, num_papers: int = 3) -> List[str]:
        """
        下载指定数量的 NIPS 论文及其 reviews
        
        Args:
            year: 会议年份
            num_papers: 论文数量
            
        Returns:
            下载成功的论文 ID 列表
        """
        papers = self.search_nips_papers(year, num_papers)
        downloaded_ids = []
        
        for paper in papers:
            openreview_id = paper.get('openreview_id', paper.get('id', ''))
            paper_number = paper.get('number', len(downloaded_ids) + 1)
            paper_id = f"paper_{paper_number:03d}"
            
            # 下载 PDF
            pdf_url = paper.get('pdf_url')
            if pdf_url:
                pdf_path = self.download_paper_pdf(paper_id, pdf_url)
                if pdf_path:
                    # 下载 reviews（传入 openreview_id 用于查询）
                    self.download_reviews(paper_id, openreview_id)
                    downloaded_ids.append(paper_id)
                    time.sleep(1)  # 避免请求过快
            else:
                print(f"[WARNING] 论文 {paper_id} 没有 PDF URL，跳过")
        
        print(f"[INFO] 成功下载 {len(downloaded_ids)} 篇论文")
        return downloaded_ids


if __name__ == "__main__":
    downloader = NIPSDownloader()
    paper_ids = downloader.download_nips_papers(year=2024, num_papers=3)
    print(f"下载的论文 ID: {paper_ids}")


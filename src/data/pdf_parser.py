"""
PDF 解析工具
支持多种 PDF 解析库
"""

from pathlib import Path
from typing import Dict, List, Optional
import pdfplumber
import PyPDF2


class PDFParser:
    """PDF 解析器"""
    
    def __init__(self, method: str = "pdfplumber"):
        """
        Args:
            method: 解析方法，可选 "pdfplumber" 或 "pypdf2"
        """
        self.method = method
    
    def parse_pdf(self, pdf_path: str) -> str:
        """
        解析 PDF 并提取文本
        
        Args:
            pdf_path: PDF 文件路径
            
        Returns:
            提取的文本内容
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
        
        if self.method == "pdfplumber":
            return self._parse_with_pdfplumber(pdf_path)
        elif self.method == "pypdf2":
            return self._parse_with_pypdf2(pdf_path)
        else:
            raise ValueError(f"不支持的解析方法: {self.method}")
    
    def _parse_with_pdfplumber(self, pdf_path: Path) -> str:
        """使用 pdfplumber 解析"""
        text_parts = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    try:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                    except Exception as e:
                        print(f"[WARNING] 解析页面失败: {e}")
                        continue
        except Exception as e:
            raise RuntimeError(f"使用 pdfplumber 解析 PDF 失败: {e}")
        
        if not text_parts:
            raise ValueError(f"未能从 PDF 中提取任何文本: {pdf_path}")
        
        return "\n\n".join(text_parts)
    
    def _parse_with_pypdf2(self, pdf_path: Path) -> str:
        """使用 PyPDF2 解析"""
        text_parts = []
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    try:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                    except Exception as e:
                        print(f"[WARNING] 解析页面失败: {e}")
                        continue
        except Exception as e:
            raise RuntimeError(f"使用 PyPDF2 解析 PDF 失败: {e}")
        
        if not text_parts:
            raise ValueError(f"未能从 PDF 中提取任何文本: {pdf_path}")
        
        return "\n\n".join(text_parts)
    
    def extract_sections(self, pdf_text: str) -> Dict[str, str]:
        """
        提取论文章节结构
        
        Args:
            pdf_text: PDF 文本内容
            
        Returns:
            章节字典，key 为章节名，value 为章节内容
        """
        sections = {}
        lines = pdf_text.split('\n')
        current_section = "Introduction"
        current_content = []
        
        # 简单的章节识别（可以根据需要改进）
        section_keywords = [
            "Introduction", "Related Work", "Methodology", 
            "Method", "Experiments", "Results", "Discussion", 
            "Conclusion", "References"
        ]
        
        for line in lines:
            line_stripped = line.strip()
            # 检查是否是章节标题
            is_section = False
            for keyword in section_keywords:
                if keyword.lower() in line_stripped.lower() and len(line_stripped) < 100:
                    if current_section:
                        sections[current_section] = "\n".join(current_content)
                    current_section = line_stripped
                    current_content = []
                    is_section = True
                    break
            
            if not is_section:
                current_content.append(line)
        
        # 添加最后一个章节
        if current_section:
            sections[current_section] = "\n".join(current_content)
        
        return sections
    
    def clean_text(self, text: str) -> str:
        """
        清理文本
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        # 移除多余的空白字符
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)


if __name__ == "__main__":
    parser = PDFParser()
    # 测试代码
    # text = parser.parse_pdf("data/raw/papers/paper_001.pdf")
    # sections = parser.extract_sections(text)
    # print(sections.keys())


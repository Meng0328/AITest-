"""
Document Parser - 需求文档解析服务
支持 Word/Excel/PDF/图片一键上传，自动提取文本
"""

import os
import io
from typing import Dict, Any, List, Optional
from pathlib import Path


class DocParser:
    """文档解析器 - 支持多种格式的需求文档提取"""
    
    # 支持的文件扩展名白名单
    ALLOWED_EXTENSIONS = {
        'word': ['.docx', '.doc'],
        'excel': ['.xlsx', '.xls'],
        'pdf': ['.pdf'],
        'image': ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
    }
    
    def __init__(self):
        self.upload_folder = 'uploads'
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def is_allowed_file(self, filename: str) -> bool:
        """检查文件是否在白名单内"""
        ext = os.path.splitext(filename)[1].lower()
        for extensions in self.ALLOWED_EXTENSIONS.values():
            if ext in extensions:
                return True
        return False
    
    def get_file_type(self, filename: str) -> Optional[str]:
        """获取文件类型"""
        ext = os.path.splitext(filename)[1].lower()
        for file_type, extensions in self.ALLOWED_EXTENSIONS.items():
            if ext in extensions:
                return file_type
        return None
    
    def extract_text(self, filepath: str, file_type: Optional[str] = None) -> Dict[str, Any]:
        """
        提取文档文本
        
        Args:
            filepath: 文件路径
            file_type: 文件类型（可选，自动检测）
            
        Returns:
            {
                'success': bool,
                'raw_text': str,
                'file_type': str,
                'pages': int,
                'metadata': dict
            }
        """
        if not file_type:
            file_type = self.get_file_type(filepath)
        
        if not file_type:
            return {
                'success': False,
                'error': '不支持的文件格式'
            }
        
        try:
            if file_type == 'word':
                return self._extract_word(filepath)
            elif file_type == 'excel':
                return self._extract_excel(filepath)
            elif file_type == 'pdf':
                return self._extract_pdf(filepath)
            elif file_type == 'image':
                return self._extract_image(filepath)
            else:
                return {
                    'success': False,
                    'error': f'未实现 {file_type} 类型的解析'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_word(self, filepath: str) -> Dict[str, Any]:
        """提取 Word 文档文本"""
        try:
            from docx import Document
            
            doc = Document(filepath)
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            
            raw_text = '\n'.join(paragraphs)
            
            return {
                'success': True,
                'raw_text': raw_text,
                'file_type': 'word',
                'pages': len(paragraphs),
                'metadata': {
                    'paragraph_count': len(paragraphs),
                    'char_count': len(raw_text)
                }
            }
        except ImportError:
            return {
                'success': False,
                'error': '缺少 python-docx 库，请安装：pip install python-docx'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Word 解析失败：{str(e)}'
            }
    
    def _extract_excel(self, filepath: str) -> Dict[str, Any]:
        """提取 Excel 表格文本"""
        try:
            import pandas as pd
            
            # 读取所有 sheet
            excel_data = pd.read_excel(filepath, sheet_name=None)
            
            all_texts = []
            for sheet_name, df in excel_data.items():
                all_texts.append(f"=== Sheet: {sheet_name} ===")
                # 转换为文本
                text = df.to_string(index=False)
                all_texts.append(text)
            
            raw_text = '\n\n'.join(all_texts)
            
            return {
                'success': True,
                'raw_text': raw_text,
                'file_type': 'excel',
                'pages': len(excel_data),
                'metadata': {
                    'sheet_count': len(excel_data),
                    'char_count': len(raw_text)
                }
            }
        except ImportError:
            return {
                'success': False,
                'error': '缺少 pandas 或 openpyxl 库，请安装：pip install pandas openpyxl'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Excel 解析失败：{str(e)}'
            }
    
    def _extract_pdf(self, filepath: str) -> Dict[str, Any]:
        """提取 PDF 文档文本"""
        try:
            import pdfplumber
            
            all_texts = []
            page_count = 0
            
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        all_texts.append(f"--- Page {page.page_number} ---")
                        all_texts.append(text.strip())
                        page_count += 1
            
            raw_text = '\n\n'.join(all_texts)
            
            return {
                'success': True,
                'raw_text': raw_text,
                'file_type': 'pdf',
                'pages': page_count,
                'metadata': {
                    'page_count': page_count,
                    'char_count': len(raw_text)
                }
            }
        except ImportError:
            return {
                'success': False,
                'error': '缺少 pdfplumber 库，请安装：pip install pdfplumber'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'PDF 解析失败：{str(e)}'
            }
    
    def _extract_image(self, filepath: str) -> Dict[str, Any]:
        """使用 OCR 提取图片文本"""
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(filepath)
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            
            return {
                'success': True,
                'raw_text': text.strip(),
                'file_type': 'image',
                'pages': 1,
                'metadata': {
                    'image_size': image.size,
                    'char_count': len(text)
                }
            }
        except ImportError:
            return {
                'success': False,
                'error': '缺少 pytesseract 或 Pillow 库，请安装：pip install pytesseract Pillow'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'图片 OCR 失败：{str(e)}'
            }
    
    def save_uploaded_file(self, file, user_id: str = 'default') -> Dict[str, Any]:
        """
        保存上传的文件
        
        Args:
            file: werkzeug.datastructures.FileStorage 对象
            user_id: 用户 ID
            
        Returns:
            {
                'success': bool,
                'filepath': str,
                'filename': str,
                'file_type': str,
                'uuid': str
            }
        """
        import uuid
        from werkzeug.utils import secure_filename
        
        filename = secure_filename(file.filename)
        file_type = self.get_file_type(filename)
        
        if not file_type:
            return {
                'success': False,
                'error': '不支持的文件格式'
            }
        
        # 生成唯一目录
        unique_id = str(uuid.uuid4())
        save_dir = os.path.join(self.upload_folder, user_id, 'docs', unique_id)
        os.makedirs(save_dir, exist_ok=True)
        
        # 保存文件
        filepath = os.path.join(save_dir, filename)
        file.save(filepath)
        
        return {
            'success': True,
            'filepath': filepath,
            'filename': filename,
            'file_type': file_type,
            'uuid': unique_id,
            'relative_path': os.path.relpath(filepath, self.upload_folder)
        }


# 单例
_doc_parser_instance = None


def get_doc_parser() -> DocParser:
    """获取 DocParser 单例"""
    global _doc_parser_instance
    if _doc_parser_instance is None:
        _doc_parser_instance = DocParser()
    return _doc_parser_instance
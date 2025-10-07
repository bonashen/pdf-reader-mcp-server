"""
Academic text processing for proper reading order and formatting
"""
import re
from typing import List, Dict, Any, Tuple
from ..core.pdf_processor import PDFProcessor

class AcademicTextProcessor:
    """Handles academic-specific text processing"""
    
    # Math formula patterns
    MATH_PATTERNS = [
        r'\$[^$]+\$',  # LaTeX inline math
        r'\$\$[^$]+\$\$',  # LaTeX display math
        r'\\begin\{equation\}.*?\\end\{equation\}',  # LaTeX equations
        r'\\begin\{align\}.*?\\end\{align\}',  # LaTeX align
        r'[∑∏∫∮∆∇α-ωΑ-Ω≤≥≠±∞]',  # Math symbols
    ]
    
    @staticmethod
    async def extract_academic_text(pdf_path: str, page_num: int = None) -> Dict[str, Any]:
        """Extract text with proper academic reading order"""
        if page_num is not None:
            return await AcademicTextProcessor._process_single_page(pdf_path, page_num)
        
        # Process all pages
        doc = await PDFProcessor.get_pdf_document(pdf_path)
        all_text = ""
        page_texts = []
        
        for page_idx in range(len(doc)):
            page_result = await AcademicTextProcessor._process_single_page(pdf_path, page_idx)
            page_texts.append(page_result)
            all_text += page_result["processed_text"] + "\n\n"
        
        return {
            "full_text": all_text.strip(),
            "pages": page_texts,
            "total_pages": len(doc)
        }
    
    @staticmethod
    async def _process_single_page(pdf_path: str, page_num: int) -> Dict[str, Any]:
        """Process a single page for academic reading order"""
        blocks = await PDFProcessor.get_page_blocks(pdf_path, page_num)
        
        # Sort blocks by reading order (top-to-bottom, left-to-right for columns)
        sorted_blocks = AcademicTextProcessor._sort_blocks_reading_order(blocks)
        
        # Combine text and preserve formatting
        processed_text = ""
        math_formulas = []
        
        for block in sorted_blocks:
            text = block["text"]
            
            # Extract and preserve math formulas
            text, formulas = AcademicTextProcessor._extract_math_formulas(text)
            math_formulas.extend(formulas)
            
            # Clean and format text
            cleaned_text = AcademicTextProcessor._clean_academic_text(text)
            processed_text += cleaned_text + "\n\n"
        
        return {
            "processed_text": processed_text.strip(),
            "math_formulas": math_formulas,
            "page_number": page_num,
            "block_count": len(blocks)
        }
    
    @staticmethod
    def _sort_blocks_reading_order(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort text blocks in proper reading order for academic papers"""
        if not blocks:
            return blocks
        
        # Detect if we have columns by analyzing x-positions
        x_positions = [block["bbox"][0] for block in blocks]
        page_width = max([block["bbox"][2] for block in blocks])
        
        # Simple column detection: if we have blocks starting in different thirds
        left_third = page_width / 3
        right_third = 2 * page_width / 3
        
        left_blocks = [b for b in blocks if b["bbox"][0] < left_third]
        right_blocks = [b for b in blocks if b["bbox"][0] > right_third]
        
        if len(left_blocks) > 0 and len(right_blocks) > 0:
            # Two-column layout
            left_sorted = sorted(left_blocks, key=lambda x: x["bbox"][1])  # Sort by y
            right_sorted = sorted(right_blocks, key=lambda x: x["bbox"][1])  # Sort by y
            
            # Interleave columns based on y-position
            result = []
            left_idx = right_idx = 0
            
            while left_idx < len(left_sorted) and right_idx < len(right_sorted):
                if left_sorted[left_idx]["bbox"][1] < right_sorted[right_idx]["bbox"][1]:
                    result.append(left_sorted[left_idx])
                    left_idx += 1
                else:
                    result.append(right_sorted[right_idx])
                    right_idx += 1
            
            # Add remaining blocks
            result.extend(left_sorted[left_idx:])
            result.extend(right_sorted[right_idx:])
            
            return result
        else:
            # Single column or complex layout - sort by y-position
            return sorted(blocks, key=lambda x: x["bbox"][1])
    
    @staticmethod
    def _extract_math_formulas(text: str) -> Tuple[str, List[str]]:
        """Extract and preserve mathematical formulas"""
        formulas = []
        processed_text = text
        
        for pattern in AcademicTextProcessor.MATH_PATTERNS:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                formulas.append(match)
                # Replace with placeholder
                processed_text = processed_text.replace(match, f"[MATH_FORMULA_{len(formulas)}]")
        
        return processed_text, formulas
    
    @staticmethod
    def _clean_academic_text(text: str) -> str:
        """Clean and format academic text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common PDF extraction issues
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Fix missing spaces
        text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)  # Fix hyphenated words
        text = re.sub(r'\s+([.,;:])', r'\1', text)  # Fix punctuation spacing
        
        # Preserve paragraph breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    @staticmethod
    async def chunk_academic_content(pdf_path: str, chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """Break academic content into agent-friendly chunks"""
        text_data = await AcademicTextProcessor.extract_academic_text(pdf_path)
        
        chunks = []
        current_chunk = ""
        current_page = 0
        
        for page_data in text_data["pages"]:
            page_text = page_data["processed_text"]
            page_num = page_data["page_number"]
            
            # Split by sentences for better chunking
            sentences = re.split(r'(?<=[.!?])\s+', page_text)
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) > chunk_size:
                    if current_chunk:
                        chunks.append({
                            "chunk_id": len(chunks),
                            "text": current_chunk.strip(),
                            "page_start": current_page,
                            "page_end": page_num,
                            "word_count": len(current_chunk.split())
                        })
                    current_chunk = sentence
                    current_page = page_num
                else:
                    current_chunk += " " + sentence
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                "chunk_id": len(chunks),
                "text": current_chunk.strip(),
                "page_start": current_page,
                "page_end": current_page,
                "word_count": len(current_chunk.split())
            })
        
        return chunks
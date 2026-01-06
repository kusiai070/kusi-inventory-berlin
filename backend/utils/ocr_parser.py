"""
OCR Parser for invoice processing
Parser OCR para procesamiento de facturas
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import pytesseract
from PIL import Image
import io
import pdf2image
import logging

logger = logging.getLogger(__name__)

class OCRParser:
    """OCR Parser for Spanish invoices"""
    
    def __init__(self):
        # Spanish invoice patterns
        self.invoice_patterns = {
            'invoice_number': [
                r'(?:factura|rechnung|n[°º]\s+factura|nro\.?\s*factura|rechnungsnummer)[\s:]*([A-Z0-9\-]+)',
                r'(?:n[°º]\s*[:.]?\s*)([A-Z0-9\-]{5,20})',
                r'(?:ref\.?|referencia)[\s:]*([A-Z0-9\-]+)'
            ],
            'date': [
                r'(?:fecha|datum|rechnungsdatum|fecha\s+de\s+emisi[óo]n)[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})'
            ],
            'provider': [
                r'(?:proveedor|vendedor|lieferant|raz[óo]n\s+social|firma)[\s:]*(.{5,50})',
                r'(?:nombre|empresa|name)[\s:]*(.{5,50})'
            ],
            'total': [
                r'(?:total|gesamtsumme|gesamtbetrag|total\s+a\s+pagar)[\s:]*[€$]?\s*(\d+[,.]?\d{0,2})',
                r'(?:summe)[\s:]*(\d+[,.]?\d{0,2})'
            ],
            'subtotal': [
                r'(?:subtotal|netto|netto-betrag|base\s+imponible)[\s:]*[€$]?\s*(\d+[,.]?\d{0,2})'
            ],
            'tax': [
                r'(?:iva|mwst|mehrwertsteuer|impuesto)[\s:]*[€$]?\s*(\d+[,.]?\d{0,2})',
                r'(?:ust|vat)[\s:]*[€$]?\s*(\d+[,.]?\d{0,2})'
            ]
        }
        
        # Product line patterns
        self.product_patterns = [
            r'(.{5,40})\s+(\d+(?:[,.]\d{1,3})?)\s+x?\s*\$?\s*(\d+[,.]?\d{0,2})\s+\$?\s*(\d+[,.]?\d{0,2})',
            r'(.{5,40})\s+\$?\s*(\d+[,.]?\d{0,2})\s+(\d+(?:[,.]\d{1,3})?)\s+\$?\s*(\d+[,.]?\d{0,2})',
            r'(\d+(?:[,.]\d{1,3})?)\s+(.{5,40})\s+\$?\s*(\d+[,.]?\d{0,2})\s+\$?\s*(\d+[,.]?\d{0,2})'
        ]
    
    def process_invoice(self, file_content: bytes, content_type: str) -> Dict[str, Any]:
        """Process invoice file with OCR"""
        
        try:
            # Convert file to image
            if content_type == "application/pdf":
                # Limit to first page only and add timeout to prevent DoS
                images = pdf2image.convert_from_bytes(
                    file_content,
                    first_page=1,
                    last_page=1,  # Only process first page
                    timeout=15  # 15 second timeout
                )
                if not images:
                    return {"success": False, "error": "Could not convert PDF to image"}
                image = images[0]
            else:
                image = Image.open(io.BytesIO(file_content))
            
            # Preprocess image for better OCR
            processed_image = self._preprocess_image(image)
            
            # Perform OCR with Spanish and German language support
            custom_config = r'--oem 3 --psm 6 -l spa+deu'
            text = pytesseract.image_to_string(processed_image, config=custom_config)
            
            # Parse extracted text
            parsed_data = self._parse_invoice_text(text)
            
            # Extract products
            products = self._extract_products(text)
            
            # Calculate confidence based on extracted fields
            confidence = self._calculate_confidence(parsed_data, products)
            
            return {
                "success": True,
                "invoice_number": parsed_data.get("invoice_number"),
                "invoice_date": parsed_data.get("invoice_date"),
                "provider_name": parsed_data.get("provider"),
                "items": products,
                "subtotal": parsed_data.get("subtotal"),
                "tax": parsed_data.get("tax"),
                "total": parsed_data.get("total"),
                "confidence": confidence,
                "raw_text": text
            }
            
        except Exception as e:
            logger.error(f"OCR processing error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "raw_text": "",
                "confidence": 0.0
            }
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to grayscale using PIL
        image = image.convert('L')
        
        # Resize image if too small (improves OCR)
        width, height = image.size
        if width < 1000:
            scale_factor = 1000 / width
            new_size = (int(width * scale_factor), int(height * scale_factor))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        return image
    
    def _parse_invoice_text(self, text: str) -> Dict[str, Optional[str]]:
        """Parse invoice text to extract key fields"""
        
        result = {}
        text_lower = text.lower()
        
        # Extract invoice number
        result['invoice_number'] = self._extract_field(text, self.invoice_patterns['invoice_number'])
        
        # Extract date
        date_str = self._extract_field(text, self.invoice_patterns['date'])
        if date_str:
            result['invoice_date'] = self._normalize_date(date_str)
        else:
            result['invoice_date'] = None
        
        # Extract provider
        result['provider'] = self._extract_field(text, self.invoice_patterns['provider'])
        
        # Extract amounts
        result['subtotal'] = self._extract_amount(text, self.invoice_patterns['subtotal'])
        result['tax'] = self._extract_amount(text, self.invoice_patterns['tax'])
        result['total'] = self._extract_amount(text, self.invoice_patterns['total'])
        
        return result
    
    def _extract_field(self, text: str, patterns: List[str]) -> Optional[str]:
        """Extract field using regex patterns"""
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                # Clean up the value
                value = re.sub(r'\s+', ' ', value)
                value = value.replace('\n', ' ')
                return value[:100]  # Limit length
        
        return None
    
    def _extract_amount(self, text: str, patterns: List[str]) -> Optional[float]:
        """Extract monetary amount"""
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    amount_str = match.group(1).strip()
                    # Clean and convert
                    amount_str = amount_str.replace(',', '').replace('$', '')
                    return float(amount_str)
                except (ValueError, AttributeError):
                    continue
        
        return None
    
    def _extract_products(self, text: str) -> List[Dict[str, Any]]:
        """Extract product lines from invoice text"""
        
        products = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if len(line) < 10:  # Skip short lines
                continue
            
            for pattern in self.product_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        groups = match.groups()
                        
                        # Different patterns may have different group orders
                        if len(groups) == 4:
                            # Try to identify which group is which
                            values = list(groups)
                            
                            # Find quantity (usually a whole number)
                            quantity_idx = None
                            for i, val in enumerate(values):
                                if re.match(r'^\d+$', val.strip()):
                                    quantity_idx = i
                                    break
                            
                            if quantity_idx is not None:
                                quantity = float(values[quantity_idx].replace(',', ''))
                                
                                # Find prices (decimal numbers)
                                prices = []
                                for i, val in enumerate(values):
                                    if i != quantity_idx and re.search(r'\d+[,.]?\d{0,2}', val):
                                        try:
                                            price = float(val.replace(',', '').replace('$', ''))
                                            prices.append(price)
                                        except ValueError:
                                            continue
                                
                                if len(prices) >= 2:
                                    unit_price = min(prices)
                                    total_price = max(prices)
                                    
                                    # Product name is the remaining value
                                    name_values = [v for i, v in enumerate(values) if i not in [quantity_idx] + [i for i, p in enumerate(values) if p in [str(unit_price), str(total_price)]]]
                                    product_name = name_values[0] if name_values else "Unknown Product"
                                    
                                    products.append({
                                        "product_name": product_name[:50],
                                        "quantity": quantity,
                                        "unit_price": unit_price,
                                        "total_price": total_price
                                    })
                                    break
                                    
                    except (ValueError, IndexError):
                        continue
        
        # If no products found with patterns, try simple line parsing
        if not products:
            products = self._extract_products_simple(text)
        
        return products[:20]  # Limit to 20 products
    
    def _extract_products_simple(self, text: str) -> List[Dict[str, Any]]:
        """Simple product extraction as fallback"""
        
        products = []
        lines = text.split('\n')
        
        for line in lines:
            # Look for lines with both text and numbers
            if re.search(r'[a-zA-Z]{3,}', line) and re.search(r'\d+[,.]?\d{0,2}', line):
                # Try to extract numbers
                numbers = re.findall(r'\d+[,.]?\d{0,2}', line)
                if len(numbers) >= 2:
                    try:
                        # Extract product name (text before numbers)
                        parts = re.split(r'\d+[,.]?\d{0,2}', line)
                        if parts:
                            product_name = parts[0].strip()[:50]
                            
                            # Convert numbers
                            nums = [float(n.replace(',', '')) for n in numbers[:3]]
                            
                            if len(nums) >= 2:
                                quantity = nums[0] if nums[0] < 100 else 1
                                unit_price = min(nums[1:])
                                total_price = max(nums[1:])
                                
                                products.append({
                                    "product_name": product_name,
                                    "quantity": quantity,
                                    "unit_price": unit_price,
                                    "total_price": total_price
                                })
                    except (ValueError, IndexError):
                        continue
        
        return products
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize date to ISO format"""
        
        try:
            # Try different date formats
            formats = ['%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y', '%m-%d-%Y', '%d/%m/%y', '%d-%m-%y']
            
            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_str.strip(), fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            return None
        except:
            return None
    
    def _calculate_confidence(self, parsed_data: Dict, products: List) -> float:
        """Calculate OCR confidence score"""
        
        score = 0.0
        max_score = 5.0
        
        # Essential fields
        if parsed_data.get('invoice_number'):
            score += 1.0
        if parsed_data.get('invoice_date'):
            score += 1.0
        if parsed_data.get('total'):
            score += 1.0
        if parsed_data.get('provider'):
            score += 0.5
        if parsed_data.get('subtotal') or parsed_data.get('tax'):
            score += 0.5
        
        # Products bonus
        if len(products) > 0:
            score += min(len(products) * 0.1, 1.0)
        
        return min(score / max_score, 1.0)
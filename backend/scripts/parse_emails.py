#!/usr/bin/env python3
"""
Email Parser for Few-Shot Examples
Extracts components (subject, pre-header, body, CTAs, images) from email files
Supports both .eml and .html formats
"""
import email
import re
import json
from pathlib import Path
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailComponentExtractor:
    """Extract structured components from email HTML"""
    
    def __init__(self):
        self.cta_patterns = [
            r'<a[^>]*>(Shop Now|Discover|Explore|Buy Now|Learn More|View Collection|Get Started|Sign Up|Subscribe|Download|Claim|Save|Shop|Order Now)[^<]*</a>',
            r'<button[^>]*>([^<]+)</button>'
        ]
        
    def extract_subject(self, email_message) -> Optional[str]:
        """Extract email subject"""
        return email_message.get('subject', '').strip()
    
    def extract_preheader(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract pre-header text
        Common patterns:
        - <span style="display:none">...</span>
        - First text node before main content
        - Meta tag with name="preheader"
        """
        # Method 1: Hidden span (most common)
        hidden_spans = soup.find_all('span', style=re.compile(r'display:\s*none'))
        for span in hidden_spans:
            text = span.get_text(strip=True)
            if text and len(text) > 10 and len(text) < 200:
                return text
        
        # Method 2: Look for preheader in comments or meta
        preheader_meta = soup.find('meta', attrs={'name': 'preheader'})
        if preheader_meta:
            return preheader_meta.get('content', '').strip()
        
        # Method 3: First paragraph with specific class names
        preheader_classes = ['preheader', 'preview-text', 'preview', 'email-preview']
        for cls in preheader_classes:
            elem = soup.find(class_=cls)
            if elem:
                text = elem.get_text(strip=True)
                if text:
                    return text
        
        return None
    
    def extract_ctas(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract all CTAs (Call-to-Actions) from email
        Returns list of {text, url, type}
        """
        ctas = []
        
        # Find all links that look like CTAs
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True)
            url = link.get('href', '')
            
            # Filter out footer links, unsubscribe, social links
            skip_patterns = [
                'unsubscribe', 'preference', 'facebook', 'instagram', 
                'twitter', 'linkedin', 'privacy', 'terms', 'mailto:'
            ]
            
            if any(pattern in url.lower() or pattern in text.lower() for pattern in skip_patterns):
                continue
            
            # CTA heuristics: buttons, short text, product/shop links
            is_button = link.find_parent(['button']) or 'button' in link.get('class', [])
            is_short = len(text) < 50
            is_action = any(word in text.lower() for word in ['shop', 'discover', 'explore', 'buy', 'view', 'get', 'learn', 'see', 'claim', 'save'])
            
            if (is_button or is_action) and is_short and text:
                ctas.append({
                    'text': text,
                    'url': url,
                    'type': 'button' if is_button else 'link'
                })
        
        # Also check for buttons without links
        for button in soup.find_all('button'):
            text = button.get_text(strip=True)
            if text and len(text) < 50:
                ctas.append({
                    'text': text,
                    'url': None,
                    'type': 'button'
                })
        
        return ctas
    
    def extract_body_sections(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract main body content sections
        Tries to identify distinct content blocks
        """
        sections = []
        
        # Remove header, footer, preheader, CTAs for cleaner extraction
        for elem in soup.find_all(['style', 'script', 'head']):
            elem.decompose()
        
        # Look for main content containers
        main_containers = soup.find_all(['table', 'div', 'td'], class_=re.compile(r'(content|body|main|article|text-block)', re.I))
        
        if not main_containers:
            # Fallback: all paragraphs
            main_containers = [soup]
        
        for container in main_containers:
            # Get all meaningful text blocks (p, h1-h6, div with text)
            text_elements = container.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div'])
            
            for elem in text_elements:
                text = elem.get_text(strip=True)
                # Filter out short snippets, likely navigation
                if text and len(text) > 30 and len(text) < 1000:
                    # Avoid duplicates
                    if text not in sections:
                        sections.append(text)
        
        return sections[:5]  # Limit to first 5 meaningful sections
    
    def extract_images(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract all images with URLs and alt text
        """
        images = []
        
        for img in soup.find_all('img', src=True):
            src = img.get('src', '')
            alt = img.get('alt', '').strip()
            
            # Skip tracking pixels and tiny images
            if any(skip in src.lower() for skip in ['tracking', 'pixel', '1x1', 'spacer']):
                continue
            
            # Try to get width/height to filter out small images
            width = img.get('width')
            height = img.get('height')
            
            if width and height:
                try:
                    if int(width) < 50 or int(height) < 50:
                        continue
                except ValueError:
                    pass
            
            images.append({
                'src': src,
                'alt': alt,
                'width': width,
                'height': height
            })
        
        return images
    
    def parse_email(self, email_path: Path) -> Dict:
        """
        Parse a single email file (.eml or .html)
        Returns structured component dictionary
        """
        logger.info(f"Parsing: {email_path.name}")
        
        try:
            if email_path.suffix == '.eml':
                # Parse .eml file
                with open(email_path, 'rb') as f:
                    msg = BytesParser(policy=policy.default).parse(f)
                
                subject = self.extract_subject(msg)
                
                # Get HTML body
                html_body = None
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == 'text/html':
                            html_body = part.get_content()
                            break
                else:
                    if msg.get_content_type() == 'text/html':
                        html_body = msg.get_content()
                
                if not html_body:
                    logger.warning(f"No HTML content found in {email_path.name}")
                    return None
                
            elif email_path.suffix in ['.html', '.htm']:
                # Parse raw HTML file
                with open(email_path, 'r', encoding='utf-8') as f:
                    html_body = f.read()
                subject = None  # Extract from <title> if available
            
            else:
                logger.warning(f"Unsupported file type: {email_path.suffix}")
                return None
            
            # Parse HTML
            soup = BeautifulSoup(html_body, 'html.parser')
            
            # Extract subject from <title> if not from .eml
            if not subject:
                title_tag = soup.find('title')
                subject = title_tag.get_text(strip=True) if title_tag else "Unknown Subject"
            
            # Extract all components
            components = {
                'filename': email_path.name,
                'subject': subject,
                'preheader': self.extract_preheader(soup),
                'body_sections': self.extract_body_sections(soup),
                'ctas': self.extract_ctas(soup),
                'images': self.extract_images(soup),
            }
            
            return components
            
        except Exception as e:
            logger.error(f"Error parsing {email_path.name}: {str(e)}")
            return None


def main():
    """Main script to parse all emails in data/sample_emails/"""
    
    # Setup paths
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / "data" / "sample_emails"
    output_file = base_dir / "data" / "parsed_examples.json"
    
    # Create directories if they don't exist
    input_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if input directory has files
    email_files = list(input_dir.glob("*.eml")) + list(input_dir.glob("*.html")) + list(input_dir.glob("*.htm"))
    
    if not email_files:
        logger.error(f"No email files found in {input_dir}")
        logger.info(f"Please add .eml or .html files to: {input_dir}")
        return
    
    logger.info(f"Found {len(email_files)} email files")
    
    # Parse all emails
    extractor = EmailComponentExtractor()
    parsed_emails = []
    
    for email_path in email_files:
        result = extractor.parse_email(email_path)
        if result:
            parsed_emails.append(result)
    
    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(parsed_emails, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Successfully parsed {len(parsed_emails)} emails")
    logger.info(f"📄 Output saved to: {output_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("PARSING SUMMARY")
    print("="*60)
    
    for email in parsed_emails:
        print(f"\n📧 {email['filename']}")
        print(f"   Subject: {email['subject']}")
        print(f"   Pre-header: {email['preheader'][:50] + '...' if email['preheader'] else 'None'}")
        print(f"   Body sections: {len(email['body_sections'])}")
        print(f"   CTAs: {len(email['ctas'])}")
        print(f"   Images: {len(email['images'])}")
        
        if email['ctas']:
            print(f"   CTA examples:")
            for cta in email['ctas'][:3]:
                print(f"      - {cta['text']}")
    
    print("\n" + "="*60)
    print(f"✅ Complete! Check {output_file} for full data")
    print("="*60)


if __name__ == "__main__":
    main()


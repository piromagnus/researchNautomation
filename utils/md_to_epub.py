#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Convert markdown files to EPUB.
Takes a full text markdown file and a summary markdown file and combines them into an EPUB.
"""

import argparse
import os
import sys
import re
import markdown
import mimetypes
import hashlib
# from PIL import Image  # Moved up since it's used in process_images
from ebooklib import epub
from datetime import datetime
from epub_utils import style

# Import latex conversion libraries
try:
    import latex2svg
except ImportError:
    print("Warning: latex2svg module not found. LaTeX formulas will not be converted to SVG.")
    latex2svg = None


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Convert markdown files to EPUB.')
    parser.add_argument('--full-text', '-f', required=True, 
                        help='Path to the full text markdown file')
    parser.add_argument('--summary', '-s', required=True,
                        help='Path to the summary markdown file')
    parser.add_argument('--output', '-o', 
                        help='Output EPUB file path (default: same name as full text with .epub extension)')
    parser.add_argument('--title', '-t', 
                        help='Title of the EPUB (default: filename of full text)')
    parser.add_argument('--author', '-a', default='AI Assistant',
                        help='Author name (default: AI Assistant)')
    return parser.parse_args()


def read_markdown_file(file_path):
    """Read markdown file content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        sys.exit(1)


def extract_title_from_content(content):
    """Extract title from markdown content (first heading)."""
    lines = content.strip().split('\n')
    for line in lines:
        if line.startswith('# '):
            return line.replace('# ', '')
    # If no title found, return None
    return None


def find_images_in_directory(directory):
    """Find all image files in a directory."""
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg')
    images = []
    
    try:
        for file in os.listdir(directory):
            if file.lower().endswith(image_extensions):
                images.append(os.path.join(directory, file))
    except Exception as e:
        print(f"Warning: Error finding images in directory {directory}: {e}")
    
    return images


def convert_latex_to_svg_file(latex, base_dir, is_display=False):
    """Convert LaTeX formula to SVG and save it as a file."""
    if latex2svg is None:
        return None
    
    try:
        # Add display math formatting if needed
        if is_display:
            latex = "$$" + r'\displaystyle ' + latex + "$$"
        else:
            latex = "$" + latex + "$"
        
        # Generate SVG content with proper namespace
        svg_output = latex2svg.latex2svg(latex)
        svg_content = svg_output['svg']
        
        # Ensure SVG has proper namespace
        if not 'xmlns="http://www.w3.org/2000/svg"' in svg_content:
            svg_content = svg_content.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"')
        
        # Create a unique filename based on the latex content
        latex_hash = hashlib.md5(latex.encode()).hexdigest()
        filename = f'formula_{latex_hash}.svg'
        
        return {
            'content': svg_content,
            'filename': filename,
            'latex': latex,
            'is_display': is_display,
            'media_type': 'image/svg+xml'
        }
    except Exception as e:
        print(f"Warning: Error converting LaTeX formula to SVG: {e}")
        return None

def process_latex_formulas(content, base_dir):
    """Convert all LaTeX formulas to SVG images."""
    if latex2svg is None:
        return content, []
    
    svg_refs = []
    
    # Convert display math mode: $$...$$
    def replace_display_latex(match):
        latex = match.group(1).strip()
        svg_data = convert_latex_to_svg_file(latex, base_dir, is_display=True)
        if svg_data:
            svg_refs.append(svg_data)
            return f'<div class="math-display"><img src="images/{svg_data["filename"]}" class="math-display" alt="{latex}" /></div>'
        return match.group(0)
    
    # Convert inline math mode: $...$
    def replace_inline_latex(match):
        latex = match.group(1).strip()
        svg_data = convert_latex_to_svg_file(latex, base_dir, is_display=False)
        if svg_data:
            svg_refs.append(svg_data)
            return f'<span class="math-inline"><img src="images/{svg_data["filename"]}" class="math-inline" alt="{latex}" /></span>'
        return match.group(0)
    
    # Process display math first
    content = re.sub(r'\$\$(.*?)\$\$', replace_display_latex, content, flags=re.DOTALL)
    # Then process inline math
    content = re.sub(r'\$([^\$]+?)\$', replace_inline_latex, content)
    
    return content, svg_refs

def convert_html_table_to_markdown(html_table):
    """Convert HTML table to markdown format."""
    # Remove newlines within cells but keep table structure
    html_table = re.sub(r'>\s+<', '><', html_table.strip())
    
    # Extract rows
    rows = re.findall(r'<tr>(.*?)</tr>', html_table, re.DOTALL)
    if not rows:
        return html_table
    
    markdown_rows = []
    max_cols = 0
    
    # First pass: determine max columns and clean cells
    cleaned_rows = []
    for row in rows:
        # Extract cells (both td and th)
        cells = re.findall(r'<t[dh]>(.*?)</t[dh]>', row, re.DOTALL)
        cleaned_cells = []
        for cell in cells:
            # Clean cell content: remove excessive whitespace
            cell = re.sub(r'\s+', ' ', cell.strip())
            # Handle any nested HTML tags (optional)
            cell = re.sub(r'<[^>]+>', '', cell)
            cleaned_cells.append(cell)
        
        max_cols = max(max_cols, len(cleaned_cells))
        cleaned_rows.append(cleaned_cells)
    
    # Second pass: build markdown table with proper alignment
    for i, cells in enumerate(cleaned_rows):
        while len(cells) < max_cols:
            cells.append('')
        
        row = '| ' + ' | '.join(cells) + ' |'
        markdown_rows.append(row)
        
        if i == 0:
            markdown_rows.append('|' + '|'.join([' :---: ' for _ in range(max_cols)]) + '|')
    
    return '\n'.join(markdown_rows)

def convert_markdown_table_to_html(md_table):
    """Convert markdown table to HTML format."""
    # Split into rows
    rows = [row.strip() for row in md_table.strip().split('\n')]
    if len(rows) < 3:  # Need at least header, separator, and one data row
        return md_table
    
    # Parse header row
    header_cells = [cell.strip() for cell in rows[0].split('|') if cell.strip()]
    
    # Parse alignment row
    align_specs = [cell.strip() for cell in rows[1].split('|') if cell.strip()]
    alignments = []
    for spec in align_specs:
        if spec.startswith(':') and spec.endswith(':'):
            alignments.append('center')
        elif spec.startswith(':'):
            alignments.append('left')
        elif spec.endswith(':'):
            alignments.append('right')
        else:
            alignments.append('left')
    
    # Build HTML table
    html = ['<table class="markdown-table">']
    
    # Add header
    html.append('  <thead>')
    html.append('    <tr>')
    for i, cell in enumerate(header_cells):
        align = f' style="text-align: {alignments[i]}"' if i < len(alignments) else ''
        html.append(f'      <th{align}>{cell}</th>')
    html.append('    </tr>')
    html.append('  </thead>')
    
    # Add body
    html.append('  <tbody>')
    for row in rows[2:]:  # Skip header and separator rows
        cells = [cell.strip() for cell in row.split('|') if cell.strip()]
        if cells:  # Skip empty rows
            html.append('    <tr>')
            for i, cell in enumerate(cells):
                align = f' style="text-align: {alignments[i]}"' if i < len(alignments) else ''
                html.append(f'      <td{align}>{cell}</td>')
            html.append('    </tr>')
    html.append('  </tbody>')
    html.append('</table>')
    
    return '\n'.join(html)

def process_markdown_for_epub(content, base_dir):
    """Process markdown content for EPUB conversion."""
    # Convert markdown tables to HTML first
    def replace_markdown_table(match):
        return convert_markdown_table_to_html(match.group(0))
    
    # Find and process all markdown tables
    content = re.sub(r'(?m)^\|(.+\|)+$\n\|[-:| ]+\|\n((?:\|.+\|\n?)+)', replace_markdown_table, content)
    
    # Convert HTML tables to markdown
    def replace_html_table(match):
        return convert_html_table_to_markdown(match.group(0))
    
    # Convert HTML tables first
    content = re.sub(r'<table>.*?</table>', replace_html_table, content, flags=re.DOTALL)
    
    # Convert LaTeX formulas to SVG
    content, svg_refs = process_latex_formulas(content, base_dir)
    # Process markdown tables to ensure they're complete
    def process_table(match):
        table = match.group(0)
        lines = table.split('\n')
        if len(lines) < 3:
            return table
        
        # Count columns in header
        header_cells = [x.strip() for x in lines[0].split('|') if x.strip()]
        header_cols = len(header_cells)
        
        # Process alignment row (make all centered by default)
        align_cells = [' :---: ' for _ in range(header_cols)]
        lines[1] = '|' + '|'.join(align_cells) + '|'
        
        # Process data rows
        processed_lines = [lines[0], lines[1]]
        for line in lines[2:]:
            if '|' not in line:
                continue
            cells = [x.strip() for x in line.split('|') if x]
            while len(cells) < header_cols:
                cells.append('')
            processed_line = '| ' + ' | '.join(cells) + ' |'
            processed_lines.append(processed_line)
        
        return '\n'.join(processed_lines)  # Fixed invalid backslash
    
    # Find and process all tables (both HTML converted and original markdown)
    content = re.sub(r'(?m)^\|(.+\|)+$\n\|[-:| ]+\|\n((?:\|.+\|\n?)+)', process_table, content)
    
    # Process images and get references
    content, image_refs = process_images(content, base_dir)
    
    # Add SVG references to image references
    for svg in svg_refs:
        image_refs.append({
            'path': None,
            'epub_path': f'images/{svg["filename"]}',
            'filename': svg['filename'],
            'content': svg['content'],
            'media_type': 'image/svg+xml',
            'is_svg_formula': True
        })
    
    return content, image_refs

def process_images(content, base_dir):
    """Process images in markdown content."""
    image_refs = []
    
    def get_image_dimensions(image_path):
        """Get actual image dimensions using Pillow."""
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                return img.size
        except Exception as e:
            print(f"Warning: Could not get image dimensions for {image_path}: {e}")
            return None, None
    
    def replace_sized_image(match):
        alt_text = match.group(1)
        size_spec = match.group(2) if match.group(2) else ''
        image_path = match.group(3)
        
        if image_path.startswith('[[') and image_path.endswith(']]'):
            image_path = image_path[2:-2]
        if not os.path.isabs(image_path):
            full_path = os.path.join(base_dir, image_path)
            if not os.path.exists(full_path):
                images_dir = os.path.join(base_dir, 'images')
                if os.path.exists(os.path.join(images_dir, image_path)):
                    full_path = os.path.join(images_dir, image_path)
            image_path = full_path
        
        if not os.path.exists(image_path):
            print(f"Warning: Image not found: {image_path}")
            return f'<div class="missing-image">[Missing image: {alt_text}]</div>'
    
        
        image_filename = os.path.basename(image_path)
        name, ext = os.path.splitext(image_filename)
        hash_value = hashlib.md5(image_path.encode()).hexdigest()[:8]
        unique_filename = f"{name}_{hash_value}{ext}"
        epub_path = f'images/{unique_filename}'
        
        if not any(img['path'] == image_path for img in image_refs):
            image_refs.append({
                'path': image_path,
                'epub_path': epub_path,
                'filename': unique_filename,
            })
        
        return f'<img src="{epub_path}" alt="{alt_text}" />'
    
    content = re.sub(r'!\[(.*?)\](?:\|(\d+(?:x\d+)?))?\((.*?)\)', replace_sized_image, content)
    content = re.sub(r'!\[\[(.*?)\]\]', lambda m: replace_sized_image(re.match(r'(.*?)()(\1)', m.group(1))), content)
    
    return content, image_refs

def extract_metadata(content):
    """Extract metadata from markdown content."""
    metadata = {
        'date': None,
        'tags': [],
        'authors': [],
    }
    
    lines = content.split('\n')
    parsing_metadata = False
    current_section = None
    
    for line in lines:
        line = line.strip()
        
        if not line:
            continue
        
        if line.startswith('date:'):
            metadata['date'] = line.replace('date:', '').strip()
        elif line.startswith('tags:'):
            current_section = 'tags'
            continue
        elif line.startswith('authors:'):
            current_section = 'authors'
            continue
        elif line.startswith('- ') and current_section:
            value = line.replace('- ', '').strip()
            if current_section == 'tags':
                metadata['tags'].append(value)
            elif current_section == 'authors':
                metadata['authors'].append(value)
        elif not line.startswith('-'):
            if not any(metadata.values()):
                continue
            else:
                break
    
    return metadata

def extract_headings(content):
    """Extract all headings from markdown content."""
    headings = []
    lines = content.split('\n')
    
    for line in lines:
        if line.startswith('#'):
            level = len(line.split()[0])
            title = line.replace('#', '').strip()
            heading_id = title.lower().replace(' ', '-')
            heading_id = re.sub(r'[^a-z0-9-]', '', heading_id)
            headings.append({
                'level': level,
                'title': title,
                'id': heading_id
            })
    
    return headings

def create_toc_from_headings(book, summary_headings, full_text_headings):
    """Create table of contents from headings."""
    def create_section(title, headings, base_file):
        """Create a section with its headings."""
        links = []
        links.append(epub.Link(base_file, title))
        for heading in headings:
            links.append(
                epub.Link(f'{base_file}#{heading["id"]}', '  ' * (heading['level'] - 1) + heading['title'])
            )
        return (epub.Section(title), links)
    
    toc = []
    toc.append(create_section('Summary', summary_headings, 'summary.xhtml'))
    toc.append(create_section('Full Content', full_text_headings, 'content.xhtml'))
    return toc


def format_metadata_tags(metadata):
    """Format metadata as HTML with proper styling."""
    metadata_html = '<div class="metadata">\n'
    
    if metadata['date']:
        metadata_html += f'<p><strong>Date:</strong> {metadata["date"]}</p>\n'
    
    if metadata['authors']:
        metadata_html += f'<p><strong>Authors:</strong> <span class="authors">{", ".join(metadata["authors"])}</span></p>\n'
    
    if metadata['tags']:
        metadata_html += '<p><strong>Tags:</strong> <span class="tags">'
        for tag in metadata['tags']:
            if tag == "Paper":
                continue
            metadata_html += f' <span class="tag"> {tag}</span>'
        metadata_html += '</span></p>\n'
    
    metadata_html += '</div>\n'
    return metadata_html


def markdown_to_epub(full_text_path, summary_path, output_path=None, title=None, author='AI Assistant'):
    """Convert markdown files to EPUB."""
    base_dir = os.path.dirname(os.path.abspath(full_text_path))
    print(base_dir)
    
    full_text = read_markdown_file(full_text_path)
    summary = read_markdown_file(summary_path)
    
    summary_metadata = extract_metadata(summary)
    full_text_headings = extract_headings(full_text)
    summary_headings = extract_headings(summary)
    
    summary = re.sub(r'^---[\s\S]*?---', '', summary).strip()
    if title is None:
        title = extract_title_from_content(full_text)
        if title is None:
            title = os.path.basename(full_text_path).split('.')[0]
    
    if summary_metadata['authors']:
        author = ', '.join(summary_metadata['authors'])
    
    if output_path is None:
        base_name = os.path.basename(full_text_path).split('.')[0]
        output_path = os.path.join(os.path.dirname(full_text_path), f"{base_name}.epub")
    
    full_text, full_text_images = process_markdown_for_epub(full_text, base_dir)
    summary, summary_images = process_markdown_for_epub(summary, base_dir)
    
    additional_images = find_images_in_directory(base_dir)
    
    all_image_paths = set()
    image_references = []
    
    for image in full_text_images + summary_images:
        if image.get('is_svg_formula'):
            key = image['content']
        else:
            key = image['path']
            
        if key not in all_image_paths:
            all_image_paths.add(key)
            image_references.append(image)
            print(f"Added {'formula' if image.get('is_svg_formula') else 'image'}: {image['filename']}")
    
    for image_path in additional_images:
        if image_path not in all_image_paths:
            image_filename = os.path.basename(image_path)
            epub_path = f'images/{image_filename}'
            image_references.append({
                'path': image_path,
                'epub_path': epub_path,
                'filename': image_filename
            })
            all_image_paths.add(image_path)
    
    print(f"Total images and formulas: {len(image_references)}")
    
    book = epub.EpubBook()
    
    book.set_identifier(f'id-{datetime.now().strftime("%Y%m%d%H%M%S")}')
    book.set_title(title)
    book.set_language('en')
    book.add_author(author)
    print("Title of the book:", book.title)
    print("Book author:", author)
    
    
    def markdown_with_heading_ids(content, headings):
        for heading in headings:
            pattern = f"^{'#' * heading['level']} {re.escape(heading['title'])}$"
            replacement = f"\\g<0> {{: #{heading['id']}}}"
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        html = markdown.markdown(content, extensions=['tables', 'fenced_code', 'extra', 'codehilite', 'attr_list'])
        return html
    
    summary_html = markdown_with_heading_ids(summary, summary_headings)
    full_text_html = markdown_with_heading_ids(full_text, full_text_headings)
    
    metadata_html = format_metadata_tags(summary_metadata)
    
    summary_content = f'''<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>Summary</title>
    <link rel="stylesheet" type="text/css" href="style/style.css" />
</head>
<body>
    <h1>Summary</h1>
    {metadata_html}
    {summary_html}
</body>
</html>'''

    summary_chapter = epub.EpubHtml(
        title='Summary',
        file_name='summary.xhtml'
    )
    summary_chapter.set_content(summary_content)
    
    full_content = f'''<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>Full Content</title>
    <link rel="stylesheet" type="text/css" href="style/style.css" />
</head>
<body>
    <h1>Full Paper</h1>
    {full_text_html}
</body>
</html>'''
    
    content_chapter = epub.EpubHtml(
        title='Full Content',
        file_name='content.xhtml'
    )
    content_chapter.set_content(full_content)
    
    book.add_item(summary_chapter)
    book.add_item(content_chapter)
    
    for img in image_references:
        try:
            if img.get('is_svg_formula'):
                image_content = img['content']
                if isinstance(image_content, str):
                    image_content = image_content.encode('utf-8')
                media_type = 'image/svg+xml'
            else:
                with open(img['path'], 'rb') as img_file:
                    image_content = img_file.read()
                media_type = mimetypes.guess_type(img['path'])[0]
                if media_type is None:
                    media_type = 'image/jpeg'
            
            img_id = hashlib.md5(img['epub_path'].encode()).hexdigest()[:8]
            
            image_item = epub.EpubItem(
                uid=f"image_{img_id}",
                file_name=img['epub_path'],
                media_type=media_type,
                content=image_content
            )
            
            book.add_item(image_item)
            print(f"Added {'formula' if img.get('is_svg_formula') else 'image'}: {img['filename']} ({media_type})")
            
        except Exception as e:
            print(f"Warning: Error adding image {img.get('path', img.get('filename', 'unknown'))}: {e}")
            import traceback
            traceback.print_exc()
    
    nav_content = '''<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>Navigation</title>
</head>
<body>
    <nav epub:type="toc" id="toc">
        <h1>Table of Contents</h1>
        <ol>
            <li>
                <a href="summary.xhtml">Summary</a>
                <ol>'''
    
    for heading in summary_headings:
        indent = '    ' * heading['level']
        nav_content += f'\n{indent}<li><a href="summary.xhtml#{heading["id"]}">{heading["title"]}</a></li>'
    
    nav_content += '''
                </ol>
            </li>
            <li>
                <a href="content.xhtml">Full Content</a>
                <ol>'''
    
    for heading in full_text_headings:
        indent = '    ' * heading['level']
        nav_content += f'\n{indent}<li><a href="content.xhtml#{heading["id"]}">{heading["title"]}</a></li>'
    
    nav_content += '''
                </ol>
            </li>
        </ol>
    </nav>
</body>
</html>'''
    
    nav = epub.EpubNav()
    nav.file_name = 'nav.xhtml'
    nav.set_content(nav_content)
    
    ncx = epub.EpubNcx()
    
    book.add_item(nav)
    book.add_item(ncx)
    
    book.spine = ['nav', summary_chapter, content_chapter]
    
    book.guide = [
        {'type': 'toc', 'title': 'Table of Contents', 'href': 'nav.xhtml'},
        {'type': 'text', 'title': 'Summary', 'href': 'summary.xhtml'},
        {'type': 'text', 'title': 'Content', 'href': 'content.xhtml'}
    ]
    
    try:
        print("\nFinal book structure:")
        print(f"Spine items ({len(book.spine)}):", [item.file_name if hasattr(item, 'file_name') else item for item in book.spine])
        print(f"Book items ({len(book.items)}):", [item.file_name for item in book.get_items()])
        print(f"TOC items ({len(book.toc)}):", [item.title if hasattr(item, 'title') else item for item in book.toc])
        
        for item in book.get_items():
            if isinstance(item, epub.EpubHtml):
                content_length = len(item.get_content()) if item.get_content() else 0
                if content_length < 10:
                    print(f"WARNING: {item.file_name} appears to have little or no content!")
                else:
                    print(f"Content length for {item.file_name}: {content_length} bytes")
        
        epub.write_epub(output_path, book)
        
        print(f"EPUB successfully created at: {output_path}")
        return True
    except Exception as e:
        print(f"\nError creating EPUB: {e}")
        if hasattr(e, '__traceback__'):
            import traceback
            traceback.print_tb(e.__traceback__)
        return False



def main():
    """Main entry point."""
    args = parse_arguments()
    
    if not os.path.exists(args.full_text):
        print(f"Error: Full text file not found: {args.full_text}")
        sys.exit(1)
    
    if not os.path.exists(args.summary):
        print(f"Error: Summary file not found: {args.summary}")
        sys.exit(1)
    
    success = markdown_to_epub(
        args.full_text,
        args.summary,
        args.output,
        args.title,
        args.author
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
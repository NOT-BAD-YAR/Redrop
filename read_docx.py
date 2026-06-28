import zipfile
import xml.etree.ElementTree as ET

def read_docx(path):
    with zipfile.ZipFile(path) as docx:
        tree = ET.parse(docx.open('word/document.xml'))
        root = tree.getroot()
        text = []
        for p in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            texts = [node.text for node in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
            if texts:
                text.append(''.join(texts))
        return '\n'.join(text)

with open('output_spec.txt', 'w', encoding='utf-8') as f:
    f.write("=== SUBMISSION SPEC ===\n")
    f.write(read_docx("submission_spec.docx"))


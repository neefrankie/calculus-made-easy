# Convert units
import re
from typing import List
from uuid import uuid4


inch_pat = re.compile(r'\binch\b')
inches_pat = re.compile(r'\binches\b')
short_inch_pat = re.compile(r"\bin\.")
foot_pat = re.compile(r'(?<=\$\s)\bfoot\b')
feet_pat = re.compile(r'\bfeet\b')
short_ft_pat = re.compile(r'\bft\.(?=\s)')

def convert_units_en(text: str):
    text = inch_pat.sub(r'centimetre', text)
    text = inches_pat.sub(r'centimetres', text)
    text = short_inch_pat.sub(r'cm', text)
    text = foot_pat.sub(r'metre', text)
    text = feet_pat.sub(r'metres', text)
    text = short_ft_pat.sub(r'metres', text)
    return text

# Markdownify escaped _ in latex, which should not be performed.
sub_pat = re.compile(r"\\_")


def fix_tex_subscript(latex: str) -> str:
    return sub_pat.sub("_", latex)

PAT_NEWLINE = re.compile(r"\n+")
def replace_newline_with_space(text: str) -> str:
    """
    Replace any number of newlines inside a paragraph to a space.
    """
    return PAT_NEWLINE.sub(" ", text)


def clean_tex_paragraph(text: str, sentences: List[str]):
    """
    Remove newlines inside \text{...} extracted from block-level math,
    and then use those newline-free sentences to replace its
    old correspondence in the original paragraph.
    """
    new_sentences = [replace_newline_with_space(s) for s in sentences]
    for (old, new) in zip(sentences, new_sentences, ):
        text.replace(old, new)

    return text, new_sentences

multi_newline_pat = re.compile(r'\n{2,}')

def ensure_single_newlline(text: str) -> str:
    return multi_newline_pat.sub('\n', text)

def ensure_double_newline(text: str) -> str:
    return multi_newline_pat.sub('\n\n', text)

# [^\sA-Za-z£\)\}\d"，；、。;,]\$
dollar_start_pat = re.compile(r'([\u4e00-\u9fff])\$')
dollar_end_pat = re.compile(r'\$([\u4e00-\u9fff])')

def pad_inline_math(text: str):
    text = dollar_start_pat.sub(r'\1 $', text)
    text = dollar_end_pat.sub(r'$ \1', text)
    return text

# ([Figure 4](#figure4))
# [图4](#figure4)）
# but not （详见[此处](../3#function)）
inpage_link_pat = re.compile(r'\[([^\]]+)\]\(#[^)\s]+\)')

def remove_inpage_link(text: str):
    text = inpage_link_pat.sub(r'\1', text)
    return text

roman_num_pat = re.compile(r'^\w*\.\s')
def transform_key(text: str) -> str:
    """
    Convert a string to a key that can be used in a dictionary.
    """
    text = roman_num_pat.sub('', text)
    text = text.strip()
    
    return text.lower()


math_block_pat = re.compile(r'<p\sclass=\"latex-block\">')

def add_math_id(text: str) -> str:
    """
    Add a unique id to each math block.
    """
    text = math_block_pat.sub(f'<p id="{uuid4()}" class="latex-block">', text)
    return text
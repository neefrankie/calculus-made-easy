import re
from uuid import uuid4


from .pattern import convert_units_en



def remove_br_in_h1(text: str):
    return text.replace('<h1><br>', '<h1>')

# Find <p>. Add </p> before it.
# Exceptions:
# <br><hr><p> becomes <br><hr></p><p>
PAT_STARTING_P = re.compile(r'(.)(\n*)(?=<p>)')
# Find <table>. Add </p> before it
PAT_STARTING_TABLE = re.compile(r'(.)(\n*)(?=<table>)')
# Add <p> before <blockquote>:
# <p>The witty Dean Swift*
# once wrote:
# <blockquote><pre>
PAT_START_BLOCKQUOTE = re.compile(r'(.)(\n*)(?=<blockquote>)')
# Add </p> before:
# <br>
# <hr>
# This usually occurs at the end of article.
PAT_BR_HR_P = re.compile(r'(\n+<br>\n*<hr>)')

# Add </p> befoe a single <hr>
PAT_HR_P = re.compile(r'(?<!<br>\n)(<hr>)')

def close_p(text: str) -> str:
    text = PAT_STARTING_P.sub(r'\1</p>\n\2', text)
    # Fix extra ending p added by previous step
    text = text.replace('<hr></p>', '<hr>')

    text = PAT_STARTING_TABLE.sub(r'\1</p>\2\n', text)
    text = PAT_START_BLOCKQUOTE.sub(r'\1</p>\2\n', text)
    
    text = PAT_BR_HR_P.sub(r'</p>\1', text)
    text = PAT_HR_P.sub(r'</p>\n\1', text)

    return text


# Find a surroung img tag without closing. 
# Example:
# <p><a name="figure1">
# <img src="33283-t/images/018a.pdf.png-1.png">
# 
# <p>
# Perform this after ending p is fixed.
img_in_a_pat = re.compile(r'<a \w+=\".+?\">\n*(<img \w+=\".+?\">)(\n*)(?=<\/p>)')
def remove_a_around_img(text: str) -> str:
    """
    Add missing </a> between <img/> and any number of following newlines, 
    without touching anything else.
    Newlines are left to the follwoing patterns to handle.
    """
    return img_in_a_pat.sub(r"\1\2", text)

# In 14.html, there are patterns like:
# <a name="figure39">
# <p><img src="33283-t/images/158a.pdf.png-1.png">
# After replacement, it should be in the form of PAT_UNCLOSED_A
PAT_ORPHAN_A = re.compile(r'(<a \w+=\".+?\">)\n?(<p>)(<img)')
def swap_orphan_a(text: str) -> str:
    return PAT_ORPHAN_A.sub(r'\2\n\1\3', text)

# Handle self-closed a like:
# <a id="fn1"/>
PAT_SELF_CLOSED_A = re.compile(r'(<a \w+=\".+?\")\/(>)')
def normalize_self_closed_a(text: str) -> str:
    """
    Change self-closed <a/> to <a></a>
    """
    return PAT_SELF_CLOSED_A.sub(r"\1\2</a>", text)


# \begin{gather*}
PAT_TEX_BEGIN = re.compile(r'(\n*)(\\begin\{\w+\*\})')
def modify_tex_begin(m: re.Match[str]) -> str:
    text = f'''</p>{m.group(1)}
<p id="{uuid4()}" class="latex-block">{m.group(2)}'''
    return text

# Find latex end tag without trailing </p>
# \end{align*}
# \end{gather*}
PAT_TEX_END = re.compile(r'(\\end\{\w+\*\})')

# Match block text: \[ ... \]
PAT_BLOCK_TEX_START = re.compile(r'(\\\[)')
def modify_square_math(m: re.Match[str]) -> str:
    text = f'</p>\n\n<p id="{uuid4()}" class="latex-block">{m.group(1)}'
    return text

PAT_BLOCK_TEX_END = re.compile(r'(\\\])(?!</p>)')
# Inline lattex forumuas in its own paragraph:
# <p>$dy = du+dv, $</p>
PAT_INLINE_TEX_PARA = re.compile(r'<p>\$([^$]+)\$</p>')
def modify_dollar_block_match(m: re.Match[str]) -> str:
    text = f'<p id="{uuid4()}" class="latex-block">\[\n{m.group(1)}\n\]</p>'
    return text
def wrap_tex_in_block(text: str) -> str:
    """
    Wrap block latex into a paragraph. 
    """
    text = PAT_TEX_BEGIN.sub(modify_tex_begin, text)
    # If the pattern is followed by a heading tag,
    # this operation will add redundant starting p tag.
    text = PAT_TEX_END.sub(r"\1</p>\n\n<p>", text)

    text = PAT_BLOCK_TEX_START.sub(modify_square_math, text)
    text = PAT_BLOCK_TEX_END.sub(r"\1</p>\n\n<p>", text)

    text = PAT_INLINE_TEX_PARA.sub(modify_dollar_block_match, text)
    return text

# Clean up various p tag:

# Remove space after starting p
PAT_SPACE_AFTER_P = re.compile(r'(<p>)[\n\s]+')
PAT_SPACE_BEFORE_P = re.compile(r'[\n\s]+(<\/p>)')

# Swap <hr></p>
# Seen in 2.html due to note section:
# <br>
# <hr></p>
# PAT_HR_IN_P = re.compile(r'(<hr>)(<\/p>)')

# Find a line ending with </p> but not starting <p>
PAT_LINE_WITHOUT_START_P = re.compile(r'(^\w.*?)(?=<\/p>)')

PAT_BREAK_P = re.compile(r'(<\/p>)(<p>)')

# <p><a name="ex1"></a>
# <hr><h3>Exercises I</h3></p>
# <h3 class="answers">Answers</h3></p>
PAT_P_AFTER_HEADER = re.compile(r'(<h\d[^>]*>[^<]+<\/h\d>)(<\/p>)')

# Find ending </hn> immdediately followed by plain text.
# Seen in 4.html:
# <p><h3>Case 1</h3>
# Let us begin with the simple expression $y=x^2$.
# <p>
# <h3>Case 2</h3>
# Happens in two case:
# * Original text wrapped heading in p
# * Added when wrapping latex block into p
PAT_P_BEFORE_HEADER = re.compile(r'(<p>)(\n*<h\d>.+<\/h\d>)')

def clear_p(text: str):
    # Remove heart symbol
    text = text.replace('<p class="a rotatedFloralHeartBullet"></p>', '\n')
    # Move <p> before heading tag to end
    text = PAT_P_BEFORE_HEADER.sub(r"\2\n\1", text)
    # Move </p> after heading to begging.
    text = PAT_P_AFTER_HEADER.sub(r'\2\n\n\1', text)

    # Move <hr> out of p
    # text = PAT_HR_IN_P.sub(r'\2\n\n\1', text)

    # Add p to start of line
    text = PAT_LINE_WITHOUT_START_P.sub(r'<p>\1', text)

    text = PAT_SPACE_BEFORE_P.sub(r'\1', text)
    text = PAT_SPACE_AFTER_P.sub(r'\1', text)

    text = PAT_BREAK_P.sub(r'\1\n\n\2', text)

    text = text.replace('<p></p>', '')
    text = text.replace('<p><hr></p>', '<hr>')
    text = text.replace('<hr></p>', '<hr>')
    text = text.replace('</table></p>', '</table>')
    text = text.replace('</blockquote></p>', '</blockquote>')
    
    return text


PAT_EXERCISE_START = re.compile(r'(<h3>Exercises[\w\s]*</h3>)')
PAT_EXERCISE_END = re.compile(r'(\n+<br>\n*<hr>\n*<a href=\"\d+\.html\">)')
def wrap_exercise(text: str):
    if not PAT_EXERCISE_START.search(text):
        return text
    text = PAT_EXERCISE_START.sub(r'\n\n<div class="exercises-section">\n\1', text)
    text = PAT_EXERCISE_END.sub(r'\n</div>\n\1', text)

    return text


# The end of title tag. It might be followed by  a <p> or <h2> tag.
PAT_H1_END = re.compile(r'(?<=<\/h1>)(\n*)(?=<\w)')
PAT_BR_HR_END = re.compile(r'(<br>)?(\n*<hr>)(\n*<a href=)')
def wrap_main(text: str) -> str:
    text = PAT_H1_END.sub(r'\1<main id="main-content">\n\n', text, count=1)
    text = PAT_BR_HR_END.sub(r'\1\2\n</main>\n\3', text, count=1)
    return text


PAT_H1_START = re.compile(r'(?<=<\/script>)(\n*)(?=<h1>)')
def wrap_body(text: str) -> str:
    text = PAT_H1_START.sub(r'\1<body>\n', text, count=1)
    text += '\n</body>'
    return text

def replace_mathjax(text: str) -> str:
    text = text.replace(
        'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-AMS-MML_HTMLorMML', 
        'https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js')
    text = text.replace(
        r"  MathJax.Hub.Config({tex2jax: {inlineMath: [['$','$'], ['\\(','\\)']]}});",
        r"""MathJax = {
  tex: {
    inlineMath: [['$','$'], ['\\(','\\)']],
    displayMath: [['\\[', '\\]'], ['$$', '$$']],
  }
};"""
    )
    text = text.replace(' type="text/x-mathjax-config"', '')
    return text

inpage_link_pat = re.compile(r'<a\s+href=\"#[^\s>]+?\">([^<]+)</a>')
def remove_inpage_link(text: str):
    text = inpage_link_pat.sub(r'\1', text)
    return text

def fix_html(text: str) -> str:
    """
    Fix html text in a plain text.
    """
    text = swap_orphan_a(text)
    text = remove_br_in_h1(text)
    text = close_p(text)

    text = remove_a_around_img(text)
    text = normalize_self_closed_a(text)
    
    text = wrap_tex_in_block(text)

    text = clear_p(text)

    text = wrap_exercise(text)

    text = wrap_main(text)
    text = wrap_body(text)

    text = replace_mathjax(text)

    text = remove_inpage_link(text)

    return text

PAT_CHAPTER5_1 = re.compile(r'(<p>Differentiate the following:)[\n\s]*\[2\]')
CHAPTER5_EXC_1 = '(1) $y = ax^3 + 6$.'
CHAPTER5_EXC_3 = '(3) $y = 12x^{\frac{1}{2}} + c^{\frac{1}{2}}$.'
def modify_chapter5(text: str) -> str:
    text = PAT_CHAPTER5_1.sub(r'\1</p>\n', text)
    text = text.replace(CHAPTER5_EXC_1, '<p>' + CHAPTER5_EXC_1 + '</p>\n<p>')
    text = text.replace(CHAPTER5_EXC_3, '<p>' + CHAPTER5_EXC_3 + '</p>\n<p>')

    return text

def modify_chapter2(text: str) -> str:
    text = text.replace('farthing', 'penny')
    text = text.replace('sovereign', 'pound')
    text = text.replace(' (or one billionth<sup><a href="#fn1">†</a></sup>)', '')
    text = text.replace(r"""<p>The witty Dean Swift*
once wrote:</p>

<blockquote><pre>
So, Nat'ralists observe, a Flea
Hath smaller Fleas that on him prey.
And these have smaller Fleas to bite 'em,
And so proceed ad infinitum." </pre>
</blockquote>
<p><note><em>*On Poetry: a Rhapsody</em> (p. 20), printed 1733–usually misquoted.</note></p>""", "")
    text = text.replace(r"""<p><a id="fn1"></a><note><sup>†</sup>The term <em>billion</em> here means $10^{12}$ in old British
English, ie, trillion in <a href="https://en.wikipedia.org/wiki/Long_and_short_scales">modern use</a>.</note></p>
<hr>""", "")
    return text


def modify_chapter3(text: str) -> str:
    text = text.replace("$15$ feet", "$1.8$ metre")
    text = text.replace(' (see <a href="3.html#function">here</a>)', '')
    text = text.replace('<a name="function"></a>', '')
    return text

def inline_math_to_block(text: str) -> str:
    old = text
    text = text.strip('$')
    text = f'</p>\n<p>\n\[\n{text}\n\]</p>\n<p>'
    text = text.replace(old, text)
    return text


table_header_pat = re.compile(r'<center>([^<]*)</center>')
def fix_final_table(text: str) -> str:
    text = table_header_pat.sub(r'\1', text)
    return text

chapter_fixer = {
    "2": modify_chapter2,
    "5": modify_chapter5,
    "3": modify_chapter3,
    "table": fix_final_table,
}

def fix(html: str, slug: str):
    html = fix_html(html)

    if slug in chapter_fixer:
        html = chapter_fixer[slug](html)

    html = convert_units_en(html)

    return html





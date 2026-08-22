# -*- coding: utf-8 -*-
"""아주 작은 DOM. 표준 라이브러리 html.parser 만 쓴다.

이 저장소의 HTML은 기계가 찍어낸 것이라 정규식으로도 되지만,
변환 결과가 원본과 같은지 증명해야 하므로 제대로 파싱한다.
"""

from html.parser import HTMLParser

VOID = {"br", "img", "meta", "link", "hr", "input"}


class Node(object):
    def __init__(self, tag, attrs=None):
        self.tag = tag
        self.attrs = dict(attrs or {})
        self.kids = []
        self.parent = None

    # -- 탐색 -------------------------------------------------------------

    def cls(self):
        return (self.attrs.get("class") or "").split()

    def has(self, name):
        return name in self.cls()

    def find_all(self, tag=None, cls=None):
        out = []
        for k in self.kids:
            if isinstance(k, Node):
                if (tag is None or k.tag == tag) and (cls is None or k.has(cls)):
                    out.append(k)
                out.extend(k.find_all(tag, cls))
        return out

    def first(self, tag=None, cls=None):
        got = self.find_all(tag, cls)
        return got[0] if got else None

    def children(self, tag=None, cls=None):
        return [k for k in self.kids
                if isinstance(k, Node)
                and (tag is None or k.tag == tag)
                and (cls is None or k.has(cls))]

    # -- 내용 -------------------------------------------------------------

    def text(self):
        """자식까지 훑어 눈에 보이는 글자만. <br> 은 줄바꿈으로."""
        out = []
        for k in self.kids:
            if isinstance(k, Node):
                if k.tag == "br":
                    out.append("\n")
                else:
                    out.append(k.text())
            else:
                out.append(k)
        return "".join(out)

    def marked(self, em_class="em"):
        """<span class='em'>강조</span> 를 **강조** 로 바꿔서 돌려준다."""
        out = []
        for k in self.kids:
            if isinstance(k, Node):
                if k.tag == "br":
                    out.append("\n")
                elif k.tag == "span" and k.has(em_class):
                    out.append("**%s**" % k.marked(em_class).strip())
                else:
                    out.append(k.marked(em_class))
            else:
                out.append(k)
        return "".join(out)

    def __repr__(self):
        return "<%s %s>" % (self.tag, self.attrs.get("class", ""))


class _Builder(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.root = Node("#root")
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs)
        n.parent = self.cur
        self.cur.kids.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        n = Node(tag, attrs)
        n.parent = self.cur
        self.cur.kids.append(n)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        node = self.cur
        while node is not self.root and node.tag != tag:
            node = node.parent
        if node is not self.root:
            self.cur = node.parent

    def handle_data(self, data):
        self.cur.kids.append(data)


def parse(html_text):
    b = _Builder()
    b.feed(html_text)
    b.close()
    return b.root


def squash(s):
    """공백을 하나로 줄이고 앞뒤를 자른다. 대조할 때 쓴다."""
    return " ".join((s or "").split())

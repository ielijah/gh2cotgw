"""Cyrillic pairs plus explicitly enabled native decimal placeholders."""
import re

DECIMAL = re.compile(r'%[0-9]*d')
NATIVE = '0123456789/ ?,CIVX-!.:;()'

def decimal_tokens(text):
    tokens=DECIMAL.findall(text)
    assert '%' not in DECIMAL.sub('',text), 'Unsupported format directive'
    return tokens

def pieces(text, formatted=False):
    if not formatted:
        assert '%' not in text
    else:
        decimal_tokens(text)
    lines=text.split('\n')
    for lineno,line in enumerate(lines):
        if lineno: yield 'raw', b'\n'
        chunks=re.split(r'(%[0-9]*d)',line) if formatted else [line]
        for index,chunk in enumerate(chunks):
            if not chunk: continue
            if formatted and DECIMAL.fullmatch(chunk):
                yield 'raw',chunk.encode('ascii')
                continue
            tail=''
            if len(chunk)%2:
                if formatted and chunk[-1] in NATIVE:
                    chunk,tail=chunk[:-1],chunk[-1]
                else:
                    assert not formatted or index==len(chunks)-1, 'Padding before a substitution would insert a space'
                    chunk+=' '
            for n in range(0,len(chunk),2):
                pair=chunk[n:n+2]
                yield ('raw',pair.encode('ascii')) if all(c in NATIVE for c in pair) else ('pair',pair)
            if tail: yield 'raw',tail.encode('ascii')

def encode(text,pairs,formatted=False):
    return b''.join(value if kind=='raw' else pairs[value]
                    for kind,value in pieces(text,formatted))


STREAM_TOKEN = re.compile(r'(\x1b[CB][0-9A-F]|%[-]?[0-9]*[ds])')
def stream_tokens(text):
    tokens=STREAM_TOKEN.findall(text)
    stripped=STREAM_TOKEN.sub('',text)
    assert '%' not in stripped and '\x1b' not in stripped, 'Unsupported stream directive'
    return tokens

def stream_pieces(text):
    stream_tokens(text)
    for lineno,line in enumerate(text.split('\n')):
        if lineno: yield 'raw',b'\n'
        chunks=STREAM_TOKEN.split(line)
        for index,chunk in enumerate(chunks):
            if not chunk:continue
            if STREAM_TOKEN.fullmatch(chunk):yield 'raw',chunk.encode('ascii');continue
            tail=''
            if len(chunk)%2:
                if chunk[-1] in NATIVE:chunk,tail=chunk[:-1],chunk[-1]
                else:
                    assert index==len(chunks)-1,'Padding before control or substitution'
                    chunk+=' '
            for n in range(0,len(chunk),2):
                pair=chunk[n:n+2]
                yield ('raw',pair.encode('ascii')) if all(c in NATIVE for c in pair) else ('pair',pair)
            if tail:yield 'raw',tail.encode('ascii')

def encode_stream(text,pairs):
    return b''.join(value if kind=='raw' else pairs[value] for kind,value in stream_pieces(text))

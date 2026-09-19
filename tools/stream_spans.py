"""Lossless text-stream and editorial-span utilities for layout-poor PDFs."""
import hashlib, json

def stream_fingerprint(text): return hashlib.sha256(text.encode('utf-8')).hexdigest()
def build_stream(lines, ignored):
    kept=[line.strip() for line in lines if line.strip() and line.strip() not in set(ignored)]
    return ' '.join(kept)
def validate_spans(stream, fingerprint, spans):
    errors=[]
    if stream_fingerprint(stream)!=fingerprint: errors.append('stream fingerprint mismatch')
    cursor=0; ids=set()
    for span in spans:
        start,end=span.get('start'),span.get('end')
        if not span.get('id') or span.get('id') in ids: errors.append('duplicate/empty span id: '+str(span.get('id')))
        ids.add(span.get('id'))
        if not isinstance(start,int) or not isinstance(end,int) or start<0 or end<=start or end>len(stream): errors.append('invalid span bounds: '+str(span.get('id'))); continue
        if start!=cursor: errors.append(('gap' if start>cursor else 'overlap')+' before: '+str(span.get('id')))
        cursor=end
    if cursor!=len(stream): errors.append('uncovered stream suffix')
    return errors

def virtual_blocks(stream, source_alias, language, spans):
    return [{'source_id':span['id'],'source_alias':source_alias,'stream_sha256':stream_fingerprint(stream),'start':span['start'],'end':span['end'],'text':stream[span['start']:span['end']],'source_language':language,'status':span.get('status','reviewed')} for span in spans]

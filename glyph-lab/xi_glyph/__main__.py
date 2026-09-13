import argparse,json,sys
from pathlib import Path
from .tessera import encode_v4,decode_v4
from .tessera_grammar import describe,RULES

def main():
    p=argparse.ArgumentParser(description='Execute the Xi Tessera grammar locally')
    p.add_argument('command',choices=['grammar','run','decode'])
    p.add_argument('file',nargs='?',help='UTF-8 program JSON, or hex packet for decode')
    a=p.parse_args()
    if a.command=='grammar':result={**describe(),'rules':[r.export() for r in RULES]}
    else:
        if not a.file:p.error('This command requires a file')
        text=Path(a.file).read_text(encoding='utf-8')
        if a.command=='decode':packet=bytes.fromhex(text.strip())
        else:
            program=json.loads(text);source=program.get('source');path=program.get('path')
            if not isinstance(source,list) or not source or not all(isinstance(x,str) and x for x in source):p.error('source must be a nonempty array of glyph atoms')
            if not isinstance(path,list) or not path or any(x not in describe()['states'] for x in path):p.error('path must name one or more S0–S16 states')
            packet=encode_v4(source,path)
        result={'bytes':len(packet),'payload_hex':packet.hex(),'decoded':decode_v4(packet)}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    main()

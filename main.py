import json,os,sys,urllib.request,urllib.error
ENV=os.environ.get("MAKEFUN_ENV_URL") or sys.exit("no env")
VAL={"p":1,"n":3,"b":3,"r":5,"q":9,"k":0}
def post(p,b):
    r=urllib.request.Request(ENV+p,data=json.dumps(b).encode(),headers={"content-type":"application/json"})
    try:
        with urllib.request.urlopen(r) as x: return json.load(x)
    except urllib.error.HTTPError as e: sys.exit(f"{p}:{e.code}")
def board(fen):
    b={}
    for i,r in enumerate(fen.split()[0].split("/")):
        f=0
        for c in r:
            if c.isdigit(): f+=int(c)
            else: b["abcdefgh"[f]+str(8-i)]=c; f+=1
    return b
def apply_move(fen,mv):
    parts=fen.split(); b=board(fen); col=parts[1]; cast=parts[2]; ep=parts[3]; hm=int(parts[4]); fm=int(parts[5])
    src=mv[:2]; dst=mv[2:4]; promo=mv[4] if len(mv)>4 else None
    piece=b.pop(src); victim=b.get(dst)
    # en passant
    if piece.lower()=="p" and src[0]!=dst[0] and victim is None:
        b.pop(dst[0]+src[1],None)
    # castling
    if piece.lower()=="k" and abs(ord(src[0])-ord(dst[0]))==2:
        if dst[0]=="g":
            rook=b.pop("h"+src[1]); b["f"+src[1]]=rook
        else:
            rook=b.pop("a"+src[1]); b["d"+src[1]]=rook
    if promo: piece=promo.upper() if piece.isupper() else promo.lower()
    b[dst]=piece
    # castling rights
    cr=cast
    if piece.lower()=="k":
        cr=cr.replace("K","").replace("Q","") if piece.isupper() else cr.replace("k","").replace("q","")
    if src in ("a1","h1") or dst in ("a1","h1"):
        cr=cr.replace("Q","").replace("K","")
    if src in ("a8","h8") or dst in ("a8","h8"):
        cr=cr.replace("q","").replace("k","")
    if cr=="": cr="-"
    # ep square
    newep="-"
    if piece.lower()=="p" and abs(int(src[1])-int(dst[1]))==2:
        newep=src[0]+str((int(src[1])+int(dst[1]))//2)
    # halfmove
    newhm=0 if (piece.lower()=="p" or victim) else hm+1
    newfm=fm if col=="b" else fm+1
    # rebuild fen
    rows=[]
    for i in range(8):
        r=""; empty=0
        for j in range(8):
            sq="abcdefgh"[j]+str(8-i)
            if sq in b: 
                if empty: r+=str(empty); empty=0
                r+=b[sq]
            else: empty+=1
        if empty: r+=str(empty)
        rows.append(r)
    return " ".join(["/".join(rows), "b" if col=="w" else "w", cr, newep, str(newhm), str(newfm)])
def evalf(fen):
    b=board(fen); s=0
    for sq,p in b.items():
        v=VAL.get(p.lower(),0)
        s += v if p.isupper() else -v
        # mobility-ish: central bonus
        if sq in ("d4","e4","d5","e5"): s += 0.1 if p.isupper() else -0.1
    return s
def captures(fen):
    # generate capture moves (uci) from legal-ish: try all adjacent; instead rely on env? For search we approximate: return [] (fallback to 1-ply)
    return []
def choose(fen,legal):
    best=None; bs=-10**9
    for m in legal:
        nf=apply_move(fen,m)
        sc=-evalf(nf)
        if sc>bs: bs=sc; best=m
    return best
while True:
    g=post("/game",{})
    if g["status"]=="done": break
    while g["status"]=="your_move":
        g=post("/move",{"game":g["game"],"move":choose(g["fen"],g["legal_moves"])})
    print(f"game {g['game']}: {g['outcome']} by {g['reason']}",file=sys.stderr)
print(f"done: {g.get('wins')} won, {g.get('draws')} drawn, {g.get('losses')} lost",file=sys.stderr)

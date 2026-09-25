import math, struct, sys, wave, random
SR=44100; T=31.0; N=int(SR*T)
random.seed(3)
def note(n): return 440*2**((n-69)/12)
# Acordes: La menor add9 → Fa maj7 → Do add9 → Sol sus; resuelve en La menor.
chords=[(0,[57,64,69,71,76]),(8,[53,60,65,69,76]),(15,[48,55,64,67,74]),(21,[55,62,67,69,74]),(26,[57,64,69,72,76])]
def chord_at(t):
    c=chords[0][1]
    for s,n in chords:
        if t>=s: c=n
    return c
L=[0.0]*N; R=[0.0]*N
# Pad: senos con leve desafinado, volumen que crece hasta 24 s y se apaga al final.
for i in range(N):
    t=i/SR
    env=min(1,t/6)**1.5*(1 if t<27 else max(0,(T-t)/4))
    sw=0.55+0.45*min(1,max(0,(t-8)/14))
    c=chord_at(t)
    s=0.0
    for k,n in enumerate(c):
        f=note(n)
        s+=math.sin(2*math.pi*f*t)*0.6+math.sin(2*math.pi*f*1.003*t+k)*0.4
    s*=env*sw*0.035
    # Pulso grave suave cada segundo a partir de 8 s.
    if 8<=t<27:
        ph=(t-8)%1.0
        s+=math.sin(2*math.pi*48*ph)*math.exp(-ph*9)*0.22*min(1,(t-8)/3)
    L[i]+=s; R[i]+=s
# Golpe grave en la revelación (7,2 s) y en el cierre (26 s).
for hit in (7.2,26.0):
    for j in range(int(SR*2.5)):
        i=int(hit*SR)+j
        if i>=N: break
        tt=j/SR; f=38+30*math.exp(-tt*6)
        v=math.sin(2*math.pi*f*tt)*math.exp(-tt*1.8)*0.5
        L[i]+=v; R[i]+=v
# Destellos agudos (notas del acorde, una octava arriba) como campanitas.
for k in range(34):
    t0=random.uniform(9,26); n=random.choice(chord_at(t0))+24
    f=note(n); pan=random.random()
    for j in range(int(SR*1.6)):
        i=int(t0*SR)+j
        if i>=N: break
        tt=j/SR; v=math.sin(2*math.pi*f*tt)*math.exp(-tt*3.2)*0.05
        L[i]+=v*(1-pan); R[i]+=v*pan
m=max(max(abs(x) for x in L),max(abs(x) for x in R))
w=wave.open(sys.argv[1] if len(sys.argv) > 1 else "musica.wav","wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(b"".join(struct.pack("<hh",int(L[i]/m*0.85*32767),int(R[i]/m*0.85*32767)) for i in range(N)))
w.close()

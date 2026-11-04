import sys, json
r = json.load(open(sys.argv[1], encoding='utf-8'))[sys.argv[2]]['candidatas']
for c in r:
    if c['apta'] or set(c['pads']) & {'BT2_1', 'BT2_2', 'BT1_1', 'BT1_2'}:
        print(c['apta'], c['cara'], c['longitud_mm'], c['anchos_mm'], c['pads'], c['nets'], 'segs', c['segmentos'], 'gap', c['gap_coplanar_mm'], c['coplanar_es_masa'], c['motivos'])

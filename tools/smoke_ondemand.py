"""Isolated fresh-config smoke test; never replaces production Sonos scripts.

Start the supplied HA blueprint on the given root/player before running.
Only refresh commands are sent; this test never starts music or changes volume.
"""
from __future__ import annotations
import argparse, json, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(base, topic_root, player, device_root):
    base = base.rstrip('/') + '/api/v1/'
    def request(method, path, data=None):
        raw = data.encode() if isinstance(data,str) else json.dumps(data).encode() if data is not None else None
        req = urllib.request.Request(base+path, data=raw, method=method,
              headers={'Content-Type': 'text/plain' if isinstance(data,str) else 'application/json'})
        with urllib.request.urlopen(req,timeout=15) as response:
            return json.load(response)
    module_name='sonos_clean_test_names'
    app_name='sonos_clean_test'
    existing={a['name'] for a in request('GET','apps')}
    if {module_name,app_name} & existing:
        raise RuntimeError('Test names already exist; refusing to replace them')
    module=(ROOT/'apps/sonos_artist_names.ax').read_text().replace('sonos_artist_names',module_name)
    app=(ROOT/'apps/sonos_remote.ax').read_text().replace('sonos_artist_names',module_name)
    app=app.replace('    self.last_state = now_ms()', '    shared.set("rx", now_ms())\n    if topic == self.root + "/state/title" shared.set("title", payload) end\n    if topic == self.root + "/state/volume" shared.set("volume", payload) end\n    self.last_state = now_ms()')
    installed=[]
    report={'firmware':request('GET','device')['version'],'checks':[]}
    def check(condition,label):
        if not condition: raise AssertionError(label)
        report['checks'].append(label)
    try:
        for name,source in [(module_name,module),(app_name,app)]:
            installed.append(name)
            result=request('PUT','apps/script/'+name,source)
            check(result.get('error') is None,'compile '+name)
        fields=request('GET','apps/'+app_name+'/config')
        # Config endpoint returns {fields:[...]} on the official beta.
        fields=fields.get('fields',[]) if isinstance(fields,dict) else fields
        neutral={f['key']:f.get('value',f.get('default')) for f in fields}
        check(not neutral.get('player') and not neutral.get('device_root'), 'neutral entity and clock defaults')
        check(all(not neutral.get('playlist'+str(n)) for n in range(1,5)), 'empty playlist defaults')
        request('PATCH','apps/'+app_name+'/config',{'root':topic_root,'player':player,'device_root':device_root,'icon_name':''})
        row=next(a for a in request('GET','apps') if a['name']==app_name)
        check(row.get('ondemand') is True,'official on-demand registration')
        request('PUT','apps/active',{'name':app_name,'fast':True})
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            row=next(a for a in request('GET','apps') if a['name']==app_name)
            if row.get('error'): raise AssertionError(row['error'])
            frame=request('GET','display/screen')
            white=sum(p==0xFFFFFF for p in frame['pixels'])
            shared=request('GET','scripts/shared')
            title=next((i['value'] for i in shared if i.get('owner')==app_name and i.get('key')=='title'),'')
            if white>15 and title: break
            time.sleep(.2)
        check(request('GET','device')['currentApp']==app_name,'on-demand display selected')
        check(frame['width']==52 and frame['height']==16 and white>15, '52x16 rendered text frame')
        check(bool(title),'metadata received from standalone Home Assistant blueprint')
        settings=request('GET','settings')
        check(settings.get('blockNavigation') is True,'local navigation blocked during remote')
        dwell=settings.get('appDurationMs',7000)/1000+1
        if dwell>50: raise RuntimeError('Carousel dwell exceeds bounded smoke-test wait')
        time.sleep(dwell)
        check(request('GET','device')['currentApp']==app_name,'native display ownership holds across carousel dwell')
        request('POST','apps/next')
        check(request('GET','device')['currentApp']!=app_name,'native exit restores another app')
        check(request('GET','settings').get('blockNavigation') is False,'native exit releases navigation')
        return report
    finally:
        for name in reversed(installed):
            request('DELETE','apps/'+name)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',required=True)
    parser.add_argument('--root',required=True)
    parser.add_argument('--player',required=True)
    parser.add_argument('--device-root',required=True)
    args=parser.parse_args()
    print(json.dumps(run(args.url,args.root,args.player,args.device_root),indent=2))

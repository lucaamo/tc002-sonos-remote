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
    playlist_name='sonos_clean_test_playlists'
    app_name='sonos_clean_test'
    existing={a['name'] for a in request('GET','apps')}
    if {module_name,playlist_name,app_name} & existing:
        raise RuntimeError('Test names already exist; refusing to replace them')
    module=(ROOT/'apps/sonos_artist_names.ax').read_text().replace('sonos_artist_names',module_name)
    playlists=(ROOT/'apps/sonos_playlists.ax').read_text().replace('sonos_playlists',playlist_name)
    app=(ROOT/'apps/sonos_remote.ax').read_text().replace('sonos_artist_names',module_name).replace('sonos_playlists',playlist_name)
    # Fail before publishing if timing jitter or a physical input would send
    # an unexpected music command. Smoke tests may publish only refresh.
    app=app.replace('  def send(action)\n', '  def send(action)\n    if action != "refresh" raise "test_failed", "unexpected media command: " + action end\n')
    app=app.replace('  def send_value(action, value)\n', '  def send_value(action, value)\n    raise "test_failed", "unexpected volume command"\n')
    app=app.replace('  def send_playlist(item)\n', '  def send_playlist(item)\n    raise "test_failed", "unexpected playlist confirmation"\n')
    app=app.replace('    self.last_state = now_ms()', '    shared.set("rx", now_ms())\n    if topic == self.root + "/state/title" shared.set("title", payload) end\n    if topic == self.root + "/state/volume" shared.set("volume", payload) end\n    self.last_state = now_ms()')
    settings=request('GET','settings')
    dwell=settings.get('appDurationMs',7000)/1000+1
    if dwell>50: raise RuntimeError('Carousel dwell exceeds bounded smoke-test wait')
    # Timed physical-input equivalents exercise the real class on the display.
    # Never confirm these synthetic playlist entries: no playback is started.
    hold=1700  # margin for timer scheduling; exact threshold is tested in the harness
    opened=int((dwell+1)*1000)+hold
    cancelled=opened+500+hold
    reopened=cancelled+500+hold
    timedout=reopened+4500  # includes the firmware's loop scheduling margin
    stages=['opened','selected','cancelled','reopened','timedout']
    # Chain a single timer: firmware permits only eight pending timers per app.
    app=app.replace('    self.enter_mode()\n  end\n\n  def enter_mode()',
        '    self.enter_mode()\n'
        '    if size(self.playlists) != 10 raise "test_failed", "ten playlist settings not loaded" end\n'
        '    self.close_picker()\n'
        f'    timer.after({opened-hold}, / -> self.smoke_step(0))\n'
        '  end\n\n  def enter_mode()')
    app=app.replace('  def enter_mode()', f'''  def smoke_step(stage)
    var button = self.device_root + "/state/buttons/knob"
    var delay = 0
    if stage == 0 || stage == 3 || stage == 5
      self.on_control(button, "1")
      delay = {hold}
    elif stage == 1
      self.on_control(button, "0")
      self.smoke_stage("opened")
      delay = 300
    elif stage == 2
      self.on_control(self.device_root + "/event/knob", "{{\\"turn\\":-1}}")
      self.smoke_stage("selected")
      delay = 200
    elif stage == 4
      self.on_control(button, "0")
      self.smoke_stage("cancelled")
      delay = 500
    elif stage == 6
      self.on_control(button, "0")
      self.smoke_stage("reopened")
      delay = 4500
    elif stage == 7
      self.smoke_stage("timedout")
      delay = 500
    else
      self.exit_mode()
      return
    end
    if timer.after(delay, / -> self.smoke_step(stage+1)) == nil
      raise "test_failed", "timer pool full"
    end
  end

  def smoke_stage(stage)
    var expected = stage == "opened" || stage == "selected" || stage == "reopened"
    if self.picker != expected raise "test_failed", stage + " picker state" end
    if stage != "opened" && self.playlist_index != 9 raise "test_failed", "tenth playlist lost" end
    if self.exit_pending raise "test_failed", "playlist gesture requested exit" end
    shared.set(stage, true)
  end

  def enter_mode()''')
    installed=[]
    report={'firmware':request('GET','device')['version'],'checks':[]}
    def check(condition,label):
        if not condition: raise AssertionError(label)
        report['checks'].append(label)
    try:
        for name,source in [(module_name,module),(playlist_name,playlists),(app_name,app)]:
            installed.append(name)
            result=request('PUT','apps/script/'+name,source)
            check(result.get('error') is None,'compile '+name)
        fields=request('GET','apps/'+app_name+'/config')
        # Config endpoint returns {fields:[...]} on the official beta.
        fields=fields.get('fields',[]) if isinstance(fields,dict) else fields
        neutral={f['key']:f.get('value',f.get('default')) for f in fields}
        check(not neutral.get('player') and not neutral.get('device_root'), 'neutral entity and clock defaults')
        fields=request('GET','apps/'+playlist_name+'/config')['fields']
        neutral_playlists={f['key']:f['value'] for f in fields}
        check(len(neutral_playlists)==10,'ten configurable playlist slots')
        check(all(not neutral_playlists.get('playlist'+str(n)) for n in range(1,11)), 'empty playlist defaults')
        request('PATCH','apps/'+playlist_name+'/config',
                {'playlist'+str(n):f'Test {n}|spotify:playlist:EXAMPLE_{n}|playlist' for n in range(1,11)})
        request('PATCH','apps/'+app_name+'/config',{'root':topic_root,'player':player,'device_root':device_root,'icon_name':'','long_ms':1200,'picker_ms':3000})
        row=next(a for a in request('GET','apps') if a['name']==app_name)
        check(row.get('ondemand') is True,'official on-demand registration')
        request('PUT','apps/active',{'name':app_name,'fast':True})
        launched=time.monotonic()
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
        time.sleep(max(0,launched+dwell-time.monotonic()))
        check(request('GET','device')['currentApp']==app_name,'native display ownership holds across carousel dwell')
        deadline=launched+(timedout+500)/1000+6
        passed=set()
        picker_frame=False
        while time.monotonic()<deadline:
            row=next(a for a in request('GET','apps') if a['name']==app_name)
            if row.get('error'): raise AssertionError(row['error'])
            shared=request('GET','scripts/shared')
            passed.update(i['key'] for i in shared
                          if i.get('owner')==app_name and i.get('key') in stages and i.get('value') is True)
            if 'opened' in passed and 'cancelled' not in passed:
                frame=request('GET','display/screen')
                picker_frame=picker_frame or (frame['width']==52 and frame['height']==16
                                              and sum(p==0xFFFFFF for p in frame['pixels'])>15)
            if request('GET','device')['currentApp']!=app_name: break
            time.sleep(.1)
        for stage in stages:
            check(stage in passed,'live playlist '+stage)
        check(picker_frame,'playlist selector renders on actual display')
        check(request('GET','device')['currentApp']!=app_name,'backend exit path unloads through native MQTT')
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

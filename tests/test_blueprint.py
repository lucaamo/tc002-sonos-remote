from __future__ import annotations
import ast
import json
import unittest
from pathlib import Path
import yaml
from jinja2 import StrictUndefined
from jinja2.nativetypes import NativeEnvironment

ROOT = Path(__file__).resolve().parents[1]

class BlueprintLoader(yaml.SafeLoader):
    pass
BlueprintLoader.add_constructor('!input',lambda loader,node: {'input':loader.construct_scalar(node)})
BP = yaml.load((ROOT/'home-assistant/sonos_remote.yaml').read_text(),Loader=BlueprintLoader)

def render(template,**variables):
    env=NativeEnvironment(undefined=StrictUndefined)
    env.filters['from_json']=lambda s,default: json.loads(s) if isinstance(s,str) and s.lstrip().startswith(('{','[','"')) else default
    result=env.from_string(template).render(**variables)
    # HA converts whitespace-padded template literals to their native types.
    if isinstance(result,str):
        try: return ast.literal_eval(result.strip())
        except (ValueError,SyntaxError): pass
    return result

def commands():
    entity='media_player.example'
    def c(action,**data): return dict(action=action,player_entity_id=entity,**data)
    return [
        (c('refresh'),True), (c('play_pause'),True), (c('next'),True), (c('previous'),True),
        (c('volume',value=0),True), (c('volume',value=100),True), (c('volume',value=12.5),True),
        (c('delta',value=-25),True), (c('delta',value=25),True),
        (c('play_media',media_content_id='SQ:10',media_content_type='favorite_item_id'),True),
        (c('play_media',media_content_id='spotify:playlist:EXAMPLE',media_content_type='playlist'),True),
        ([],False), (None,False), ('refresh',False), ({},False),
        (dict(action='next',player_entity_id='media_player.another'),False),
        (c('delete'),False), (c('media_player.volume_set'),False),
        (c('volume',value=True),False), (c('volume',value='50'),False),
        (c('volume',value=-1),False), (c('volume',value=101),False),
        (c('volume',value=float('nan')),False), (c('delta',value=26),False),
        (c('delta',value=-26),False), (c('delta',value=None),False),
        (c('play_media',media_content_id='',media_content_type='playlist'),False),
        (c('play_media',media_content_id='x'*769,media_content_type='playlist'),False),
        (c('play_media',media_content_id='SQ:10',media_content_type=None),False),
        (c('play_media',media_content_id='SQ:10',media_content_type='x'*65),False),
    ]

class BlueprintTests(unittest.TestCase):
    def test_protocol_validation_rejects_wrong_entity_and_malformed_commands(self):
        template=BP['actions'][2]['variables']['valid_command']
        for cmd,expected in commands():
            with self.subTest(cmd=cmd):
                self.assertIs(render(template,cmd=cmd,player='media_player.example'),expected)

    def test_fixed_service_allowlist_and_serial_execution(self):
        def services(node):
            if isinstance(node,dict):
                if 'action' in node: yield node['action']
                for value in node.values(): yield from services(value)
            elif isinstance(node,list):
                for value in node: yield from services(value)
        self.assertEqual(set(services(BP)), {'media_player.media_play_pause',
            'media_player.media_next_track','media_player.media_previous_track',
            'media_player.volume_set','media_player.play_media','mqtt.publish'})
        self.assertEqual(BP['mode'],'queued')
        self.assertEqual(BP['variables']['player'],{'input':'player'})

    def test_topic_root_validation(self):
        template=BP['actions'][0]['variables']['valid_root']
        for value in ['', 'remote/', 'remote/#', 'remote/+', 'bad\nroot', 'x'*97, None]:
            self.assertFalse(render(template,topic_root=value))
        self.assertTrue(render(template,topic_root='clock2/sonos'))

    def test_delta_requires_known_volume_and_clamps(self):
        template=BP['actions'][4]['choose'][0]['sequence'][0]['choose'][3]['sequence'][0]['variables']['target_volume']
        for current,delta,expected in [(None,5,None),(0,-5,0),(1,5,1),(.4,5,.45)]:
            self.assertEqual(render(template,command_action='delta',current_volume=current,cmd={'value':delta}),expected)
        self.assertEqual(render(template,command_action='volume',current_volume=None,cmd={'value':20}),.2)

    def test_native_artwork_resolves_proxy_and_preserves_absolute_url(self):
        template=BP['actions'][-1]['choose'][1]['sequence'][0]['variables']['cover_url']
        cases=[
            ('/api/media_player_proxy/media_player.example?token=sample',
             'http://ha.example:8123/api/media_player_proxy/media_player.example?token=sample'),
            ('https://images.example/album.jpg?size=large', 'https://images.example/album.jpg?size=large'),
            ('', ''), ('//another.example/album.jpg', ''),
            ('file:///etc/image.jpg', ''), ('https://images.example/a b.jpg', ''),
            ('https://images.example/a\nb.jpg', ''), ('https://images.example/a\tb.jpg', ''),
            ('https://images.example/'+'x'*2050, ''),
        ]
        for picture,expected in cases:
            with self.subTest(picture=picture):
                result=render(template,player='media_player.example',
                    artwork_base_url='http://ha.example:8123/',
                    state_attr=lambda entity,key: picture,
                    states=lambda entity: 'playing')
                self.assertEqual(result.strip(),expected)
        result=render(template,player='media_player.example',
            artwork_base_url='http://ha.example:8123',
            state_attr=lambda entity,key: '/album.jpg', states=lambda entity: 'unavailable')
        self.assertEqual(result.strip(),'')

    def test_existing_installations_keep_artwork_opt_in(self):
        inputs=BP['blueprint']['input']
        self.assertTrue(inputs['clear_artwork']['default'])
        self.assertEqual(inputs['artwork_base_url']['default'],'')

if __name__=='__main__': unittest.main()

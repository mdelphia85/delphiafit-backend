"""End-to-end DelphiaFit integration smoke test.

Run only in a development/test environment after installing requirements.txt.
The script creates and deletes /tmp/delphiafit_integration_smoke.db and enables
debug reset-token return only inside this process. It never targets production.
"""

import os, sys, json, subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['DATABASE_URL'] = 'sqlite:////tmp/delphiafit_integration_smoke.db'
os.environ['JWT_SECRET'] = 'integration-smoke-test-secret-not-for-production'
os.environ['PASSWORD_RESET_DEBUG_RETURN_TOKEN'] = 'true'

# fresh schema through the actual migration module
p = Path('/tmp/delphiafit_integration_smoke.db')
if p.exists(): p.unlink()
subprocess.run([sys.executable, '-m', 'app.database.migrate'], cwd=ROOT, check=True, env=os.environ.copy(), stdout=subprocess.PIPE, text=True)

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.user import User
from app.models.coach import Coach
from app.models.team import Team
from app.models.client import Client
from app.models.invite import Invite
from app.models.messages import Message
from app.auth.hashing import hash_password

client=TestClient(app)
results=[]
def chk(name, response, expect=range(200,300), pred=None):
    ok=response.status_code in expect
    data=None
    try: data=response.json()
    except Exception: data=response.text
    if ok and pred is not None:
        try: ok=bool(pred(data))
        except Exception: ok=False
    results.append((name, response.status_code, ok, data if not ok else None))
    if not ok:
        print('FAIL',name,response.status_code,data)
    return data

def auth(token): return {'Authorization':f'Bearer {token}'}

# USER auth + frontend flows
u=chk('register',client.post('/auth/register',json={'name':'Integration User','email':'user@example.com','password':'longpassword1'}),pred=lambda d:d['email']=='user@example.com')
victim=chk('register second user',client.post('/auth/register',json={'name':'Second User','email':'second@example.com','password':'secondpassword1'}),pred=lambda d:d['email']=='second@example.com')
l=chk('login',client.post('/auth/login',json={'email':'user@example.com','password':'longpassword1'}),pred=lambda d:'access_token' in d)
ut=l['access_token']
chk('profile get default',client.get('/profile/get',headers=auth(ut)),pred=lambda d:d['name']=='Integration User')
profile={'name':'Integrated Name','dob':'1990-01-02','weight_unit':'lb','height_unit':'in','starting_weight':'210','current_weight':'200','goal_weight':'185','height':'72'}
chk('profile update',client.post('/profile/update',headers=auth(ut),json=profile),pred=lambda d:d['current_weight']=='200')
chk('profile persists',client.get('/profile/get',headers=auth(ut)),pred=lambda d:d['name']=='Integrated Name' and d['height']=='72')
progress={'email':'spoof@example.com','date':datetime.now(UTC).date().isoformat(),'protein':150,'water':96,'calories':2200,'meals':4,'workouts':1,'supplements':2}
chk('progress log',client.post('/api/progress/log',headers=auth(ut),json=progress),pred=lambda d:d['entry']['protein']==150)
chk('progress history',client.get('/api/progress/history?email=wrong@example.com',headers=auth(ut)),pred=lambda d:len(d['history'])==1 and d['history'][0]['water']==96)
chk('progress summary',client.get('/api/progress/summary?email=wrong@example.com&days=7',headers=auth(ut)),pred=lambda d:len(d['entries'])==1)
chk('free training',client.post('/free/log',headers=auth(ut),json={'workout_name':'Free Session','skill_focus':'mobility','notes':'good','extra':'none','duration_seconds':1800}),pred=lambda d:d.get('mode')=='manual')
legacy={'mode':'structured','sport':'Basketball','category':'Shooting','level':'Beginner','drill':{'name':'Form Shooting','output':'10 makes'},'duration':25,'notes':'solid','timestamp':datetime.now(UTC).isoformat(),'completed':True}
chk('legacy workout',client.post('/workouts',headers=auth(ut),json=legacy),pred=lambda d:d.get('mode')=='structured')
chk('recent drills',client.get('/drills/recent',headers=auth(ut)),pred=lambda d:len(d['logs'])>=1 and d['logs'][0]['sport']=='Basketball')

# password reset lifecycle
forgot=chk('user forgot',client.post('/auth/forgot-password',json={'email':'user@example.com'}),pred=lambda d:'debug_token' in d)
rt=forgot['debug_token']
chk('user reset',client.post('/auth/reset-password',json={'email':'user@example.com','token':rt,'new_password':'newlongpassword2'}))
chk('user login new password',client.post('/auth/login',json={'email':'user@example.com','password':'newlongpassword2'}),pred=lambda d:'access_token' in d)

# Seed admin, coach/team/client/invite/message via ORM to test UI contracts
with SessionLocal() as db:
    user=db.query(User).filter(User.email=='user@example.com').one(); user.is_admin=True
    coach=Coach(email='headcoach@example.com',name='Head Coach',organization='Delphia',role='head_coach',hashed_password=hash_password('coachpassword1'),is_active=True)
    db.add(coach); db.flush()
    team=Team(coach_id=coach.id,name='Delphia Varsity',sport='Basketball',level='Varsity',organization='Delphia',season='2026',is_active=True)
    db.add(team); db.flush()
    clientrow=Client(coach_id=coach.id,team_id=team.id,email='athlete@example.com',name='Athlete One',status='active')
    db.add(clientrow)
    invite=Invite(coach_id=coach.id,team_id=team.id,email='assistant@example.com',role='assistant_coach',token='assistant-token-123',expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(days=1),accepted=False)
    db.add(invite)
    db.add(Message(name='Integration User',email='user@example.com',subject='Help',message='Test message',is_read=False))
    db.add(Message(name='Second User',email='second@example.com',subject='Delete me',message='Second test message',is_read=False))
    db.commit(); team_id=team.id; client_id=clientrow.id

# ADMIN contracts
al=chk('admin login',client.post('/admin/login',json={'email':'user@example.com','password':'newlongpassword2'}),pred=lambda d:'access_token' in d)
at=al['access_token']
adminh=auth(at)
for name,url,pred in [
 ('admin me','/admin/me',lambda d:d['email']=='user@example.com'),
 ('admin users','/admin/users',lambda d:isinstance(d,list) and len(d)>=1),
 ('admin analytics','/admin/analytics',lambda d:'overview' in d and 'top_workouts' in d and 'recent_activity' in d),
 ('admin dashboard','/admin/dashboard',lambda d:isinstance(d,dict)),
 ('admin system health','/admin/system/health',lambda d:d.get('database_status') in {'connected','ok'}),
 ('admin actions','/admin/actions/recent',lambda d:'actions' in d),
 ('admin messages','/admin/messages',lambda d:isinstance(d,list) and len(d)>=1 and 'resolved' in d[0]),
 ('admin logs','/admin/logs',lambda d:'logs' in d and isinstance(d['logs'],list)),
]: chk(name,client.get(url,headers=adminh),pred=pred)
ann=chk('announcement create',client.post('/admin/announcements',headers=adminh,json={'title':'Test','body':'Body copy'}),pred=lambda d:d['body']=='Body copy')
aid=ann['id']
chk('announcements get',client.get('/admin/announcements',headers=adminh),pred=lambda d:isinstance(d,list) and any(x['id']==aid and x['body']=='Body copy' for x in d))
chk('announcement delete',client.delete(f'/admin/announcements/{aid}',headers=adminh))
msgs=client.get('/admin/messages',headers=adminh).json(); mid=msgs[0]['id']
chk('message resolve',client.patch(f'/admin/messages/{mid}/resolve',headers=adminh),pred=lambda d:d.get('resolved') is True or d.get('message',{}).get('resolved') is True)
# admin user detail contracts
uid=u['id']
for name,suf,pred in [
 ('admin user detail','',lambda d:d['id']==uid and 'hashed_password' not in d),
 ('admin user workouts','/workouts',lambda d:isinstance(d,list) and len(d)>=2),
 ('admin user daily','/daily',lambda d:isinstance(d,list) and len(d)>=1),
 ('admin user messages','/messages',lambda d:isinstance(d,list) and len(d)>=1),
 ('admin user activity','/logs',lambda d:isinstance(d,list)),
]: chk(name,client.get(f'/admin/users/{uid}{suf}',headers=adminh),pred=pred)
victim_id=victim['id']
chk('admin toggle user',client.patch(f'/admin/users/{victim_id}/admin',headers=adminh),pred=lambda d:d.get('user',{}).get('is_admin') is True)
second_msg=next(x for x in client.get('/admin/messages',headers=adminh).json() if x['email']=='second@example.com')
chk('admin delete message',client.delete(f"/admin/messages/{second_msg['id']}",headers=adminh))
chk('admin delete user',client.delete(f'/admin/users/{victim_id}',headers=adminh),pred=lambda d:d.get('status')=='deleted')

# COACH contracts
cl=chk('coach login',client.post('/coach/login',json={'email':'headcoach@example.com','password':'coachpassword1'}),pred=lambda d:'access_token' in d and d['team_id']==team_id)
ct=cl['access_token']; coachh=auth(ct)
chk('coach dashboard',client.get('/coach/team',headers=coachh),pred=lambda d:d['team_id']==team_id and d['stats']['totalClients']>=1)
chk('staff clients',client.get('/staff/clients',headers=coachh),pred=lambda d:len(d['clients'])>=1 and d['clients'][0]['email']=='athlete@example.com')
chk('staff invite',client.post('/staff/clients/invite',headers=coachh,json={'email':'newathlete@example.com'}),pred=lambda d:'invite_id' in d)
with SessionLocal() as db:
    client_invite_token=db.query(Invite).filter(Invite.email=='newathlete@example.com', Invite.role=='client').one().token
chk('client invite accept',client.post('/staff/invitations/accept',json={'invitation_token':client_invite_token,'name':'New Athlete','password':'athletepassword1'}),pred=lambda d:d.get('login_email')=='newathlete@example.com')
chk('client login after invite',client.post('/auth/login',json={'email':'newathlete@example.com','password':'athletepassword1'}),pred=lambda d:'access_token' in d)
chk('staff remove',client.delete(f'/staff/clients/{client_id}',headers=coachh),pred=lambda d:d.get('status')=='removed')
# assistant coach invite acceptance + login + shared team access
chk('coach invite accept',client.post('/coach/invitations/accept',json={'invitation_token':'assistant-token-123','name':'Assistant Coach','password':'assistantpass1'}),pred=lambda d:d['team_id']==team_id)
acl=chk('assistant coach login',client.post('/coach/login',json={'email':'assistant@example.com','password':'assistantpass1'}),pred=lambda d:d.get('team_id')==team_id)
ach=auth(acl['access_token'])
chk('assistant shared team',client.get(f'/coach/team?team_id={team_id}',headers=ach),pred=lambda d:d['team_id']==team_id)
# coach password reset
cf=chk('coach forgot',client.post('/coach/password/forgot',json={'email':'assistant@example.com'}),pred=lambda d:'debug_token' in d)
chk('coach reset',client.post('/coach/password/reset',json={'email':'assistant@example.com','token':cf['debug_token'],'new_password':'assistantpass2'}))
chk('coach login reset password',client.post('/coach/login',json={'email':'assistant@example.com','password':'assistantpass2'}),pred=lambda d:'access_token' in d)

# public sports catalog hierarchy
sports_data=chk('sports list',client.get('/sports'),pred=lambda d:isinstance(d.get('sports'),list) and len(d['sports'])>0)
sport=sports_data['sports'][0]
skills=chk('sports skills',client.get(f'/sports/{sport}/skills'),pred=lambda d:isinstance(d.get('skills'),list) and len(d['skills'])>0)
category=skills['skills'][0]
levels=chk('sports levels',client.get(f'/sports/{sport}/{category}/levels'),pred=lambda d:isinstance(d.get('levels'),list) and len(d['levels'])>0)
level=levels['levels'][0]
chk('sports drill',client.get(f'/sports/{sport}/{category}/{level}/drills'),pred=lambda d:isinstance(d.get('drill'),str) and len(d['drill'])>0)

# Tactical helper contracts are authenticated and user-owned.
for division in ('firefighters','ems','police','military'):
    payload={'category':'Readiness','name':f'{division} drill','level':'advanced','duration':'20 min','notes':'integration','intensity':'high','environment':'urban','objective':'readiness'}
    created=chk(f'{division} tactical create',client.post(f'/tactical/{division}/log',headers=auth(ut),json=payload),pred=lambda d:d.get('intensity')=='high' and d.get('environment')=='urban')
    did=created['id']
    chk(f'{division} tactical list',client.get(f'/tactical/{division}/logs',headers=auth(ut)),pred=lambda d:any(x['id']==did for x in d))
    chk(f'{division} tactical update',client.put(f'/tactical/{division}/log/{did}',headers=auth(ut),json={'notes':'updated','focus':'speed'}),pred=lambda d:d.get('focus')=='speed' and d.get('notes')=='updated')
    chk(f'{division} tactical delete',client.delete(f'/tactical/{division}/log/{did}',headers=auth(ut)),pred=lambda d:d.get('success') is True)

passed=sum(1 for _,_,ok,_ in results if ok)
print(f'WORKFLOW_RESULTS {passed}/{len(results)} passed')
if passed != len(results):
    for row in results:
        if not row[2]: print(row)
    raise SystemExit(1)

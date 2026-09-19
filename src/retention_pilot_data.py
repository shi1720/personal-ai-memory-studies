"""Controlled fictional journals with observable, fixed empirical targets."""
import hashlib
import json
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]
PAIRS=[('swimming','cycling'),('painting','pottery'),('yoga','pilates'),
       ('chess','badminton'),('gardening','baking'),('walking','rowing')]
DETAILS=['The venue had a mural of bright blue birds beside the entrance.',
         'A brass clock chimed while rain tapped against the large windows.',
         'A small delivery robot paused beside a stack of orange crates.',
         'The lights flickered once as a distant train crossed the bridge.',
         'A visitor left a purple umbrella next to a carved wooden bench.',
         'Someone carried a large paper kite through the courtyard outside.']
PROMPTS={
 'important':'You manage episodic memory for a personal assistant. Select exactly six events that are most important and useful to remember about this user for future conversations. Preserve concrete evidence about preferences and experiences.',
 'representative':'You manage episodic memory for a personal assistant. Select exactly six events that represent the overall pattern of this user\'s experiences. Cover recurring themes and typical outcomes, and avoid overemphasizing unusually detailed events.'}

def make_journals():
    out=[]
    for seed in range(12):
        rng=random.Random(31000+seed)
        activities=list(PAIRS[seed%6])
        if seed//6:activities.reverse()
        events=[]
        for activity,positive_count in zip(activities,[9,6]):
            outcomes=[True]*positive_count+[False]*(12-positive_count)
            rng.shuffle(outcomes)
            for positive in outcomes:
                events.append({'activity':activity,'positive':positive})
        rng.shuffle(events)
        detail_index=0
        for i,e in enumerate(events):
            e.update(id=f'E{i+1:02d}',day=i+1)
            e['detail']=''
            if e['activity']==activities[1] and e['positive']:
                e['detail']=DETAILS[detail_index]
                detail_index+=1
        # Display chronology remains fixed; IDs are event identity, not labels.
        out.append({'id':f'journal-{seed:02d}','seed':31000+seed,'activities':activities,'events':events})
    return out

def render_journal(journal,detailed):
    lines=[]
    for e in journal['events']:
        outcome='I enjoyed the session.' if e['positive'] else 'I did not enjoy the session.'
        text=f"{e['id']} | Day {e['day']:02d}: I attended a {e['activity']} session. {outcome}"
        if detailed and e['detail']:text+=' '+e['detail']
        lines.append(text)
    return '\n'.join(lines)

def messages(journal,writer,detailed):
    return [{'role':'system','content':PROMPTS[writer]+' Return only a JSON array of exactly six distinct event IDs. Do not include explanations or any IDs not in the journal.'},
            {'role':'user','content':'ACTIVITY JOURNAL\n'+render_journal(journal,detailed)+'\n\nSelect six event IDs:'}]

def parse_selection(text,allowed):
    try:result=json.loads(text.strip())
    except json.JSONDecodeError:return None
    if not isinstance(result,list) or len(result)!=6 or any(not isinstance(x,str) for x in result):return None
    if len(set(result))!=6 or not set(result).issubset(allowed):return None
    return result

def main():
    output=ROOT/'results/pilot-003-journals.json'
    output.write_text(json.dumps(make_journals(),indent=2)+'\n')
    print(output,hashlib.sha256(output.read_bytes()).hexdigest())

if __name__=='__main__':main()

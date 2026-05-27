import random
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(prefix="/sports", tags=["Sports"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ---------------------------------------------------------
# ⭐ PASTE YOUR FULL PYTHON SPORTS GENERATOR HERE
#
SPORTS = {
"Boxing": {
    "Punching Technique": {
        "actions": ["Jab", "Cross", "Hook", "Uppercut"],
        "modifiers": ["Mechanics", "Accuracy", "Timing", "Footwork"],
    },
    "Footwork": {
        "actions": ["Pivot", "Angle Step", "Lateral Movement", "Forward Pressure"],
        "modifiers": ["Basics", "Control", "Speed", "Chains"],
    },
    "Defense": {
        "actions": ["Slip", "Roll", "Parry", "Block"],
        "modifiers": ["Basics", "Counter", "Timing", "Reaction"],
    },
    "Conditioning": {
        "actions": ["Shadowboxing", "Jump Rope", "Bag Work", "Footwork Conditioning"],
        "modifiers": ["Light", "Intervals", "High‑Intensity", "Endurance"],
    },
},
"Kickboxing": {
    "Striking": {
        "actions": ["Jab‑Cross", "Roundhouse Kick", "Teep", "Low Kick"],
        "modifiers": ["Basics", "Accuracy", "Timing", "Power"],
    },
    "Defense": {
        "actions": ["Check", "Slip", "Parry", "Block"],
        "modifiers": ["Basics", "Counter", "Reaction", "Chains"],
    },
    "Footwork": {
        "actions": ["Angle Step", "Lateral Movement", "Forward Pressure", "Exit Step"],
        "modifiers": ["Basics", "Control", "Speed", "Chains"],
    },
    "Conditioning": {
        "actions": ["Bag Rounds", "Pad Rounds", "Shadowboxing", "Sprint Intervals"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Power"],
    },
},
"Muay Thai": {
    "Striking": {
        "actions": ["Jab‑Cross", "Roundhouse Kick", "Teep", "Elbow Strike"],
        "modifiers": ["Basics", "Accuracy", "Timing", "Power"],
    },
    "Clinching": {
        "actions": ["Neck Tie", "Knee Strike", "Off‑Balance", "Frame Control"],
        "modifiers": ["Basics", "Positioning", "Timing", "Dominance"],
    },
    "Defense": {
        "actions": ["Check Kick", "Long Guard", "Parry", "Slip"],
        "modifiers": ["Basics", "Counter", "Reaction", "Chains"],
    },
    "Footwork": {
        "actions": ["Angle Step", "Cut Step", "Forward Pressure", "Retreat Step"],
        "modifiers": ["Basics", "Control", "Speed", "Chains"],
    },
    "Conditioning": {
        "actions": ["Bag Rounds", "Pad Rounds", "Clinching Rounds", "Sprint Intervals"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Power"],
    },
},
"Wrestling": {
    "Takedowns": {
        "actions": ["Double Leg", "Single Leg", "High‑Crotch", "Snap‑Down"],
        "modifiers": ["Setup", "Entry", "Finish", "Chain‑Wrestling"],
    },
    "Top Control": {
        "actions": ["Breakdown", "Half‑Nelson", "Arm Bar", "Cradle"],
        "modifiers": ["Basics", "Pressure", "Transition", "Ride‑Time"],
    },
    "Bottom Escapes": {
        "actions": ["Stand‑Up", "Sit‑Out", "Granby Roll", "Hip‑Heist"],
        "modifiers": ["Basics", "Timing", "Explosive", "Chain‑Escape"],
    },
    "Neutral Defense": {
        "actions": ["Sprawl", "Down‑Block", "Re‑Shot", "Underhook Defense"],
        "modifiers": ["Basics", "Reaction", "Counter", "Positioning"],
    },
    "Conditioning": {
        "actions": ["Hand‑Fighting", "Stance‑Motion", "Sprint Intervals", "Grip Training"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Power"],
    },
},
"Brazilian Jiu-Jitsu": {
    "Takedowns": {
        "actions": ["Single Leg", "Double Leg", "Body Lock", "Foot Sweep"],
        "modifiers": ["Basics", "Setup", "Timing", "Chain‑Entry"],
    },
    "Guard": {
        "actions": ["Closed Guard", "Open Guard", "De La Riva", "Half Guard"],
        "modifiers": ["Retention", "Sweeps", "Entries", "Transitions"],
    },
    "Passing": {
        "actions": ["Toreando", "Knee Cut", "Over‑Under", "Stack Pass"],
        "modifiers": ["Basics", "Pressure", "Speed", "Control"],
    },
    "Submissions": {
        "actions": ["Armbar", "Triangle", "Rear Naked Choke", "Guillotine"],
        "modifiers": ["Basics", "Setup", "Finish", "Chain‑Attack"],
    },
    "Escapes": {
        "actions": ["Bridge & Roll", "Shrimp Escape", "Hip Escape", "Frame Escape"],
        "modifiers": ["Basics", "Timing", "Explosive", "Survival"],
    },
},
"Judo": {
    "Tachi‑Waza (Standing Throws)": {
        "actions": ["O‑goshi", "Seoi‑nage", "Osoto‑gari", "Uchi‑mata"],
        "modifiers": ["Kuzushi", "Tsukuri", "Kake", "Combination"],
    },
    "Ne‑Waza (Groundwork)": {
        "actions": ["Kesa‑gatame", "Yoko‑shiho‑gatame", "Tate‑shiho‑gatame", "Kami‑shiho‑gatame"],
        "modifiers": ["Control", "Pressure", "Transition", "Escape Prevention"],
    },
    "Submissions": {
        "actions": ["Juji‑gatame", "Hadaka‑jime", "Okuri‑eri‑jime", "Kata‑gatame"],
        "modifiers": ["Basics", "Setup", "Finish", "Chain‑Attack"],
    },
    "Escapes": {
        "actions": ["Bridge & Roll", "Shrimp Escape", "Leg Trap Escape", "Hip Turn Escape"],
        "modifiers": ["Basics", "Timing", "Explosive", "Survival"],
    },
    "Grip Fighting": {
        "actions": ["Standard Grip", "Cross Grip", "Sleeve Control", "Collar Control"],
        "modifiers": ["Basics", "Dominance", "Breaking", "Entry"],
    },
},
"Karate": {
    "Kihon (Basics)": {
        "actions": ["Straight Punch", "Front Kick", "Knife‑Hand Strike", "Low Block"],
        "modifiers": ["Basics", "Form", "Timing", "Power"],
    },
    "Kata": {
        "actions": ["Heian Shodan", "Heian Nidan", "Heian Sandan", "Heian Yondan"],
        "modifiers": ["Basics", "Precision", "Flow", "Application"],
    },
    "Kumite (Sparring)": {
        "actions": ["Point Attack", "Counter Punch", "Angle Step", "Combination Entry"],
        "modifiers": ["Basics", "Timing", "Distance", "Speed"],
    },
    "Footwork": {
        "actions": ["Zenkutsu Step", "Kokutsu Shift", "Slide Step", "Switch Step"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
    "Conditioning": {
        "actions": ["Kicking Drills", "Stance Training", "Shadow Sparring", "Sprint Intervals"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Power"],
    },
},
"Taekwondo": {
    "Kicking Technique": {
        "actions": ["Front Kick", "Roundhouse Kick", "Side Kick", "Axe Kick"],
        "modifiers": ["Basics", "Accuracy", "Speed", "Power"],
    },
    "Forms (Poomsae)": {
        "actions": ["Taegeuk 1", "Taegeuk 2", "Taegeuk 3", "Taegeuk 4"],
        "modifiers": ["Basics", "Precision", "Flow", "Application"],
    },
    "Sparring (Kyorugi)": {
        "actions": ["Counter Kick", "Cut Kick", "Back Kick", "Combination Entry"],
        "modifiers": ["Basics", "Timing", "Distance", "Speed"],
    },
    "Footwork": {
        "actions": ["Slide Step", "Switch Step", "Angle Step", "Retreat Step"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
    "Conditioning": {
        "actions": ["Kicking Drills", "Plyometrics", "Sprint Intervals", "Core Circuit"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"MMA": {
    "Striking": {
        "actions": ["Jab‑Cross", "Leg Kick", "Elbow Strike", "Overhand Right"],
        "modifiers": ["Basics", "Accuracy", "Timing", "Power"],
    },
    "Wrestling": {
        "actions": ["Double Leg", "Single Leg", "Body Lock", "Trip Takedown"],
        "modifiers": ["Setup", "Entry", "Finish", "Chain‑Wrestling"],
    },
    "BJJ / Grappling": {
        "actions": ["Guard Pass", "Rear Naked Choke", "Arm Triangle", "Kimura"],
        "modifiers": ["Basics", "Pressure", "Setup", "Finish"],
    },
    "Clinch": {
        "actions": ["Underhooks", "Frame Control", "Knee Strike", "Dirty Boxing"],
        "modifiers": ["Basics", "Positioning", "Timing", "Dominance"],
    },
    "Ground & Pound": {
        "actions": ["Posture Strike", "Elbow Smash", "Hammerfist", "Control‑Strike"],
        "modifiers": ["Basics", "Pressure", "Accuracy", "Power"],
    },
},
"Baseball": {
    "Hitting": {
        "actions": ["Swing Mechanics", "Contact Drill", "Power Swing", "Timing Drill"],
        "modifiers": ["Basics", "Accuracy", "Bat Speed", "Placement"],
    },
    "Fielding": {
        "actions": ["Ground Ball", "Fly Ball", "Backhand Scoop", "Charge & Throw"],
        "modifiers": ["Basics", "Footwork", "Glove Control", "Quick Release"],
    },
    "Pitching": {
        "actions": ["Fastball", "Changeup", "Curveball", "Slider"],
        "modifiers": ["Basics", "Accuracy", "Velocity", "Movement"],
    },
    "Base Running": {
        "actions": ["Lead Off", "Steal Start", "Rounding Bases", "Slide Technique"],
        "modifiers": ["Basics", "Speed", "Timing", "Aggression"],
    },
    "Catching": {
        "actions": ["Receiving", "Blocking", "Throw‑Down", "Framing"],
        "modifiers": ["Basics", "Footwork", "Quickness", "Accuracy"],
    },
},
"Softball": {
    "Hitting": {
        "actions": ["Swing Mechanics", "Contact Drill", "Power Swing", "Timing Drill"],
        "modifiers": ["Basics", "Accuracy", "Bat Speed", "Placement"],
    },
    "Fielding": {
        "actions": ["Ground Ball", "Fly Ball", "Backhand Scoop", "Charge & Throw"],
        "modifiers": ["Basics", "Footwork", "Glove Control", "Quick Release"],
    },
    "Pitching": {
        "actions": ["Fastpitch", "Changeup", "Rise Ball", "Drop Ball"],
        "modifiers": ["Basics", "Accuracy", "Spin", "Velocity"],
    },
    "Base Running": {
        "actions": ["Lead Off", "Steal Start", "Rounding Bases", "Slide Technique"],
        "modifiers": ["Basics", "Speed", "Timing", "Aggression"],
    },
    "Catching": {
        "actions": ["Receiving", "Blocking", "Throw‑Down", "Framing"],
        "modifiers": ["Basics", "Footwork", "Quickness", "Accuracy"],
    },
},
"Football": {
    "Offense": {
        "actions": ["Route Running", "Run Block", "Pass Block", "Quarterback Drop"],
        "modifiers": ["Basics", "Timing", "Footwork", "Execution"],
    },
    "Defense": {
        "actions": ["Backpedal", "Pass Rush", "Tackle Form", "Coverage Drop"],
        "modifiers": ["Basics", "Reaction", "Pursuit", "Aggression"],
    },
    "Special Teams": {
        "actions": ["Kickoff Coverage", "Punt Coverage", "Field Goal Block", "Return Setup"],
        "modifiers": ["Basics", "Timing", "Speed", "Discipline"],
    },
    "Conditioning": {
        "actions": ["Sprint Intervals", "Agility Ladder", "Cone Drills", "Backpedal‑Sprint"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
    "Footwork": {
        "actions": ["Shuffle", "Crossover Step", "Angle Break", "Acceleration Step"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
},
"Rugby": {
    "Passing": {
        "actions": ["Spin Pass", "Pop Pass", "Offload", "Skip Pass"],
        "modifiers": ["Basics", "Accuracy", "Timing", "Distance"],
    },
    "Tackling": {
        "actions": ["Front Tackle", "Side Tackle", "Low Chop", "Wrap Tackle"],
        "modifiers": ["Basics", "Form", "Power", "Safety"],
    },
    "Rucking": {
        "actions": ["Clear Out", "Jackal Entry", "Body Position", "Counter‑Ruck"],
        "modifiers": ["Basics", "Timing", "Strength", "Technique"],
    },
    "Scrum": {
        "actions": ["Engage", "Drive", "Bind", "Hook"],
        "modifiers": ["Basics", "Power", "Coordination", "Control"],
    },
    "Kicking": {
        "actions": ["Grubber Kick", "Box Kick", "Punt", "Drop Kick"],
        "modifiers": ["Basics", "Accuracy", "Distance", "Placement"],
    },
},
"Hockey": {
    "Skating": {
        "actions": ["Forward Stride", "Backward Stride", "Crossover", "Stops"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Stickhandling": {
        "actions": ["Puck Control", "Toe Drag", "Quick Hands", "Wide Handle"],
        "modifiers": ["Basics", "Speed", "Accuracy", "Deception"],
    },
    "Shooting": {
        "actions": ["Wrist Shot", "Slap Shot", "Snap Shot", "Backhand"],
        "modifiers": ["Basics", "Power", "Accuracy", "Quick Release"],
    },
    "Checking": {
        "actions": ["Body Check", "Stick Check", "Poke Check", "Angling"],
        "modifiers": ["Basics", "Timing", "Positioning", "Safety"],
    },
    "Goalie": {
        "actions": ["Butterfly", "Kick Save", "Glove Save", "Rebound Control"],
        "modifiers": ["Basics", "Reaction", "Positioning", "Explosive"],
    },
},
"Field Hockey": {
    "Dribbling": {
        "actions": ["Push Dribble", "Indian Dribble", "Pull Back", "V‑Drag"],
        "modifiers": ["Basics", "Control", "Speed", "Deception"],
    },
    "Passing": {
        "actions": ["Push Pass", "Slap Pass", "Hit Pass", "Aerial"],
        "modifiers": ["Basics", "Accuracy", "Timing", "Distance"],
    },
    "Shooting": {
        "actions": ["Hit", "Flick", "Drag Flick", "Reverse Shot"],
        "modifiers": ["Basics", "Power", "Accuracy", "Placement"],
    },
    "Defense": {
        "actions": ["Block Tackle", "Jab Tackle", "Channeling", "Interception"],
        "modifiers": ["Basics", "Timing", "Footwork", "Positioning"],
    },
    "Goalkeeping": {
        "actions": ["Kick Save", "Stick Save", "Smother", "Clear"],
        "modifiers": ["Basics", "Reaction", "Positioning", "Explosive"],
    },
},
"Lacrosse": {
    "Shooting": {
        "actions": ["Overhand Shot", "Sidearm Shot", "Underhand Shot", "Quick Stick"],
        "modifiers": ["Basics", "Power", "Accuracy", "Placement"],
    },
    "Dodging": {
        "actions": ["Split Dodge", "Roll Dodge", "Face Dodge", "Bull Dodge"],
        "modifiers": ["Basics", "Timing", "Speed", "Deception"],
    },
    "Passing": {
        "actions": ["Overhand Pass", "Sidearm Pass", "Quick Pass", "Skip Pass"],
        "modifiers": ["Basics", "Accuracy", "Timing", "Distance"],
    },
    "Defense": {
        "actions": ["Body Position", "Stick Check", "Lift Check", "Trail Check"],
        "modifiers": ["Basics", "Timing", "Footwork", "Pressure"],
    },
    "Faceoff": {
        "actions": ["Clamp", "Rake", "Plunger", "Counter"],
        "modifiers": ["Basics", "Speed", "Strength", "Technique"],
    },
},
"Tennis": {
    "Groundstrokes": {
        "actions": ["Forehand", "Backhand", "Topspin Shot", "Slice Shot"],
        "modifiers": ["Basics", "Accuracy", "Power", "Placement"],
    },
    "Serving": {
        "actions": ["Flat Serve", "Kick Serve", "Slice Serve", "Second Serve"],
        "modifiers": ["Basics", "Power", "Spin", "Placement"],
    },
    "Volleys": {
        "actions": ["Forehand Volley", "Backhand Volley", "Punch Volley", "Drop Volley"],
        "modifiers": ["Basics", "Timing", "Control", "Touch"],
    },
    "Footwork": {
        "actions": ["Split Step", "Recovery Step", "Crossover Step", "Shuffle"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Conditioning": {
        "actions": ["Court Sprints", "Agility Ladder", "Shadow Swings", "Endurance Run"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Table Tennis": {
    "Strokes": {
        "actions": ["Forehand Drive", "Backhand Drive", "Forehand Loop", "Backhand Loop"],
        "modifiers": ["Basics", "Spin", "Speed", "Placement"],
    },
    "Serving": {
        "actions": ["Backspin Serve", "Sidespin Serve", "Topspin Serve", "No‑Spin Serve"],
        "modifiers": ["Basics", "Deception", "Placement", "Spin"],
    },
    "Footwork": {
        "actions": ["Side Shuffle", "Crossover Step", "In‑Out Step", "Recovery Step"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Defense": {
        "actions": ["Block", "Chop", "Counter‑Drive", "Lob"],
        "modifiers": ["Basics", "Timing", "Spin Control", "Placement"],
    },
    "Rallying": {
        "actions": ["Consistency Drill", "Multi‑Ball", "Random Placement", "Spin Variation"],
        "modifiers": ["Basics", "Speed", "Endurance", "Accuracy"],
    },
},
"Badminton": {
    "Strokes": {
        "actions": ["Clear", "Drop Shot", "Smash", "Drive"],
        "modifiers": ["Basics", "Accuracy", "Power", "Placement"],
    },
    "Serving": {
        "actions": ["Low Serve", "High Serve", "Flick Serve", "Drive Serve"],
        "modifiers": ["Basics", "Deception", "Placement", "Spin"],
    },
    "Footwork": {
        "actions": ["Split Step", "Lunge", "Shuffle Step", "Recovery Step"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Defense": {
        "actions": ["Lift", "Block", "Drive Defense", "Counter‑Smash"],
        "modifiers": ["Basics", "Timing", "Control", "Reaction"],
    },
    "Rallying": {
        "actions": ["Consistency Drill", "Multi‑Shuttle", "Random Placement", "Pressure Drill"],
        "modifiers": ["Basics", "Speed", "Endurance", "Accuracy"],
    },
},
"Cricket": {
    "Batting": {
        "actions": ["Forward Defense", "Cover Drive", "Pull Shot", "Cut Shot"],
        "modifiers": ["Basics", "Timing", "Placement", "Power"],
    },
    "Bowling": {
        "actions": ["Fast Bowling", "Off‑Spin", "Leg‑Spin", "Swing Bowling"],
        "modifiers": ["Basics", "Accuracy", "Variation", "Pace"],
    },
    "Fielding": {
        "actions": ["Ground Fielding", "High Catch", "Direct Hit", "Diving Stop"],
        "modifiers": ["Basics", "Footwork", "Speed", "Reaction"],
    },
    "Wicketkeeping": {
        "actions": ["Glove Work", "Stumping", "Receiving", "Footwork"],
        "modifiers": ["Basics", "Speed", "Accuracy", "Positioning"],
    },
    "Running Between Wickets": {
        "actions": ["Quick Single", "Turn Technique", "Calling", "Acceleration"],
        "modifiers": ["Basics", "Timing", "Speed", "Decision‑Making"],
    },
},
"Golf": {
    "Full Swing": {
        "actions": ["Driver Swing", "Iron Swing", "Hybrid Swing", "Fairway Wood"],
        "modifiers": ["Basics", "Accuracy", "Power", "Consistency"],
    },
    "Short Game": {
        "actions": ["Chip Shot", "Pitch Shot", "Bunker Shot", "Flop Shot"],
        "modifiers": ["Basics", "Touch", "Spin", "Control"],
    },
    "Putting": {
        "actions": ["Straight Putt", "Lag Putt", "Break Reading", "Distance Control"],
        "modifiers": ["Basics", "Feel", "Accuracy", "Consistency"],
    },
    "Course Management": {
        "actions": ["Club Selection", "Shot Shaping", "Risk Assessment", "Wind Adjustment"],
        "modifiers": ["Basics", "Strategy", "Precision", "Execution"],
    },
    "Conditioning": {
        "actions": ["Mobility Work", "Core Training", "Balance Drills", "Rotation Power"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Swimming": {
    "Freestyle": {
        "actions": ["Stroke Technique", "Breathing Pattern", "Kick Set", "Pull Set"],
        "modifiers": ["Basics", "Endurance", "Speed", "Efficiency"],
    },
    "Backstroke": {
        "actions": ["Body Position", "Kick Rhythm", "Arm Recovery", "Rotation"],
        "modifiers": ["Basics", "Timing", "Control", "Speed"],
    },
    "Breaststroke": {
        "actions": ["Kick Technique", "Pull Technique", "Timing Drill", "Glide Control"],
        "modifiers": ["Basics", "Efficiency", "Power", "Coordination"],
    },
    "Butterfly": {
        "actions": ["Dolphin Kick", "Arm Recovery", "Breathing Timing", "Stroke Rhythm"],
        "modifiers": ["Basics", "Power", "Endurance", "Timing"],
    },
    "Starts & Turns": {
        "actions": ["Dive Start", "Flip Turn", "Open Turn", "Underwater Kick"],
        "modifiers": ["Basics", "Speed", "Explosive", "Efficiency"],
    },
},
"Track & Field": {
    "Sprinting": {
        "actions": ["Acceleration", "Top Speed", "Starts", "Stride Technique"],
        "modifiers": ["Basics", "Power", "Speed", "Efficiency"],
    },
    "Distance Running": {
        "actions": ["Pacing", "Breathing", "Stride Control", "Endurance Run"],
        "modifiers": ["Basics", "Endurance", "Efficiency", "Rhythm"],
    },
    "Jumping": {
        "actions": ["Long Jump", "High Jump", "Triple Jump", "Pole Vault"],
        "modifiers": ["Basics", "Technique", "Power", "Timing"],
    },
    "Throwing": {
        "actions": ["Shot Put", "Discus", "Javelin", "Hammer Throw"],
        "modifiers": ["Basics", "Power", "Form", "Release"],
    },
    "Hurdles": {
        "actions": ["Lead Leg", "Trail Leg", "Hurdle Rhythm", "Starts"],
        "modifiers": ["Basics", "Timing", "Speed", "Technique"],
    },
},
"Water Polo": {
    "Ball Handling": {
        "actions": ["Passing", "Dribbling", "Ball Control", "Quick Release"],
        "modifiers": ["Basics", "Accuracy", "Speed", "Pressure"],
    },
    "Shooting": {
        "actions": ["Power Shot", "Skip Shot", "Lob Shot", "Quick Shot"],
        "modifiers": ["Basics", "Placement", "Power", "Deception"],
    },
    "Defense": {
        "actions": ["Shot Block", "Press Defense", "Steal Attempt", "Positioning"],
        "modifiers": ["Basics", "Timing", "Strength", "Awareness"],
    },
    "Swimming": {
        "actions": ["Eggbeater", "Sprint Swim", "Back Swim", "Change of Direction"],
        "modifiers": ["Basics", "Endurance", "Speed", "Control"],
    },
    "Center Play": {
        "actions": ["Posting Up", "Wrestling for Position", "Turn Move", "Entry Pass"],
        "modifiers": ["Basics", "Strength", "Timing", "Control"],
    },
},
"Handball": {
    "Shooting": {
        "actions": ["Jump Shot", "Standing Shot", "Sidearm Shot", "Breakthrough Shot"],
        "modifiers": ["Basics", "Power", "Accuracy", "Placement"],
    },
    "Passing": {
        "actions": ["Chest Pass", "Bounce Pass", "Overhead Pass", "Quick Pass"],
        "modifiers": ["Basics", "Timing", "Speed", "Distance"],
    },
    "Defense": {
        "actions": ["Block", "Steal Attempt", "Body Position", "Closeout"],
        "modifiers": ["Basics", "Timing", "Footwork", "Pressure"],
    },
    "Footwork": {
        "actions": ["Side Shuffle", "Crossover Step", "Acceleration Step", "Retreat Step"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Goalkeeping": {
        "actions": ["Kick Save", "Hand Save", "Angle Coverage", "Rebound Control"],
        "modifiers": ["Basics", "Reaction", "Positioning", "Explosive"],
    },
},
"Archery": {
    "Shooting Technique": {
        "actions": ["Draw", "Anchor", "Aim", "Release"],
        "modifiers": ["Basics", "Stability", "Precision", "Consistency"],
    },
    "Bow Handling": {
        "actions": ["Grip Control", "Stance Setup", "Follow‑Through", "String Alignment"],
        "modifiers": ["Basics", "Balance", "Control", "Form"],
    },
    "Distance Shooting": {
        "actions": ["Short Range", "Mid Range", "Long Range", "Variable Distance"],
        "modifiers": ["Basics", "Accuracy", "Wind Adjustment", "Consistency"],
    },
    "Conditioning": {
        "actions": ["Shoulder Strength", "Back Tension", "Core Stability", "Breath Control"],
        "modifiers": ["Light", "Endurance", "Power", "Control"],
    },
    "Mental Training": {
        "actions": ["Focus Drill", "Visualization", "Shot Routine", "Pressure Simulation"],
        "modifiers": ["Basics", "Calmness", "Consistency", "Confidence"],
    },
},
"Fencing": {
    "Footwork": {
        "actions": ["Advance", "Retreat", "Lunge", "Recovery"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Blade Work": {
        "actions": ["Parry", "Riposte", "Feint", "Disengage"],
        "modifiers": ["Basics", "Timing", "Deception", "Precision"],
    },
    "Attacks": {
        "actions": ["Direct Attack", "Compound Attack", "Counterattack", "Beat Attack"],
        "modifiers": ["Basics", "Speed", "Accuracy", "Setup"],
    },
    "Defense": {
        "actions": ["Block", "Distance Control", "Counter‑Parry", "Footwork Defense"],
        "modifiers": ["Basics", "Timing", "Reaction", "Positioning"],
    },
    "Conditioning": {
        "actions": ["Agility Ladder", "Lunge Repeats", "Core Work", "Explosive Steps"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Box Lacrosse": {
    "Shooting": {
        "actions": ["Quick Stick", "Sidearm Shot", "Overhand Shot", "Tight‑Angle Shot"],
        "modifiers": ["Basics", "Power", "Accuracy", "Deception"],
    },
    "Dodging": {
        "actions": ["Inside Roll", "Bull Dodge", "Face Dodge", "Split Dodge"],
        "modifiers": ["Basics", "Timing", "Strength", "Deception"],
    },
    "Passing": {
        "actions": ["Quick Pass", "Behind‑the‑Back", "Skip Pass", "Wall Pass"],
        "modifiers": ["Basics", "Accuracy", "Timing", "Speed"],
    },
    "Defense": {
        "actions": ["Cross‑Check", "Body Position", "Stick Lift", "Lane Denial"],
        "modifiers": ["Basics", "Timing", "Pressure", "Footwork"],
    },
    "Goalie": {
        "actions": ["Angle Coverage", "Rebound Control", "Kick Save", "Butterfly Block"],
        "modifiers": ["Basics", "Reaction", "Positioning", "Explosive"],
    },
},
"Cycling": {
    "Endurance": {
        "actions": ["Steady Ride", "Long Ride", "Tempo Ride", "Cadence Control"],
        "modifiers": ["Basics", "Endurance", "Efficiency", "Pacing"],
    },
    "Speed Work": {
        "actions": ["Sprint Intervals", "Hill Sprints", "Standing Sprint", "Acceleration Drill"],
        "modifiers": ["Basics", "Power", "Speed", "Explosive"],
    },
    "Climbing": {
        "actions": ["Seated Climb", "Standing Climb", "Switchback Technique", "Hill Endurance"],
        "modifiers": ["Basics", "Power", "Pacing", "Efficiency"],
    },
    "Bike Handling": {
        "actions": ["Cornering", "Braking", "Balance Control", "Drafting"],
        "modifiers": ["Basics", "Control", "Timing", "Safety"],
    },
    "Conditioning": {
        "actions": ["Core Training", "Leg Strength", "Mobility Work", "Breath Control"],
        "modifiers": ["Light", "Endurance", "Power", "Control"],
    },
},
"Rowing": {
    "Technique": {
        "actions": ["Catch", "Drive", "Finish", "Recovery"],
        "modifiers": ["Basics", "Timing", "Power", "Efficiency"],
    },
    "Erg Work": {
        "actions": ["Steady State", "Intervals", "Power 10s", "Rate Ladders"],
        "modifiers": ["Basics", "Endurance", "Power", "Pacing"],
    },
    "Boat Skills": {
        "actions": ["Balance Drill", "Feathering", "Slide Control", "Synchronization"],
        "modifiers": ["Basics", "Control", "Timing", "Coordination"],
    },
    "Conditioning": {
        "actions": ["Core Work", "Leg Strength", "Mobility", "Explosive Training"],
        "modifiers": ["Light", "Endurance", "Power", "Control"],
    },
    "Starts": {
        "actions": ["High‑Rate Start", "Build Sequence", "Power Start", "Race Start"],
        "modifiers": ["Basics", "Timing", "Power", "Execution"],
    },
},
"Surfing": {
    "Paddling": {
        "actions": ["Prone Paddle", "Sprint Paddle", "Positioning Paddle", "Duck Dive Prep"],
        "modifiers": ["Basics", "Endurance", "Speed", "Efficiency"],
    },
    "Takeoff": {
        "actions": ["Pop‑Up", "Late Takeoff", "Angle Takeoff", "Steep Drop"],
        "modifiers": ["Basics", "Timing", "Commitment", "Control"],
    },
    "Riding": {
        "actions": ["Bottom Turn", "Cutback", "Floater", "Top Turn"],
        "modifiers": ["Basics", "Power", "Flow", "Line Choice"],
    },
    "Wave Selection": {
        "actions": ["Reading Sets", "Positioning", "Priority Choice", "Exit Strategy"],
        "modifiers": ["Basics", "Awareness", "Timing", "Risk"],
    },
    "Conditioning": {
        "actions": ["Paddle Intervals", "Pop‑Up Reps", "Balance Drills", "Breath Holds"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Skateboarding": {
    "Basics": {
        "actions": ["Push", "Stop", "Turn", "Ollie"],
        "modifiers": ["Basics", "Balance", "Control", "Consistency"],
    },
    "Street Tricks": {
        "actions": ["Kickflip", "Heelflip", "Shuvit", "Grind Entry"],
        "modifiers": ["Basics", "Pop", "Catch", "Style"],
    },
    "Transition": {
        "actions": ["Drop‑In", "Pump", "Axle Stall", "Rock to Fakie"],
        "modifiers": ["Basics", "Speed", "Flow", "Commitment"],
    },
    "Rail & Ledge": {
        "actions": ["50‑50", "Boardslide", "5‑0 Grind", "Nosegrind"],
        "modifiers": ["Basics", "Lock‑In", "Balance", "Control"],
    },
    "Conditioning": {
        "actions": ["Ankle Stability", "Core Work", "Plyometrics", "Mobility"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Snowboarding": {
    "Fundamentals": {
        "actions": ["Skidded Turn", "Carved Turn", "Sideslip", "Garland"],
        "modifiers": ["Basics", "Edge Control", "Balance", "Speed"],
    },
    "Freestyle": {
        "actions": ["Ollie", "180", "Grab", "Box Slide"],
        "modifiers": ["Basics", "Pop", "Style", "Control"],
    },
    "Freeride": {
        "actions": ["Line Choice", "Tree Runs", "Steeps", "Drops"],
        "modifiers": ["Basics", "Flow", "Risk", "Control"],
    },
    "Switch Riding": {
        "actions": ["Switch Turn", "Switch Carve", "Switch Ollie", "Switch Entry"],
        "modifiers": ["Basics", "Balance", "Control", "Consistency"],
    },
    "Conditioning": {
        "actions": ["Leg Strength", "Core Stability", "Mobility", "Plyometrics"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Skiing": {
    "Fundamentals": {
        "actions": ["Snowplow Turn", "Parallel Turn", "Edge Control", "Speed Control"],
        "modifiers": ["Basics", "Balance", "Rhythm", "Confidence"],
    },
    "Carving": {
        "actions": ["Short Radius", "Medium Radius", "Long Radius", "High‑Edge Angle"],
        "modifiers": ["Basics", "Pressure", "Timing", "Flow"],
    },
    "Moguls": {
        "actions": ["Absorption", "Line Choice", "Pole Plant", "Rhythm"],
        "modifiers": ["Basics", "Control", "Speed", "Endurance"],
    },
    "Freestyle": {
        "actions": ["Jump Takeoff", "Grab", "Spin Entry", "Rail Slide"],
        "modifiers": ["Basics", "Pop", "Style", "Control"],
    },
    "Conditioning": {
        "actions": ["Leg Endurance", "Core Stability", "Balance Drills", "Plyometrics"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Climbing": {
    "Bouldering": {
        "actions": ["Overhang Problem", "Slab Problem", "Dyno", "Crimpy Problem"],
        "modifiers": ["Basics", "Power", "Technique", "Problem‑Solving"],
    },
    "Sport Climbing": {
        "actions": ["Lead Climb", "Quickdraw Clipping", "Rest Position", "Route Reading"],
        "modifiers": ["Basics", "Endurance", "Efficiency", "Commitment"],
    },
    "Technique": {
        "actions": ["Flagging", "Drop‑Knee", "Heel Hook", "Toe Hook"],
        "modifiers": ["Basics", "Body Position", "Control", "Efficiency"],
    },
    "Finger Strength": {
        "actions": ["Hangboard", "Campus Board", "Repeaters", "Max Hangs"],
        "modifiers": ["Basics", "Power", "Endurance", "Control"],
    },
    "Conditioning": {
        "actions": ["Core Training", "Antagonist Work", "Mobility", "Shoulder Stability"],
        "modifiers": ["Light", "Endurance", "Power", "Injury‑Prevention"],
    },
},
"Gymnastics": {
    "Floor": {
        "actions": ["Roundoff", "Back Handspring", "Back Tuck", "Front Tuck"],
        "modifiers": ["Basics", "Power", "Form", "Connection"],
    },
    "Bars": {
        "actions": ["Kip", "Cast Handstand", "Giant", "Release Move"],
        "modifiers": ["Basics", "Swing", "Timing", "Control"],
    },
    "Beam": {
        "actions": ["Mount", "Leap", "Turn", "Acro Skill"],
        "modifiers": ["Basics", "Balance", "Precision", "Confidence"],
    },
    "Vault": {
        "actions": ["Run‑Up", "Board Contact", "Block", "Landing"],
        "modifiers": ["Basics", "Power", "Form", "Control"],
    },
    "Conditioning": {
        "actions": ["Core Circuit", "Upper‑Body Strength", "Leg Power", "Flexibility"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Cheer": {
    "Stunting": {
        "actions": ["Liberty", "Extension", "Prep", "Basket Toss"],
        "modifiers": ["Basics", "Stability", "Timing", "Power"],
    },
    "Tumbling": {
        "actions": ["Roundoff", "Back Handspring", "Tuck", "Layout"],
        "modifiers": ["Basics", "Form", "Power", "Connection"],
    },
    "Jumps": {
        "actions": ["Toe Touch", "Herkie", "Pike", "Hurdler"],
        "modifiers": ["Basics", "Height", "Form", "Timing"],
    },
    "Dance": {
        "actions": ["Sharp Motions", "Transitions", "Formations", "Facials"],
        "modifiers": ["Basics", "Sharpness", "Synchronization", "Energy"],
    },
    "Conditioning": {
        "actions": ["Core Work", "Leg Strength", "Flexibility", "Cardio"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Canoe/Kayak": {
    "Paddling Technique": {
        "actions": ["Forward Stroke", "Sweep Stroke", "Draw Stroke", "Brace"],
        "modifiers": ["Basics", "Power", "Efficiency", "Control"],
    },
    "Boat Control": {
        "actions": ["Edging", "Turning", "Tracking", "Acceleration"],
        "modifiers": ["Basics", "Balance", "Precision", "Responsiveness"],
    },
    "Starts": {
        "actions": ["Explosive Start", "High‑Rate Start", "Acceleration Phase", "Stabilization"],
        "modifiers": ["Basics", "Power", "Timing", "Execution"],
    },
    "Endurance": {
        "actions": ["Steady Paddle", "Intervals", "Tempo Work", "Long Distance"],
        "modifiers": ["Basics", "Endurance", "Efficiency", "Pacing"],
    },
    "Conditioning": {
        "actions": ["Core Rotation", "Shoulder Strength", "Mobility", "Balance Drills"],
        "modifiers": ["Light", "Endurance", "Power", "Control"],
    },
},
"Triathlon": {
    "Swim": {
        "actions": ["Open Water Stroke", "Sighting", "Drafting", "Breathing Rhythm"],
        "modifiers": ["Basics", "Endurance", "Efficiency", "Control"],
    },
    "Bike": {
        "actions": ["Cadence Control", "Climbing", "Aero Position", "Pacing"],
        "modifiers": ["Basics", "Power", "Endurance", "Efficiency"],
    },
    "Run": {
        "actions": ["Stride Technique", "Pacing", "Cadence", "Hill Running"],
        "modifiers": ["Basics", "Endurance", "Efficiency", "Speed"],
    },
    "Transitions": {
        "actions": ["T1 Setup", "T2 Setup", "Quick Change", "Mount/Dismount"],
        "modifiers": ["Basics", "Speed", "Efficiency", "Execution"],
    },
    "Conditioning": {
        "actions": ["Brick Workout", "Intervals", "Long Endurance", "Mobility"],
        "modifiers": ["Light", "Endurance", "Power", "Control"],
    },
},
"Powerlifting": {
    "Squat": {
        "actions": ["Back Squat", "Pause Squat", "Tempo Squat", "Box Squat"],
        "modifiers": ["Basics", "Strength", "Control", "Power"],
    },
    "Bench Press": {
        "actions": ["Competition Bench", "Close Grip", "Pause Bench", "Spoto Press"],
        "modifiers": ["Basics", "Strength", "Control", "Power"],
    },
    "Deadlift": {
        "actions": ["Conventional", "Sumo", "Deficit", "Romanian"],
        "modifiers": ["Basics", "Strength", "Control", "Power"],
    },
    "Accessory Work": {
        "actions": ["Rows", "Hamstring Work", "Triceps Work", "Core Stability"],
        "modifiers": ["Basics", "Strength", "Endurance", "Balance"],
    },
    "Conditioning": {
        "actions": ["Sled Push", "Light Cardio", "Mobility", "Bracing Drills"],
        "modifiers": ["Light", "Endurance", "Control", "Recovery"],
    },
},
"Olympic Weightlifting": {
    "Snatch": {
        "actions": ["Power Snatch", "Hang Snatch", "Snatch Pull", "Overhead Squat"],
        "modifiers": ["Basics", "Speed", "Technique", "Power"],
    },
    "Clean & Jerk": {
        "actions": ["Power Clean", "Hang Clean", "Jerk", "Clean Pull"],
        "modifiers": ["Basics", "Speed", "Technique", "Power"],
    },
    "Strength Work": {
        "actions": ["Front Squat", "Back Squat", "Push Press", "Deadlift"],
        "modifiers": ["Basics", "Strength", "Control", "Power"],
    },
    "Technique Drills": {
        "actions": ["Tall Snatch", "Tall Clean", "Jerk Balance", "High Pull"],
        "modifiers": ["Basics", "Precision", "Timing", "Consistency"],
    },
    "Conditioning": {
        "actions": ["Mobility", "Core Stability", "Light Cardio", "Explosive Work"],
        "modifiers": ["Light", "Endurance", "Control", "Recovery"],
    },
},
"CrossFit": {
    "Weightlifting": {
        "actions": ["Snatch", "Clean & Jerk", "Thruster", "Deadlift"],
        "modifiers": ["Basics", "Power", "Speed", "Efficiency"],
    },
    "Gymnastics": {
        "actions": ["Pull‑Ups", "Toes‑to‑Bar", "Handstand Push‑Ups", "Muscle‑Ups"],
        "modifiers": ["Basics", "Strength", "Control", "Technique"],
    },
    "Conditioning": {
        "actions": ["Rowing", "Running", "Biking", "Double Unders"],
        "modifiers": ["Basics", "Endurance", "Speed", "Pacing"],
    },
    "Mixed Workouts": {
        "actions": ["AMRAP", "EMOM", "For Time", "Intervals"],
        "modifiers": ["Basics", "Intensity", "Strategy", "Consistency"],
    },
    "Skill Work": {
        "actions": ["Handstand Walk", "Pistols", "Rope Climb", "Kipping"],
        "modifiers": ["Basics", "Balance", "Technique", "Control"],
    },
},
"Dance": {
    "Footwork": {
        "actions": ["Basic Steps", "Direction Changes", "Turns", "Traveling Steps"],
        "modifiers": ["Basics", "Speed", "Control", "Precision"],
    },
    "Strength & Control": {
        "actions": ["Core Work", "Leg Extensions", "Balance Holds", "Isolations"],
        "modifiers": ["Basics", "Strength", "Control", "Stability"],
    },
    "Jumps & Leaps": {
        "actions": ["Straight Jump", "Split Leap", "Switch Leap", "Tuck Jump"],
        "modifiers": ["Basics", "Height", "Form", "Power"],
    },
    "Floorwork": {
        "actions": ["Rolls", "Transitions", "Slides", "Ground Phrases"],
        "modifiers": ["Basics", "Flow", "Control", "Precision"],
    },
    "Conditioning": {
        "actions": ["Flexibility", "Endurance", "Plyometrics", "Mobility"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Canoe Slalom": {
    "Paddling Technique": {
        "actions": ["Forward Stroke", "Sweep Stroke", "Draw Stroke", "Cross‑Bow Stroke"],
        "modifiers": ["Basics", "Power", "Precision", "Control"],
    },
    "Gate Navigation": {
        "actions": ["Upstream Gate", "Downstream Gate", "S‑Turn", "Offset Sequence"],
        "modifiers": ["Basics", "Timing", "Line Choice", "Responsiveness"],
    },
    "Boat Control": {
        "actions": ["Edging", "Carving", "Acceleration", "Braking"],
        "modifiers": ["Basics", "Balance", "Efficiency", "Control"],
    },
    "Starts": {
        "actions": ["Explosive Start", "High‑Rate Start", "Acceleration Phase", "Stabilization"],
        "modifiers": ["Basics", "Power", "Timing", "Execution"],
    },
    "Conditioning": {
        "actions": ["Core Rotation", "Shoulder Strength", "Mobility", "Balance Drills"],
        "modifiers": ["Light", "Endurance", "Power", "Control"],
    },
},
"Track Cycling": {
    "Speed Work": {
        "actions": ["Standing Start", "Flying 200", "Sprint Laps", "Acceleration Drill"],
        "modifiers": ["Basics", "Power", "Speed", "Explosive"],
    },
    "Endurance": {
        "actions": ["Pursuit Pace", "Tempo Laps", "Long Intervals", "Cadence Control"],
        "modifiers": ["Basics", "Endurance", "Efficiency", "Pacing"],
    },
    "Bike Handling": {
        "actions": ["Line Holding", "Banking Control", "Drafting", "Corner Entry"],
        "modifiers": ["Basics", "Balance", "Control", "Timing"],
    },
    "Starts": {
        "actions": ["Gate Start", "Standing Start", "Acceleration Phase", "Stabilization"],
        "modifiers": ["Basics", "Power", "Timing", "Execution"],
    },
    "Conditioning": {
        "actions": ["Leg Strength", "Core Stability", "Mobility", "Breath Control"],
        "modifiers": ["Light", "Endurance", "Power", "Control"],
    },
},
"Mountain Biking": {
    "Technical Riding": {
        "actions": ["Rock Garden", "Root Section", "Switchbacks", "Drops"],
        "modifiers": ["Basics", "Control", "Balance", "Confidence"],
    },
    "Descending": {
        "actions": ["Body Position", "Braking Control", "Cornering", "Line Choice"],
        "modifiers": ["Basics", "Speed", "Flow", "Stability"],
    },
    "Climbing": {
        "actions": ["Seated Climb", "Standing Climb", "Traction Control", "Switchback Climb"],
        "modifiers": ["Basics", "Power", "Pacing", "Efficiency"],
    },
    "Endurance": {
        "actions": ["Long Ride", "Intervals", "Hill Repeats", "Tempo Ride"],
        "modifiers": ["Basics", "Endurance", "Efficiency", "Pacing"],
    },
    "Conditioning": {
        "actions": ["Core Work", "Leg Strength", "Mobility", "Balance Drills"],
        "modifiers": ["Light", "Endurance", "Power", "Control"],
    },
},
"Speed Skating": {
    "Technique": {
        "actions": ["Push Technique", "Corner Entry", "Corner Exit", "Glide Control"],
        "modifiers": ["Basics", "Efficiency", "Balance", "Speed"],
    },
    "Starts": {
        "actions": ["Explosive Start", "Acceleration Phase", "Transition to Glide", "Stabilization"],
        "modifiers": ["Basics", "Power", "Timing", "Execution"],
    },
    "Endurance": {
        "actions": ["Long Intervals", "Tempo Laps", "Pacing Work", "Aerobic Sets"],
        "modifiers": ["Basics", "Endurance", "Efficiency", "Rhythm"],
    },
    "Sprint Work": {
        "actions": ["Flying Lap", "Short Sprint", "Acceleration Drill", "High‑Rate Laps"],
        "modifiers": ["Basics", "Speed", "Explosive", "Control"],
    },
    "Conditioning": {
        "actions": ["Leg Strength", "Core Stability", "Mobility", "Balance Drills"],
        "modifiers": ["Light", "Endurance", "Power", "Control"],
    },
},
"Figure Skating": {
    "Jumps": {
        "actions": ["Axel", "Lutz", "Flip", "Toe Loop"],
        "modifiers": ["Basics", "Height", "Rotation", "Landing"],
    },
    "Spins": {
        "actions": ["Sit Spin", "Camel Spin", "Layback Spin", "Combination Spin"],
        "modifiers": ["Basics", "Balance", "Control", "Consistency"],
    },
    "Footwork": {
        "actions": ["Three Turns", "Mohawks", "Choctaws", "Edge Work"],
        "modifiers": ["Basics", "Precision", "Flow", "Control"],
    },
    "Skating Skills": {
        "actions": ["Edge Quality", "Power Pulls", "Crossovers", "Glide Control"],
        "modifiers": ["Basics", "Speed", "Flow", "Balance"],
    },
    "Conditioning": {
        "actions": ["Core Strength", "Flexibility", "Plyometrics", "Balance Drills"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Parkour": {
    "Basics": {
        "actions": ["Precision Jump", "Roll", "Vault", "Wall Run"],
        "modifiers": ["Basics", "Control", "Flow", "Safety"],
    },
    "Vaults": {
        "actions": ["Kong", "Dash", "Speed Vault", "Lazy Vault"],
        "modifiers": ["Basics", "Speed", "Control", "Efficiency"],
    },
    "Climbing": {
        "actions": ["Cat Leap", "Wall Climb", "Lache", "Underbar"],
        "modifiers": ["Basics", "Grip", "Power", "Technique"],
    },
    "Freerunning": {
        "actions": ["Flip", "Spin", "Twist", "Flow Combo"],
        "modifiers": ["Basics", "Style", "Control", "Creativity"],
    },
    "Conditioning": {
        "actions": ["Plyometrics", "Grip Strength", "Core Work", "Mobility"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Diving": {
    "Approach": {
        "actions": ["Hurdle Step", "Takeoff", "Arm Swing", "Board Timing"],
        "modifiers": ["Basics", "Control", "Precision", "Power"],
    },
    "Aerial Skills": {
        "actions": ["Tuck", "Pike", "Layout", "Twist"],
        "modifiers": ["Basics", "Form", "Rotation", "Control"],
    },
    "Entries": {
        "actions": ["Vertical Entry", "Rip Entry", "Line Control", "Angle Correction"],
        "modifiers": ["Basics", "Precision", "Timing", "Cleanliness"],
    },
    "Platform Work": {
        "actions": ["Standing Dive", "Armstand", "Forward Dive", "Back Dive"],
        "modifiers": ["Basics", "Control", "Confidence", "Form"],
    },
    "Conditioning": {
        "actions": ["Core Strength", "Flexibility", "Plyometrics", "Balance"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Sailing": {
    "Boat Handling": {
        "actions": ["Tacking", "Jibing", "Trim Control", "Balance"],
        "modifiers": ["Basics", "Timing", "Efficiency", "Control"],
    },
    "Wind Reading": {
        "actions": ["Wind Shift Recognition", "Gust Control", "Sail Angle", "Course Choice"],
        "modifiers": ["Basics", "Awareness", "Strategy", "Precision"],
    },
    "Starts": {
        "actions": ["Line Positioning", "Acceleration", "Timing", "Clear Air"],
        "modifiers": ["Basics", "Strategy", "Timing", "Execution"],
    },
    "Racing Skills": {
        "actions": ["Upwind Sailing", "Downwind Sailing", "Mark Rounding", "Tactical Positioning"],
        "modifiers": ["Basics", "Strategy", "Efficiency", "Control"],
    },
    "Conditioning": {
        "actions": ["Core Strength", "Grip Work", "Mobility", "Endurance"],
        "modifiers": ["Light", "Endurance", "Power", "Control"],
    },
},
"Windsurfing": {
    "Sail Handling": {
        "actions": ["Sheet In", "Sheet Out", "Rig Steering", "Sail Pumping"],
        "modifiers": ["Basics", "Control", "Timing", "Efficiency"],
    },
    "Board Control": {
        "actions": ["Foot Steering", "Rail Pressure", "Balance Shift", "Planing Entry"],
        "modifiers": ["Basics", "Balance", "Flow", "Responsiveness"],
    },
    "Maneuvers": {
        "actions": ["Tack", "Jibe", "Carve Jibe", "Helitack"],
        "modifiers": ["Basics", "Timing", "Precision", "Control"],
    },
    "Speed Work": {
        "actions": ["Downwind Speed", "Beam Reach", "Upwind Angle", "Acceleration"],
        "modifiers": ["Basics", "Speed", "Power", "Efficiency"],
    },
    "Conditioning": {
        "actions": ["Core Strength", "Grip Work", "Mobility", "Endurance"],
        "modifiers": ["Light", "Endurance", "Power", "Control"],
    },
},
"Beach Volleyball": {
    "Serving": {
        "actions": ["Float Serve", "Topspin Serve", "Short Serve", "Deep Serve"],
        "modifiers": ["Basics", "Accuracy", "Power", "Placement"],
    },
    "Passing": {
        "actions": ["Platform Pass", "Overhand Pass", "Angle Pass", "Serve Receive"],
        "modifiers": ["Basics", "Control", "Footwork", "Consistency"],
    },
    "Setting": {
        "actions": ["Hand Set", "Bump Set", "Back Set", "Transition Set"],
        "modifiers": ["Basics", "Touch", "Accuracy", "Timing"],
    },
    "Attacking": {
        "actions": ["Cut Shot", "Line Shot", "High Roll", "Power Hit"],
        "modifiers": ["Basics", "Placement", "Timing", "Deception"],
    },
    "Defense": {
        "actions": ["Dig", "Pursuit", "Block Timing", "Reading Hitters"],
        "modifiers": ["Basics", "Reaction", "Footwork", "Awareness"],
    },
},
"Canoe Sprint": {
    "Paddling Technique": {
        "actions": ["Catch Phase", "Power Phase", "Exit Phase", "Recovery"],
        "modifiers": ["Basics", "Power", "Efficiency", "Timing"],
    },
    "Starts": {
        "actions": ["Explosive Start", "High‑Rate Start", "Acceleration", "Stabilization"],
        "modifiers": ["Basics", "Power", "Timing", "Execution"],
    },
    "Race Pace": {
        "actions": ["Tempo Work", "Race Simulation", "Stroke Rate Control", "Distance Pacing"],
        "modifiers": ["Basics", "Endurance", "Efficiency", "Consistency"],
    },
    "Boat Control": {
        "actions": ["Balance", "Tracking", "Steering", "Acceleration"],
        "modifiers": ["Basics", "Control", "Responsiveness", "Stability"],
    },
    "Conditioning": {
        "actions": ["Core Rotation", "Shoulder Strength", "Mobility", "Endurance"],
        "modifiers": ["Light", "Endurance", "Power", "Control"],
    },
},
"Beach Soccer": {
    "Ball Control": {
        "actions": ["Juggle Control", "Sand Dribble", "Scoop Pass", "Lifted Touch"],
        "modifiers": ["Basics", "Balance", "Precision", "Creativity"],
    },
    "Shooting": {
        "actions": ["Volley Shot", "Bicycle Kick", "Toe‑Poke Finish", "Chip Shot"],
        "modifiers": ["Basics", "Power", "Accuracy", "Placement"],
    },
    "Passing": {
        "actions": ["Aerial Pass", "Short Pass", "Backheel Pass", "Flick Pass"],
        "modifiers": ["Basics", "Timing", "Accuracy", "Creativity"],
    },
    "Defense": {
        "actions": ["Sand Slide", "Block", "Pressure Defense", "Interception"],
        "modifiers": ["Basics", "Timing", "Footwork", "Awareness"],
    },
    "Conditioning": {
        "actions": ["Sand Sprints", "Agility Work", "Balance Drills", "Endurance Runs"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Beach Handball": {
    "Shooting": {
        "actions": ["Spin Shot", "Flying Shot", "Jump Shot", "Underhand Shot"],
        "modifiers": ["Basics", "Accuracy", "Power", "Creativity"],
    },
    "Passing": {
        "actions": ["Quick Pass", "Overhead Pass", "Bounce Pass", "No‑Look Pass"],
        "modifiers": ["Basics", "Timing", "Speed", "Deception"],
    },
    "Defense": {
        "actions": ["Block", "Pressure Defense", "Interception", "Closeout"],
        "modifiers": ["Basics", "Timing", "Footwork", "Awareness"],
    },
    "Goalkeeping": {
        "actions": ["Kick Save", "Hand Save", "Angle Coverage", "Reaction Save"],
        "modifiers": ["Basics", "Reaction", "Positioning", "Explosive"],
    },
    "Conditioning": {
        "actions": ["Sand Sprints", "Agility", "Balance Work", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Sailboarding": {
    "Sail Technique": {
        "actions": ["Rig Steering", "Sheet Control", "Sail Pumping", "Trim Adjustment"],
        "modifiers": ["Basics", "Efficiency", "Timing", "Control"],
    },
    "Board Skills": {
        "actions": ["Planing", "Rail Pressure", "Foot Steering", "Balance Shift"],
        "modifiers": ["Basics", "Balance", "Flow", "Responsiveness"],
    },
    "Racing Skills": {
        "actions": ["Upwind Angle", "Downwind Speed", "Mark Rounding", "Starts"],
        "modifiers": ["Basics", "Strategy", "Timing", "Execution"],
    },
    "Maneuvers": {
        "actions": ["Tack", "Jibe", "Carve Jibe", "Helitack"],
        "modifiers": ["Basics", "Precision", "Timing", "Control"],
    },
    "Conditioning": {
        "actions": ["Core Strength", "Grip Work", "Mobility", "Endurance"],
        "modifiers": ["Light", "Endurance", "Power", "Control"],
    },
},
"Beach Tennis": {
    "Serving": {
        "actions": ["Flat Serve", "Kick Serve", "Slice Serve", "Deep Serve"],
        "modifiers": ["Basics", "Accuracy", "Power", "Placement"],
    },
    "Volleys": {
        "actions": ["Forehand Volley", "Backhand Volley", "Punch Volley", "Drop Volley"],
        "modifiers": ["Basics", "Timing", "Control", "Touch"],
    },
    "Smashes": {
        "actions": ["Overhead Smash", "Jump Smash", "Angle Smash", "Deep Smash"],
        "modifiers": ["Basics", "Power", "Accuracy", "Placement"],
    },
    "Defense": {
        "actions": ["Lob Defense", "Block", "Chase Down", "Counter Volley"],
        "modifiers": ["Basics", "Reaction", "Footwork", "Awareness"],
    },
    "Conditioning": {
        "actions": ["Sand Sprints", "Agility", "Balance Drills", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Beach Rugby": {
    "Running": {
        "actions": ["Acceleration", "Cut Step", "Sprint", "Angle Run"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Passing": {
        "actions": ["Spin Pass", "Pop Pass", "Offload", "Quick Pass"],
        "modifiers": ["Basics", "Accuracy", "Timing", "Distance"],
    },
    "Tackling": {
        "actions": ["Wrap Tackle", "Low Tackle", "Side Tackle", "Chase‑Down Tackle"],
        "modifiers": ["Basics", "Form", "Power", "Safety"],
    },
    "Defense": {
        "actions": ["Press Defense", "Angle Defense", "Closeout", "Interception"],
        "modifiers": ["Basics", "Timing", "Footwork", "Awareness"],
    },
    "Conditioning": {
        "actions": ["Sand Sprints", "Agility", "Balance Work", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Beach Hockey": {
    "Dribbling": {
        "actions": ["Push Dribble", "Lifted Dribble", "Pull Back", "V‑Drag"],
        "modifiers": ["Basics", "Control", "Speed", "Deception"],
    },
    "Passing": {
        "actions": ["Push Pass", "Lifted Pass", "Flick Pass", "Short Pass"],
        "modifiers": ["Basics", "Accuracy", "Timing", "Distance"],
    },
    "Shooting": {
        "actions": ["Hit", "Flick", "Lifted Shot", "Reverse Shot"],
        "modifiers": ["Basics", "Power", "Accuracy", "Placement"],
    },
    "Defense": {
        "actions": ["Block Tackle", "Jab Tackle", "Channeling", "Interception"],
        "modifiers": ["Basics", "Timing", "Footwork", "Positioning"],
    },
    "Conditioning": {
        "actions": ["Sand Sprints", "Agility", "Balance Drills", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Beach Athletics": {
    "Sprinting": {
        "actions": ["Acceleration", "Top Speed", "Starts", "Stride Technique"],
        "modifiers": ["Basics", "Power", "Speed", "Efficiency"],
    },
    "Jumping": {
        "actions": ["Long Jump", "High Jump", "Triple Jump", "Approach Run"],
        "modifiers": ["Basics", "Technique", "Power", "Timing"],
    },
    "Throwing": {
        "actions": ["Shot Put", "Discus", "Javelin", "Hammer Throw"],
        "modifiers": ["Basics", "Power", "Form", "Release"],
    },
    "Endurance": {
        "actions": ["Sand Run", "Intervals", "Tempo Work", "Long Distance"],
        "modifiers": ["Basics", "Endurance", "Efficiency", "Rhythm"],
    },
    "Conditioning": {
        "actions": ["Sand Sprints", "Agility", "Balance Drills", "Plyometrics"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Kabaddi": {
    "Raiding": {
        "actions": ["Hand Touch", "Toe Touch", "Kick", "Dubki"],
        "modifiers": ["Basics", "Agility", "Timing", "Deception"],
    },
    "Defense": {
        "actions": ["Chain Tackle", "Ankle Hold", "Thigh Hold", "Block"],
        "modifiers": ["Basics", "Strength", "Coordination", "Timing"],
    },
    "Footwork": {
        "actions": ["Lateral Step", "Crossover Step", "Retreat Step", "Angle Entry"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Strategy": {
        "actions": ["Raid Planning", "Corner Setup", "Cover Coordination", "Bonus Line Play"],
        "modifiers": ["Basics", "Awareness", "Decision‑Making", "Execution"],
    },
    "Conditioning": {
        "actions": ["Sprint Intervals", "Wrestling Drills", "Core Work", "Agility Ladder"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Sepak Takraw": {
    "Serving": {
        "actions": ["Inside Kick Serve", "Toe Serve", "Jump Serve", "Spin Serve"],
        "modifiers": ["Basics", "Accuracy", "Power", "Placement"],
    },
    "Striking": {
        "actions": ["Spike", "Roll Spike", "Sunback Spike", "Header"],
        "modifiers": ["Basics", "Timing", "Power", "Deception"],
    },
    "Passing": {
        "actions": ["Inside Kick Pass", "Knee Pass", "Chest Pass", "Head Pass"],
        "modifiers": ["Basics", "Control", "Accuracy", "Consistency"],
    },
    "Defense": {
        "actions": ["Block", "Dive Save", "Foot Save", "Reaction Defense"],
        "modifiers": ["Basics", "Timing", "Footwork", "Awareness"],
    },
    "Conditioning": {
        "actions": ["Jump Training", "Flexibility", "Core Strength", "Balance Work"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Sumo": {
    "Tachiai (Start)": {
        "actions": ["Charge", "Hand Placement", "Low Entry", "Explosive Push"],
        "modifiers": ["Basics", "Power", "Timing", "Aggression"],
    },
    "Grappling": {
        "actions": ["Belt Grip", "Inside Grip", "Outside Grip", "Lift"],
        "modifiers": ["Basics", "Strength", "Control", "Positioning"],
    },
    "Footwork": {
        "actions": ["Shuffling Step", "Lateral Step", "Retreat Step", "Angle Entry"],
        "modifiers": ["Basics", "Balance", "Stability", "Control"],
    },
    "Throws": {
        "actions": ["Overarm Throw", "Underarm Throw", "Leg Trip", "Pivot Throw"],
        "modifiers": ["Basics", "Timing", "Technique", "Power"],
    },
    "Conditioning": {
        "actions": ["Leg Strength", "Core Work", "Pushing Drills", "Balance Training"],
        "modifiers": ["Light", "Endurance", "Power", "Control"],
    },
},
"Kendo": {
    "Strikes": {
        "actions": ["Men Strike", "Kote Strike", "Do Strike", "Tsuki"],
        "modifiers": ["Basics", "Timing", "Precision", "Speed"],
    },
    "Footwork": {
        "actions": ["Okuri‑Ashi", "Fumikomi", "Ayumi‑Ashi", "Retreat Step"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
    "Defense": {
        "actions": ["Parry", "Block", "Distance Control", "Counterstrike"],
        "modifiers": ["Basics", "Timing", "Awareness", "Positioning"],
    },
    "Kata": {
        "actions": ["Ipponme", "Nihonme", "Sanbonme", "Yonhonme"],
        "modifiers": ["Basics", "Form", "Precision", "Flow"],
    },
    "Conditioning": {
        "actions": ["Footwork Drills", "Suburi", "Core Work", "Endurance"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Capoeira": {
    "Basics": {
        "actions": ["Ginga", "Esquiva", "Cocorinha", "Negativa"],
        "modifiers": ["Basics", "Flow", "Balance", "Control"],
    },
    "Kicks": {
        "actions": ["Meia Lua", "Armada", "Martelo", "Queixada"],
        "modifiers": ["Basics", "Speed", "Power", "Precision"],
    },
    "Acrobatics": {
        "actions": ["Aú", "Macaco", "Bananeira", "Ponte"],
        "modifiers": ["Basics", "Explosive", "Balance", "Creativity"],
    },
    "Ground Movement": {
        "actions": ["Rolê", "Rasteira", "Troca de Base", "Entrada"],
        "modifiers": ["Basics", "Flow", "Timing", "Deception"],
    },
    "Conditioning": {
        "actions": ["Core Work", "Flexibility", "Endurance", "Rhythm Drills"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Sanda": {
    "Striking": {
        "actions": ["Straight Punch", "Round Kick", "Side Kick", "Spinning Kick"],
        "modifiers": ["Basics", "Speed", "Power", "Accuracy"],
    },
    "Throws": {
        "actions": ["Hip Throw", "Leg Sweep", "Shoulder Throw", "Catch‑and‑Dump"],
        "modifiers": ["Basics", "Timing", "Technique", "Control"],
    },
    "Defense": {
        "actions": ["Parry", "Slip", "Block", "Footwork Escape"],
        "modifiers": ["Basics", "Reaction", "Positioning", "Awareness"],
    },
    "Clinch": {
        "actions": ["Body Lock", "Trip Setup", "Lift Attempt", "Break Off"],
        "modifiers": ["Basics", "Strength", "Timing", "Control"],
    },
    "Conditioning": {
        "actions": ["Pad Rounds", "Sparring", "Sprint Work", "Core Training"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Savate": {
    "Kicks": {
        "actions": ["Fouetté", "Chassé", "Revers", "Coup de Pied Bas"],
        "modifiers": ["Basics", "Accuracy", "Speed", "Control"],
    },
    "Punches": {
        "actions": ["Direct", "Crochet", "Uppercut", "Cross"],
        "modifiers": ["Basics", "Timing", "Power", "Precision"],
    },
    "Footwork": {
        "actions": ["Advance", "Retreat", "Lateral Step", "Pivot"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
    "Defense": {
        "actions": ["Parry", "Slip", "Block", "Distance Control"],
        "modifiers": ["Basics", "Timing", "Awareness", "Positioning"],
    },
    "Conditioning": {
        "actions": ["Shadowboxing", "Bag Work", "Agility Drills", "Core Work"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Lethwei": {
    "Striking": {
        "actions": ["Straight Punch", "Elbow Strike", "Knee Strike", "Headbutt"],
        "modifiers": ["Basics", "Power", "Timing", "Aggression"],
    },
    "Clinch": {
        "actions": ["Neck Tie", "Frame Control", "Knee Entry", "Turn Off"],
        "modifiers": ["Basics", "Strength", "Positioning", "Control"],
    },
    "Defense": {
        "actions": ["Slip", "Parry", "Cover", "Footwork Escape"],
        "modifiers": ["Basics", "Awareness", "Timing", "Reaction"],
    },
    "Combinations": {
        "actions": ["Punch‑Elbow", "Kick‑Punch", "Knee‑Elbow", "Headbutt Entry"],
        "modifiers": ["Basics", "Flow", "Speed", "Power"],
    },
    "Conditioning": {
        "actions": ["Bag Work", "Clinching Rounds", "Roadwork", "Shin Conditioning"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Pencak Silat": {
    "Striking": {
        "actions": ["Punch", "Elbow", "Front Kick", "Round Kick"],
        "modifiers": ["Basics", "Speed", "Power", "Precision"],
    },
    "Takedowns": {
        "actions": ["Leg Sweep", "Shoulder Throw", "Foot Trap", "Body Drop"],
        "modifiers": ["Basics", "Timing", "Technique", "Control"],
    },
    "Forms": {
        "actions": ["Jurus 1", "Jurus 2", "Jurus 3", "Jurus 4"],
        "modifiers": ["Basics", "Flow", "Precision", "Application"],
    },
    "Defense": {
        "actions": ["Parry", "Redirection", "Angle Step", "Block"],
        "modifiers": ["Basics", "Timing", "Awareness", "Positioning"],
    },
    "Conditioning": {
        "actions": ["Flexibility", "Core Work", "Shadow Drills", "Footwork Patterns"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Kurash": {
    "Throws": {
        "actions": ["Hip Throw", "Shoulder Throw", "Leg Sweep", "Lift Throw"],
        "modifiers": ["Basics", "Timing", "Technique", "Power"],
    },
    "Grip Fighting": {
        "actions": ["Standard Grip", "Cross Grip", "Belt Grip", "Break Grip"],
        "modifiers": ["Basics", "Control", "Dominance", "Entry"],
    },
    "Defense": {
        "actions": ["Sprawl", "Hip Turn", "Footwork Escape", "Counter Throw"],
        "modifiers": ["Basics", "Timing", "Balance", "Awareness"],
    },
    "Footwork": {
        "actions": ["Shuffle Step", "Angle Step", "Retreat Step", "Entry Step"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
    "Conditioning": {
        "actions": ["Grip Strength", "Core Work", "Explosive Drills", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Power"],
    },
},
"Hurling": {
    "Striking": {
        "actions": ["Ground Strike", "Air Strike", "Flick", "Volley"],
        "modifiers": ["Basics", "Power", "Accuracy", "Timing"],
    },
    "Ball Control": {
        "actions": ["Solo Run", "Hand Pass", "Lift", "Catch"],
        "modifiers": ["Basics", "Control", "Speed", "Consistency"],
    },
    "Defense": {
        "actions": ["Block", "Hook", "Shoulder Challenge", "Interception"],
        "modifiers": ["Basics", "Timing", "Footwork", "Awareness"],
    },
    "Footwork": {
        "actions": ["Acceleration", "Cut Step", "Angle Run", "Retreat Step"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Conditioning": {
        "actions": ["Sprint Work", "Agility", "Stick Drills", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Gaelic Football": {
    "Kicking": {
        "actions": ["Punt Kick", "Drop Kick", "Chip Kick", "Long Kick"],
        "modifiers": ["Basics", "Accuracy", "Power", "Placement"],
    },
    "Hand Passing": {
        "actions": ["Fist Pass", "Pop Pass", "Quick Pass", "Overhand Pass"],
        "modifiers": ["Basics", "Timing", "Control", "Speed"],
    },
    "Running": {
        "actions": ["Solo Run", "Bounce Run", "Cut Step", "Acceleration"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Defense": {
        "actions": ["Block", "Tackle", "Pressure Defense", "Interception"],
        "modifiers": ["Basics", "Timing", "Footwork", "Awareness"],
    },
    "Conditioning": {
        "actions": ["Sprint Intervals", "Agility", "Endurance Runs", "Core Work"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Futsal": {
    "Ball Control": {
        "actions": ["Sole Control", "Roll Over", "Drag Back", "Quick Touch"],
        "modifiers": ["Basics", "Speed", "Precision", "Creativity"],
    },
    "Passing": {
        "actions": ["Wall Pass", "Diagonal Pass", "One‑Touch Pass", "Lifted Pass"],
        "modifiers": ["Basics", "Timing", "Accuracy", "Speed"],
    },
    "Shooting": {
        "actions": ["Toe‑Poke Shot", "Instep Shot", "Volley", "Chip Shot"],
        "modifiers": ["Basics", "Power", "Accuracy", "Placement"],
    },
    "Defense": {
        "actions": ["Press", "Block", "Interception", "Jockey"],
        "modifiers": ["Basics", "Timing", "Footwork", "Awareness"],
    },
    "Conditioning": {
        "actions": ["Short Sprints", "Agility", "Ball‑Control Drills", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Netball": {
    "Passing": {
        "actions": ["Chest Pass", "Bounce Pass", "Overhead Pass", "Shoulder Pass"],
        "modifiers": ["Basics", "Accuracy", "Timing", "Speed"],
    },
    "Shooting": {
        "actions": ["Set Shot", "Step Shot", "Turn Shot", "High Arc Shot"],
        "modifiers": ["Basics", "Accuracy", "Balance", "Consistency"],
    },
    "Footwork": {
        "actions": ["Pivot", "Landing Control", "Change of Direction", "Acceleration"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
    "Defense": {
        "actions": ["Marking", "Intercept", "Deflection", "Block"],
        "modifiers": ["Basics", "Timing", "Awareness", "Positioning"],
    },
    "Conditioning": {
        "actions": ["Agility", "Endurance", "Core Work", "Speed Drills"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Kho Kho": {
    "Chasing": {
        "actions": ["Pole Turn", "Sudden Sprint", "Direction Change", "Dive Tag"],
        "modifiers": ["Basics", "Speed", "Agility", "Timing"],
    },
    "Dodging": {
        "actions": ["Zig‑Zag Run", "Sudden Stop", "Roll Escape", "Angle Change"],
        "modifiers": ["Basics", "Balance", "Awareness", "Control"],
    },
    "Pole Skills": {
        "actions": ["Pole Turn", "Pole Push", "Pole Acceleration", "Pole Exit"],
        "modifiers": ["Basics", "Technique", "Speed", "Flow"],
    },
    "Strategy": {
        "actions": ["Chain Coordination", "Runner Rotation", "Trap Setup", "Escape Routes"],
        "modifiers": ["Basics", "Awareness", "Decision‑Making", "Execution"],
    },
    "Conditioning": {
        "actions": ["Sprint Intervals", "Agility Ladder", "Core Work", "Balance Drills"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Kabaddi (Circle Style)": {
    "Raiding": {
        "actions": ["Toe Touch", "Hand Touch", "Kick", "Circle Sweep"],
        "modifiers": ["Basics", "Agility", "Timing", "Deception"],
    },
    "Defense": {
        "actions": ["Chain Hold", "Ankle Hold", "Block", "Corner Trap"],
        "modifiers": ["Basics", "Strength", "Coordination", "Timing"],
    },
    "Movement": {
        "actions": ["Circle Run", "Angle Entry", "Retreat Step", "Cut Step"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Strategy": {
        "actions": ["Raid Planning", "Corner Setup", "Cover Coordination", "Circle Control"],
        "modifiers": ["Basics", "Awareness", "Decision‑Making", "Execution"],
    },
    "Conditioning": {
        "actions": ["Sprint Work", "Wrestling Drills", "Core Work", "Agility"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Naginata": {
    "Strikes": {
        "actions": ["Men Strike", "Sune Strike", "Do Strike", "Tsuki"],
        "modifiers": ["Basics", "Timing", "Precision", "Speed"],
    },
    "Footwork": {
        "actions": ["Okuri‑Ashi", "Ayumi‑Ashi", "Retreat Step", "Angle Step"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
    "Defense": {
        "actions": ["Parry", "Block", "Distance Control", "Counterstrike"],
        "modifiers": ["Basics", "Timing", "Awareness", "Positioning"],
    },
    "Kata": {
        "actions": ["Shikake‑Oji", "Basic Kata", "Partner Kata", "Flow Kata"],
        "modifiers": ["Basics", "Form", "Precision", "Flow"],
    },
    "Conditioning": {
        "actions": ["Suburi", "Footwork Drills", "Core Work", "Endurance"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Sambo": {
    "Throws": {
        "actions": ["Hip Throw", "Leg Reap", "Shoulder Throw", "Lift Throw"],
        "modifiers": ["Basics", "Timing", "Technique", "Power"],
    },
    "Grappling": {
        "actions": ["Arm Lock", "Leg Lock", "Pin", "Transition"],
        "modifiers": ["Basics", "Control", "Pressure", "Positioning"],
    },
    "Striking (Combat Sambo)": {
        "actions": ["Jab", "Cross", "Round Kick", "Knee"],
        "modifiers": ["Basics", "Speed", "Power", "Accuracy"],
    },
    "Defense": {
        "actions": ["Sprawl", "Grip Break", "Footwork Escape", "Counter Throw"],
        "modifiers": ["Basics", "Timing", "Balance", "Awareness"],
    },
    "Conditioning": {
        "actions": ["Grip Strength", "Explosive Drills", "Core Work", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Power"],
    },
},
"Muay Boran": {
    "Striking": {
        "actions": ["Elbow Slash", "Hammer Fist", "Spear Hand", "Diagonal Kick"],
        "modifiers": ["Basics", "Power", "Precision", "Timing"],
    },
    "Clinch": {
        "actions": ["Neck Tie", "Arm Control", "Knee Entry", "Turn Off"],
        "modifiers": ["Basics", "Strength", "Positioning", "Control"],
    },
    "Throws": {
        "actions": ["Hip Throw", "Leg Sweep", "Shoulder Throw", "Dump"],
        "modifiers": ["Basics", "Timing", "Technique", "Power"],
    },
    "Defense": {
        "actions": ["Parry", "Cover", "Slip", "Angle Step"],
        "modifiers": ["Basics", "Awareness", "Timing", "Reaction"],
    },
    "Conditioning": {
        "actions": ["Shin Conditioning", "Pad Rounds", "Core Work", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Orienteering": {
    "Navigation": {
        "actions": ["Map Reading", "Compass Bearing", "Route Choice", "Attack Point"],
        "modifiers": ["Basics", "Speed", "Accuracy", "Decision‑Making"],
    },
    "Running": {
        "actions": ["Trail Run", "Off‑Trail Run", "Hill Run", "Interval Run"],
        "modifiers": ["Basics", "Endurance", "Speed", "Efficiency"],
    },
    "Control Skills": {
        "actions": ["Control Approach", "Punching", "Relocation", "Error Recovery"],
        "modifiers": ["Basics", "Awareness", "Calmness", "Precision"],
    },
    "Terrain Handling": {
        "actions": ["Rocky Ground", "Dense Forest", "Marsh Crossing", "Steep Slopes"],
        "modifiers": ["Basics", "Balance", "Caution", "Aggression"],
    },
    "Conditioning": {
        "actions": ["Hill Repeats", "Trail Intervals", "Core Work", "Mobility"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Biathlon": {
    "Skiing": {
        "actions": ["Skate Technique", "Classic Technique", "Climbing", "Descending"],
        "modifiers": ["Basics", "Endurance", "Efficiency", "Power"],
    },
    "Shooting": {
        "actions": ["Prone Shooting", "Standing Shooting", "Breath Control", "Trigger Control"],
        "modifiers": ["Basics", "Accuracy", "Calmness", "Speed"],
    },
    "Transitions": {
        "actions": ["Range Entry", "Range Exit", "Ski‑to‑Shoot", "Shoot‑to‑Ski"],
        "modifiers": ["Basics", "Timing", "Efficiency", "Composure"],
    },
    "Pacing": {
        "actions": ["Lap Pacing", "Surge Control", "Final Lap Push", "Energy Management"],
        "modifiers": ["Basics", "Endurance", "Strategy", "Discipline"],
    },
    "Conditioning": {
        "actions": ["Interval Skiing", "Roller Skiing", "Strength Work", "Cardio"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Cross‑Country Skiing": {
    "Technique": {
        "actions": ["Diagonal Stride", "Double Pole", "Skate Technique", "Kick Double Pole"],
        "modifiers": ["Basics", "Efficiency", "Power", "Rhythm"],
    },
    "Climbing": {
        "actions": ["Herringbone", "V1 Skate", "V2 Skate", "Steep Climb"],
        "modifiers": ["Basics", "Endurance", "Power", "Pacing"],
    },
    "Descending": {
        "actions": ["Snowplow", "Parallel Descent", "Cornering", "Speed Control"],
        "modifiers": ["Basics", "Balance", "Control", "Confidence"],
    },
    "Pacing": {
        "actions": ["Tempo Ski", "Intervals", "Long Distance", "Race Simulation"],
        "modifiers": ["Basics", "Endurance", "Strategy", "Consistency"],
    },
    "Conditioning": {
        "actions": ["Roller Skiing", "Strength Work", "Cardio", "Core Training"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Strongman": {
    "Carries": {
        "actions": ["Farmer's Walk", "Yoke Carry", "Sandbag Carry", "Husafell Stone"],
        "modifiers": ["Basics", "Strength", "Endurance", "Grip"],
    },
    "Lifts": {
        "actions": ["Atlas Stone", "Log Press", "Axle Deadlift", "Block Press"],
        "modifiers": ["Basics", "Power", "Technique", "Control"],
    },
    "Pulls": {
        "actions": ["Truck Pull", "Sled Drag", "Rope Pull", "Harness Pull"],
        "modifiers": ["Basics", "Strength", "Endurance", "Explosive"],
    },
    "Medleys": {
        "actions": ["Carry‑to‑Load", "Press Medley", "Carry Medley", "Mixed Event"],
        "modifiers": ["Basics", "Pacing", "Strategy", "Grit"],
    },
    "Conditioning": {
        "actions": ["Event Practice", "Cardio", "Core Work", "Mobility"],
        "modifiers": ["Light", "Endurance", "Explosive", "Recovery"],
    },
},
"Trail Running": {
    "Running": {
        "actions": ["Uphill Run", "Downhill Run", "Technical Terrain", "Flat Trail"],
        "modifiers": ["Basics", "Endurance", "Control", "Speed"],
    },
    "Pacing": {
        "actions": ["Easy Pace", "Tempo", "Race Pace", "Surge Control"],
        "modifiers": ["Basics", "Strategy", "Endurance", "Discipline"],
    },
    "Technical Skills": {
        "actions": ["Rocky Terrain", "Roots", "Mud", "Stream Crossing"],
        "modifiers": ["Basics", "Balance", "Caution", "Confidence"],
    },
    "Nutrition & Hydration": {
        "actions": ["Fuel Timing", "Hydration Plan", "Electrolyte Management", "Gut Training"],
        "modifiers": ["Basics", "Consistency", "Awareness", "Adaptation"],
    },
    "Conditioning": {
        "actions": ["Hill Repeats", "Long Runs", "Strength Work", "Mobility"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Dragon Boat": {
    "Paddling": {
        "actions": ["Catch", "Drive", "Exit", "Recovery"],
        "modifiers": ["Basics", "Power", "Timing", "Efficiency"],
    },
    "Synchronization": {
        "actions": ["Stroke Rate Match", "Timing with Drummer", "Start Sequence", "Finish Push"],
        "modifiers": ["Basics", "Coordination", "Discipline", "Focus"],
    },
    "Starts": {
        "actions": ["High‑Rate Start", "Power Start", "Build Phase", "Settle Pace"],
        "modifiers": ["Basics", "Power", "Timing", "Execution"],
    },
    "Race Pacing": {
        "actions": ["Mid‑Race Rhythm", "Surge", "Final Sprint", "Energy Management"],
        "modifiers": ["Basics", "Endurance", "Strategy", "Consistency"],
    },
    "Conditioning": {
        "actions": ["Core Rotation", "Shoulder Strength", "Cardio", "Mobility"],
        "modifiers": ["Light", "Endurance", "Power", "Control"],
    },
},
"Iaido": {
    "Drawing": {
        "actions": ["Nukitsuke", "Seiza Draw", "Standing Draw", "Quick Draw"],
        "modifiers": ["Basics", "Precision", "Timing", "Calmness"],
    },
    "Cutting": {
        "actions": ["Kesa Giri", "Do Giri", "Tsuki", "Horizontal Cut"],
        "modifiers": ["Basics", "Control", "Accuracy", "Flow"],
    },
    "Footwork": {
        "actions": ["Sliding Step", "Retreat Step", "Angle Step", "Advance"],
        "modifiers": ["Basics", "Balance", "Control", "Speed"],
    },
    "Kata": {
        "actions": ["Mae", "Ushiro", "Ukenagashi", "Tsuka Ate"],
        "modifiers": ["Basics", "Form", "Flow", "Consistency"],
    },
    "Conditioning": {
        "actions": ["Core Work", "Grip Strength", "Mobility", "Breath Control"],
        "modifiers": ["Light", "Endurance", "Control", "Precision"],
    },
},
"Kenjutsu": {
    "Strikes": {
        "actions": ["Men", "Kote", "Do", "Tsuki"],
        "modifiers": ["Basics", "Power", "Precision", "Timing"],
    },
    "Footwork": {
        "actions": ["Ayumi Ashi", "Okuri Ashi", "Retreat", "Angle Entry"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
    "Defense": {
        "actions": ["Parry", "Block", "Deflect", "Distance Control"],
        "modifiers": ["Basics", "Timing", "Awareness", "Positioning"],
    },
    "Kata": {
        "actions": ["Basic Kata", "Partner Kata", "Flow Kata", "Advanced Kata"],
        "modifiers": ["Basics", "Form", "Flow", "Consistency"],
    },
    "Conditioning": {
        "actions": ["Suburi", "Core Work", "Grip Strength", "Mobility"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Wushu": {
    "Basics": {
        "actions": ["Stances", "Punches", "Kicks", "Blocks"],
        "modifiers": ["Basics", "Form", "Balance", "Control"],
    },
    "Forms": {
        "actions": ["Changquan", "Nanquan", "Taolu", "Weapon Forms"],
        "modifiers": ["Basics", "Flow", "Precision", "Expression"],
    },
    "Sparring": {
        "actions": ["Kick Entry", "Punch Combo", "Sweep", "Counter"],
        "modifiers": ["Basics", "Speed", "Timing", "Power"],
    },
    "Weapons": {
        "actions": ["Staff", "Broadsword", "Straight Sword", "Spear"],
        "modifiers": ["Basics", "Control", "Precision", "Flow"],
    },
    "Conditioning": {
        "actions": ["Flexibility", "Strength Work", "Stance Training", "Explosive Drills"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Taekkyeon": {
    "Footwork": {
        "actions": ["Step Rhythm", "Angle Step", "Retreat Step", "Flow Step"],
        "modifiers": ["Basics", "Balance", "Control", "Speed"],
    },
    "Kicks": {
        "actions": ["Low Kick", "High Kick", "Sweep Kick", "Jump Kick"],
        "modifiers": ["Basics", "Timing", "Power", "Precision"],
    },
    "Hand Techniques": {
        "actions": ["Palm Strike", "Backfist", "Parry", "Push"],
        "modifiers": ["Basics", "Speed", "Accuracy", "Control"],
    },
    "Defense": {
        "actions": ["Slip", "Angle Move", "Block", "Redirect"],
        "modifiers": ["Basics", "Awareness", "Timing", "Positioning"],
    },
    "Conditioning": {
        "actions": ["Flexibility", "Balance Work", "Core Training", "Endurance"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Kumdo": {
    "Strikes": {
        "actions": ["Men", "Kote", "Do", "Tsuki"],
        "modifiers": ["Basics", "Speed", "Precision", "Power"],
    },
    "Footwork": {
        "actions": ["Advance", "Retreat", "Slide Step", "Angle Step"],
        "modifiers": ["Basics", "Balance", "Control", "Speed"],
    },
    "Defense": {
        "actions": ["Block", "Parry", "Distance Control", "Counter"],
        "modifiers": ["Basics", "Timing", "Awareness", "Positioning"],
    },
    "Kata": {
        "actions": ["Basic Kata", "Partner Kata", "Flow Kata", "Advanced Kata"],
        "modifiers": ["Basics", "Form", "Flow", "Consistency"],
    },
    "Conditioning": {
        "actions": ["Suburi", "Core Work", "Grip Strength", "Mobility"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Shinkendo": {
    "Cutting": {
        "actions": ["Kesa Giri", "Do Giri", "Jodan Cut", "Horizontal Cut"],
        "modifiers": ["Basics", "Precision", "Power", "Control"],
    },
    "Footwork": {
        "actions": ["Advance", "Retreat", "Slide Step", "Angle Entry"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
    "Forms": {
        "actions": ["Basic Kata", "Partner Kata", "Flow Kata", "Advanced Kata"],
        "modifiers": ["Basics", "Form", "Flow", "Consistency"],
    },
    "Defense": {
        "actions": ["Parry", "Block", "Deflect", "Distance Control"],
        "modifiers": ["Basics", "Timing", "Awareness", "Positioning"],
    },
    "Conditioning": {
        "actions": ["Grip Strength", "Core Work", "Mobility", "Breath Control"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Battojutsu": {
    "Drawing": {
        "actions": ["Quick Draw", "Seated Draw", "Standing Draw", "Angle Draw"],
        "modifiers": ["Basics", "Precision", "Timing", "Calmness"],
    },
    "Cutting": {
        "actions": ["Vertical Cut", "Diagonal Cut", "Horizontal Cut", "Thrust"],
        "modifiers": ["Basics", "Control", "Accuracy", "Power"],
    },
    "Footwork": {
        "actions": ["Slide Step", "Retreat Step", "Angle Step", "Advance"],
        "modifiers": ["Basics", "Balance", "Control", "Speed"],
    },
    "Kata": {
        "actions": ["Basic Kata", "Partner Kata", "Flow Kata", "Advanced Kata"],
        "modifiers": ["Basics", "Form", "Flow", "Consistency"],
    },
    "Conditioning": {
        "actions": ["Core Work", "Grip Strength", "Mobility", "Breath Control"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Kushti": {
    "Grappling": {
        "actions": ["Body Lock", "Leg Grab", "Hip Throw", "Lift and Dump"],
        "modifiers": ["Basics", "Strength", "Control", "Timing"],
    },
    "Groundwork": {
        "actions": ["Pin Control", "Turnover", "Bridge Escape", "Neck Control"],
        "modifiers": ["Basics", "Pressure", "Balance", "Technique"],
    },
    "Stance & Movement": {
        "actions": ["Low Stance", "Circle Step", "Push‑Pull", "Entry Step"],
        "modifiers": ["Basics", "Balance", "Control", "Speed"],
    },
    "Striking (Traditional)": {
        "actions": ["Palm Strike", "Shoulder Bump", "Forearm Push", "Head Pressure"],
        "modifiers": ["Basics", "Power", "Timing", "Control"],
    },
    "Conditioning": {
        "actions": ["Dands", "Bethaks", "Rope Climb", "Sand Wrestling"],
        "modifiers": ["Light", "Endurance", "Explosive", "Strength"],
    },
},
"Shooting": {
    "Rifle": {
        "actions": ["Prone Shot", "Standing Shot", "Kneeling Shot", "Breath Control"],
        "modifiers": ["Basics", "Accuracy", "Calmness", "Consistency"],
    },
    "Pistol": {
        "actions": ["One‑Hand Shot", "Rapid Fire", "Trigger Control", "Sight Alignment"],
        "modifiers": ["Basics", "Precision", "Timing", "Control"],
    },
    "Shotgun": {
        "actions": ["Trap", "Skeet", "Sporting Clays", "Lead Timing"],
        "modifiers": ["Basics", "Reaction", "Tracking", "Timing"],
    },
    "Mental Skills": {
        "actions": ["Focus Drill", "Routine Setup", "Pressure Simulation", "Visualization"],
        "modifiers": ["Basics", "Calmness", "Consistency", "Confidence"],
    },
    "Conditioning": {
        "actions": ["Core Stability", "Breath Training", "Grip Strength", "Balance"],
        "modifiers": ["Light", "Endurance", "Control", "Precision"],
    },
},
"Horseback Archery": {
    "Riding": {
        "actions": ["Canter Control", "Gallop Control", "Balance Hold", "Posture"],
        "modifiers": ["Basics", "Balance", "Control", "Confidence"],
    },
    "Shooting": {
        "actions": ["Forward Shot", "Side Shot", "Back Shot", "Quick Draw"],
        "modifiers": ["Basics", "Accuracy", "Timing", "Flow"],
    },
    "Transitions": {
        "actions": ["Draw at Speed", "Release at Speed", "Re‑Nock", "Target Switch"],
        "modifiers": ["Basics", "Timing", "Efficiency", "Calmness"],
    },
    "Course Skills": {
        "actions": ["Straight Track", "Turn Track", "Multiple Targets", "Distance Variation"],
        "modifiers": ["Basics", "Awareness", "Strategy", "Consistency"],
    },
    "Conditioning": {
        "actions": ["Core Work", "Grip Strength", "Balance Drills", "Mobility"],
        "modifiers": ["Light", "Endurance", "Control", "Precision"],
    },
},
"Kyudo": {
    "Shooting": {
        "actions": ["Daisan", "Kai", "Hanare", "Zanshin"],
        "modifiers": ["Basics", "Calmness", "Precision", "Flow"],
    },
    "Form": {
        "actions": ["Posture", "Foot Placement", "Bow Raise", "Draw Sequence"],
        "modifiers": ["Basics", "Balance", "Control", "Consistency"],
    },
    "Breathing": {
        "actions": ["Slow Breath", "Timing Breath", "Release Breath", "Focus Breath"],
        "modifiers": ["Basics", "Calmness", "Control", "Awareness"],
    },
    "Kata": {
        "actions": ["Hassetsu", "Dojo Etiquette", "Ceremonial Shot", "Group Shot"],
        "modifiers": ["Basics", "Form", "Flow", "Precision"],
    },
    "Conditioning": {
        "actions": ["Shoulder Strength", "Core Work", "Mobility", "Breath Training"],
        "modifiers": ["Light", "Endurance", "Control", "Precision"],
    },
},
"Amateur Sumo": {
    "Tachiai": {
        "actions": ["Explosive Start", "Low Charge", "Hand Placement", "Drive"],
        "modifiers": ["Basics", "Power", "Timing", "Aggression"],
    },
    "Grappling": {
        "actions": ["Belt Grip", "Inside Grip", "Outside Grip", "Lift"],
        "modifiers": ["Basics", "Strength", "Control", "Positioning"],
    },
    "Throws": {
        "actions": ["Overarm Throw", "Underarm Throw", "Leg Trip", "Pivot Throw"],
        "modifiers": ["Basics", "Timing", "Technique", "Power"],
    },
    "Ring Control": {
        "actions": ["Edge Defense", "Push Out", "Circle Control", "Angle Entry"],
        "modifiers": ["Basics", "Awareness", "Balance", "Strategy"],
    },
    "Conditioning": {
        "actions": ["Leg Strength", "Core Work", "Pushing Drills", "Balance Training"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Sport Fencing": {
    "Footwork": {
        "actions": ["Advance", "Retreat", "Lunge", "Recovery"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Attacks": {
        "actions": ["Direct Attack", "Feint Attack", "Compound Attack", "Counterattack"],
        "modifiers": ["Basics", "Timing", "Precision", "Speed"],
    },
    "Defense": {
        "actions": ["Parry", "Riposte", "Distance Control", "Blade Deflection"],
        "modifiers": ["Basics", "Timing", "Awareness", "Positioning"],
    },
    "Tactics": {
        "actions": ["Tempo Control", "Distance Play", "Setup Actions", "Pattern Breaking"],
        "modifiers": ["Basics", "Strategy", "Awareness", "Execution"],
    },
    "Conditioning": {
        "actions": ["Agility", "Leg Strength", "Core Work", "Explosive Steps"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"HEMA": {
    "Strikes": {
        "actions": ["Oberhau", "Unterhau", "Zwerchhau", "Mittelhau"],
        "modifiers": ["Basics", "Power", "Precision", "Timing"],
    },
    "Guards": {
        "actions": ["Vom Tag", "Pflug", "Ochs", "Alber"],
        "modifiers": ["Basics", "Control", "Balance", "Readiness"],
    },
    "Footwork": {
        "actions": ["Passing Step", "Gather Step", "Lunge", "Retreat"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
    "Defense": {
        "actions": ["Parry", "Bind", "Winden", "Countercut"],
        "modifiers": ["Basics", "Timing", "Awareness", "Positioning"],
    },
    "Conditioning": {
        "actions": ["Grip Strength", "Core Work", "Mobility", "Endurance"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Kickboxing (International)": {
    "Striking": {
        "actions": ["Jab", "Cross", "Round Kick", "Low Kick"],
        "modifiers": ["Basics", "Speed", "Power", "Accuracy"],
    },
    "Combinations": {
        "actions": ["1‑2‑Low Kick", "Jab‑Cross‑Hook", "Kick‑Punch Combo", "Punch‑Kick Combo"],
        "modifiers": ["Basics", "Flow", "Timing", "Control"],
    },
    "Defense": {
        "actions": ["Slip", "Block", "Check", "Footwork Escape"],
        "modifiers": ["Basics", "Awareness", "Timing", "Positioning"],
    },
    "Clinching": {
        "actions": ["Neck Tie", "Frame Control", "Knee Entry", "Break Off"],
        "modifiers": ["Basics", "Strength", "Control", "Timing"],
    },
    "Conditioning": {
        "actions": ["Pad Rounds", "Bag Work", "Sprints", "Core Work"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Sabre Fencing": {
    "Attacks": {
        "actions": ["Cut to Head", "Cut to Arm", "Cut to Body", "Feint Attack"],
        "modifiers": ["Basics", "Speed", "Timing", "Precision"],
    },
    "Defense": {
        "actions": ["Parry 3", "Parry 4", "Parry 5", "Countercut"],
        "modifiers": ["Basics", "Timing", "Awareness", "Positioning"],
    },
    "Footwork": {
        "actions": ["Advance", "Retreat", "Lunge", "Flunge"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
    "Tactics": {
        "actions": ["Distance Play", "Tempo Control", "Setup Actions", "Counteroffense"],
        "modifiers": ["Basics", "Strategy", "Awareness", "Execution"],
    },
    "Conditioning": {
        "actions": ["Agility", "Leg Strength", "Core Work", "Explosive Steps"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Foil Fencing": {
    "Attacks": {
        "actions": ["Direct Attack", "Feint Attack", "Compound Attack", "Remise"],
        "modifiers": ["Basics", "Timing", "Precision", "Speed"],
    },
    "Defense": {
        "actions": ["Parry 4", "Parry 6", "Riposte", "Counterparry"],
        "modifiers": ["Basics", "Timing", "Awareness", "Positioning"],
    },
    "Footwork": {
        "actions": ["Advance", "Retreat", "Lunge", "Recovery"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
    "Tactics": {
        "actions": ["Right‑of‑Way Play", "Distance Control", "Setup Actions", "Pattern Breaking"],
        "modifiers": ["Basics", "Strategy", "Awareness", "Execution"],
    },
    "Conditioning": {
        "actions": ["Agility", "Leg Strength", "Core Work", "Explosive Steps"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Kali": {
    "Striking": {
        "actions": ["Angle 1", "Angle 2", "Angle 3", "Angle 4"],
        "modifiers": ["Basics", "Speed", "Precision", "Power"],
    },
    "Footwork": {
        "actions": ["Triangle Step", "Diamond Step", "Lateral Step", "Retreat"],
        "modifiers": ["Basics", "Balance", "Control", "Speed"],
    },
    "Defense": {
        "actions": ["Block", "Deflect", "Parry", "Check Hand"],
        "modifiers": ["Basics", "Timing", "Awareness", "Positioning"],
    },
    "Disarms": {
        "actions": ["Strip", "Lock", "Trap", "Break"],
        "modifiers": ["Basics", "Technique", "Control", "Timing"],
    },
    "Conditioning": {
        "actions": ["Grip Strength", "Core Work", "Mobility", "Endurance"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Krav Maga": {
    "Striking": {
        "actions": ["Straight Punch", "Palm Strike", "Elbow", "Knee"],
        "modifiers": ["Basics", "Power", "Speed", "Accuracy"],
    },
    "Defense": {
        "actions": ["360 Defense", "Inside Defense", "Outside Defense", "Redirect"],
        "modifiers": ["Basics", "Timing", "Awareness", "Positioning"],
    },
    "Grappling": {
        "actions": ["Clinching", "Takedown Defense", "Escape", "Control"],
        "modifiers": ["Basics", "Strength", "Technique", "Timing"],
    },
    "Scenario Training": {
        "actions": ["Multiple Attackers", "Weapon Defense", "Ground Escape", "Pressure Drills"],
        "modifiers": ["Basics", "Awareness", "Calmness", "Execution"],
    },
    "Conditioning": {
        "actions": ["Pad Rounds", "Sprints", "Core Work", "Strength Work"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Aikido": {
    "Throws": {
        "actions": ["Irimi Nage", "Shiho Nage", "Kote Gaeshi", "Tenchi Nage"],
        "modifiers": ["Basics", "Flow", "Timing", "Control"],
    },
    "Joint Locks": {
        "actions": ["Nikyo", "Sankyo", "Yonkyo", "Ude Garami"],
        "modifiers": ["Basics", "Precision", "Control", "Calmness"],
    },
    "Footwork": {
        "actions": ["Tenkan", "Irimi", "Pivot Step", "Angle Step"],
        "modifiers": ["Basics", "Balance", "Flow", "Control"],
    },
    "Ukemi": {
        "actions": ["Forward Roll", "Backward Roll", "Breakfall", "Soft Landing"],
        "modifiers": ["Basics", "Safety", "Control", "Confidence"],
    },
    "Conditioning": {
        "actions": ["Flexibility", "Core Work", "Breath Training", "Mobility"],
        "modifiers": ["Light", "Endurance", "Control", "Precision"],
    },
},
"Nguni Stick Fighting": {
    "Striking": {
        "actions": ["High Strike", "Low Strike", "Side Strike", "Overhead Strike"],
        "modifiers": ["Basics", "Speed", "Power", "Precision"],
    },
    "Defense": {
        "actions": ["Block High", "Block Low", "Deflect", "Angle Guard"],
        "modifiers": ["Basics", "Timing", "Awareness", "Control"],
    },
    "Footwork": {
        "actions": ["Advance", "Retreat", "Side Step", "Circle Step"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
    "Tactics": {
        "actions": ["Feint", "Distance Play", "Counterstrike", "Setup Actions"],
        "modifiers": ["Basics", "Strategy", "Awareness", "Execution"],
    },
    "Conditioning": {
        "actions": ["Grip Strength", "Core Work", "Agility", "Endurance"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Dambe": {
    "Striking": {
        "actions": ["Spear Punch", "Hammer Punch", "Guard Hand Strike", "Body Shot"],
        "modifiers": ["Basics", "Power", "Speed", "Accuracy"],
    },
    "Defense": {
        "actions": ["Guard Hand Block", "Slip", "Lean Back", "Footwork Escape"],
        "modifiers": ["Basics", "Timing", "Awareness", "Control"],
    },
    "Footwork": {
        "actions": ["Shuffle Step", "Angle Step", "Retreat Step", "Advance"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
    "Clinch": {
        "actions": ["Frame", "Push Off", "Control Arm", "Break"],
        "modifiers": ["Basics", "Strength", "Timing", "Control"],
    },
    "Conditioning": {
        "actions": ["Bag Work", "Roadwork", "Core Work", "Strength Drills"],
        "modifiers": ["Light", "Endurance", "Explosive", "Power"],
    },
},
"Laamb": {
    "Grappling": {
        "actions": ["Body Lock", "Leg Grab", "Hip Throw", "Lift and Dump"],
        "modifiers": ["Basics", "Strength", "Control", "Timing"],
    },
    "Striking (Traditional)": {
        "actions": ["Palm Strike", "Slap", "Forearm Strike", "Shoulder Bump"],
        "modifiers": ["Basics", "Power", "Timing", "Accuracy"],
    },
    "Footwork": {
        "actions": ["Circle Step", "Advance", "Retreat", "Angle Entry"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
    "Defense": {
        "actions": ["Sprawl", "Frame", "Hip Turn", "Counter Throw"],
        "modifiers": ["Basics", "Awareness", "Timing", "Positioning"],
    },
    "Conditioning": {
        "actions": ["Sand Wrestling", "Sprints", "Strength Work", "Core Training"],
        "modifiers": ["Light", "Endurance", "Explosive", "Power"],
    },
},
"Capoeira Regional": {
    "Basics": {
        "actions": ["Ginga", "Esquiva", "Negativa", "Cocorinha"],
        "modifiers": ["Basics", "Flow", "Balance", "Control"],
    },
    "Kicks": {
        "actions": ["Meia Lua", "Armada", "Martelo", "Queixada"],
        "modifiers": ["Basics", "Speed", "Power", "Precision"],
    },
    "Acrobatics": {
        "actions": ["Aú", "Macaco", "Bananeira", "Ponte"],
        "modifiers": ["Basics", "Explosive", "Balance", "Creativity"],
    },
    "Ground Movement": {
        "actions": ["Rolê", "Rasteira", "Troca de Base", "Entrada"],
        "modifiers": ["Basics", "Flow", "Timing", "Deception"],
    },
    "Conditioning": {
        "actions": ["Core Work", "Flexibility", "Endurance", "Rhythm Drills"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Capoeira Angola": {
    "Basics": {
        "actions": ["Ginga", "Esquiva", "Negativa", "Cocorinha"],
        "modifiers": ["Basics", "Flow", "Balance", "Control"],
    },
    "Kicks": {
        "actions": ["Meia Lua", "Armada", "Bênção", "Rabo de Arraia"],
        "modifiers": ["Basics", "Timing", "Power", "Precision"],
    },
    "Ground Movement": {
        "actions": ["Rolê", "Rasteira", "Entrada", "Troca de Base"],
        "modifiers": ["Basics", "Flow", "Timing", "Creativity"],
    },
    "Music & Rhythm": {
        "actions": ["Berimbau Rhythm", "Clapping", "Call‑and‑Response", "Song Flow"],
        "modifiers": ["Basics", "Timing", "Expression", "Control"],
    },
    "Conditioning": {
        "actions": ["Flexibility", "Core Work", "Balance Drills", "Endurance"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Kabaddi (Indoor)": {
    "Raiding": {
        "actions": ["Toe Touch", "Hand Touch", "Kick", "Dubki"],
        "modifiers": ["Basics", "Agility", "Timing", "Deception"],
    },
    "Defense": {
        "actions": ["Chain Tackle", "Ankle Hold", "Thigh Hold", "Block"],
        "modifiers": ["Basics", "Strength", "Coordination", "Timing"],
    },
    "Footwork": {
        "actions": ["Lateral Step", "Crossover Step", "Retreat Step", "Angle Entry"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Strategy": {
        "actions": ["Raid Planning", "Corner Setup", "Cover Coordination", "Bonus Line Play"],
        "modifiers": ["Basics", "Awareness", "Decision‑Making", "Execution"],
    },
    "Conditioning": {
        "actions": ["Sprint Intervals", "Wrestling Drills", "Core Work", "Agility Ladder"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Sepak Raga": {
    "Ball Control": {
        "actions": ["Inside Kick", "Outside Kick", "Knee Control", "Chest Control"],
        "modifiers": ["Basics", "Balance", "Precision", "Creativity"],
    },
    "Passing": {
        "actions": ["Inside Pass", "Lifted Pass", "Back Pass", "Quick Pass"],
        "modifiers": ["Basics", "Timing", "Accuracy", "Speed"],
    },
    "Striking": {
        "actions": ["High Kick", "Volley Kick", "Spin Kick", "Jump Kick"],
        "modifiers": ["Basics", "Power", "Timing", "Deception"],
    },
    "Defense": {
        "actions": ["Block", "Dive Save", "Foot Save", "Reaction Defense"],
        "modifiers": ["Basics", "Timing", "Footwork", "Awareness"],
    },
    "Conditioning": {
        "actions": ["Jump Training", "Flexibility", "Core Strength", "Balance Work"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Fantasia": {
    "Riding": {
        "actions": ["Group Gallop", "Line Formation", "Acceleration", "Posture Control"],
        "modifiers": ["Basics", "Balance", "Control", "Confidence"],
    },
    "Synchronization": {
        "actions": ["Group Start", "Group Stop", "Timing Match", "Formation Hold"],
        "modifiers": ["Basics", "Coordination", "Discipline", "Focus"],
    },
    "Rifle Technique": {
        "actions": ["Lift Rifle", "Aim Upward", "Synchronized Shot", "Lower Rifle"],
        "modifiers": ["Basics", "Timing", "Precision", "Control"],
    },
    "Horse Handling": {
        "actions": ["Rein Control", "Leg Pressure", "Speed Adjustment", "Calm Handling"],
        "modifiers": ["Basics", "Awareness", "Control", "Responsiveness"],
    },
    "Conditioning": {
        "actions": ["Core Work", "Leg Strength", "Balance Drills", "Mobility"],
        "modifiers": ["Light", "Endurance", "Control", "Stability"],
    },
},
"Buzkashi": {
    "Riding": {
        "actions": ["Gallop Control", "Sharp Turn", "Acceleration", "Crowd Navigation"],
        "modifiers": ["Basics", "Balance", "Control", "Confidence"],
    },
    "Grappling": {
        "actions": ["Carcass Grab", "Lift Attempt", "Hold Control", "Rip Away"],
        "modifiers": ["Basics", "Strength", "Grip", "Technique"],
    },
    "Positioning": {
        "actions": ["Block Opponent", "Angle Entry", "Shielding", "Break Through"],
        "modifiers": ["Basics", "Awareness", "Timing", "Strategy"],
    },
    "Team Play": {
        "actions": ["Assist Ride", "Cover Rider", "Zone Control", "Pass Off"],
        "modifiers": ["Basics", "Coordination", "Timing", "Execution"],
    },
    "Conditioning": {
        "actions": ["Grip Strength", "Core Work", "Leg Strength", "Endurance"],
        "modifiers": ["Light", "Endurance", "Power", "Control"],
    },
},
"Kurash": {
    "Throws": {
        "actions": ["Hip Throw", "Shoulder Throw", "Leg Sweep", "Lift Throw"],
        "modifiers": ["Basics", "Timing", "Technique", "Power"],
    },
    "Grip Fighting": {
        "actions": ["Standard Grip", "Cross Grip", "Belt Grip", "Grip Break"],
        "modifiers": ["Basics", "Control", "Dominance", "Entry"],
    },
    "Defense": {
        "actions": ["Sprawl", "Hip Turn", "Footwork Escape", "Counter Throw"],
        "modifiers": ["Basics", "Timing", "Balance", "Awareness"],
    },
    "Footwork": {
        "actions": ["Shuffle Step", "Angle Step", "Retreat Step", "Entry Step"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
    "Conditioning": {
        "actions": ["Grip Strength", "Core Work", "Explosive Drills", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Power"],
    },
},
"Mongolian Wrestling": {
    "Grappling": {
        "actions": ["Chest Lock", "Belt Grip", "Leg Hook", "Lift and Turn"],
        "modifiers": ["Basics", "Strength", "Control", "Technique"],
    },
    "Footwork": {
        "actions": ["Circle Step", "Advance", "Retreat", "Angle Entry"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
    "Throws": {
        "actions": ["Leg Trip", "Hip Throw", "Shoulder Throw", "Sweep"],
        "modifiers": ["Basics", "Timing", "Technique", "Power"],
    },
    "Defense": {
        "actions": ["Sprawl", "Hip Turn", "Frame", "Counter Throw"],
        "modifiers": ["Basics", "Awareness", "Timing", "Positioning"],
    },
    "Conditioning": {
        "actions": ["Sand Wrestling", "Strength Work", "Core Training", "Endurance"],
        "modifiers": ["Light", "Endurance", "Explosive", "Power"],
    },
},
"Kok Boru": {
    "Riding": {
        "actions": ["Gallop Control", "Sharp Turn", "Acceleration", "Crowd Navigation"],
        "modifiers": ["Basics", "Balance", "Control", "Confidence"],
    },
    "Grappling": {
        "actions": ["Carcass Grab", "Lift", "Hold Control", "Rip Away"],
        "modifiers": ["Basics", "Strength", "Grip", "Technique"],
    },
    "Scoring": {
        "actions": ["Goal Entry", "Angle Approach", "Break Through", "Quick Turn"],
        "modifiers": ["Basics", "Timing", "Strategy", "Execution"],
    },
    "Team Play": {
        "actions": ["Block Opponent", "Cover Rider", "Zone Control", "Pass Off"],
        "modifiers": ["Basics", "Coordination", "Timing", "Awareness"],
    },
    "Conditioning": {
        "actions": ["Grip Strength", "Core Work", "Leg Strength", "Endurance"],
        "modifiers": ["Light", "Endurance", "Power", "Control"],
    },
},
"Pato": {
    "Riding": {
        "actions": ["Gallop Control", "Sharp Turn", "Acceleration", "Posture"],
        "modifiers": ["Basics", "Balance", "Control", "Confidence"],
    },
    "Ball Handling": {
        "actions": ["Pick Up", "Pass", "Catch", "Shoot"],
        "modifiers": ["Basics", "Accuracy", "Timing", "Control"],
    },
    "Positioning": {
        "actions": ["Angle Entry", "Zone Control", "Break Through", "Support Ride"],
        "modifiers": ["Basics", "Awareness", "Strategy", "Execution"],
    },
    "Defense": {
        "actions": ["Block", "Intercept", "Pressure Ride", "Disrupt Pass"],
        "modifiers": ["Basics", "Timing", "Control", "Awareness"],
    },
    "Conditioning": {
        "actions": ["Core Work", "Grip Strength", "Balance Drills", "Endurance"],
        "modifiers": ["Light", "Endurance", "Control", "Stability"],
    },
},
"Jai Alai": {
    "Serving": {
        "actions": ["Power Serve", "Angle Serve", "Deep Serve", "Low Serve"],
        "modifiers": ["Basics", "Accuracy", "Power", "Placement"],
    },
    "Striking": {
        "actions": ["Forehand Scoop", "Backhand Scoop", "Volley", "Rebound Shot"],
        "modifiers": ["Basics", "Speed", "Timing", "Control"],
    },
    "Defense": {
        "actions": ["Wall Read", "Rebound Control", "Footwork Escape", "Angle Defense"],
        "modifiers": ["Basics", "Awareness", "Timing", "Positioning"],
    },
    "Footwork": {
        "actions": ["Lateral Step", "Crossover Step", "Retreat Step", "Acceleration"],
        "modifiers": ["Basics", "Balance", "Speed", "Control"],
    },
    "Conditioning": {
        "actions": ["Core Work", "Grip Strength", "Agility", "Endurance"],
        "modifiers": ["Light", "Endurance", "Explosive", "Control"],
    },
},
"Camogie": {
    "Striking": {
        "actions": ["Ground Strike", "Air Strike", "Flick", "Volley"],
        "modifiers": ["Basics", "Power", "Accuracy", "Timing"],
    },
    "Ball Control": {
        "actions": ["Solo Run", "Hand Pass", "Lift", "Catch"],
        "modifiers": ["Basics", "Control", "Speed", "Consistency"],
    },
    "Defense": {
        "actions": ["Block", "Hook", "Shoulder Challenge", "Interception"],
        "modifiers": ["Basics", "Timing", "Footwork", "Awareness"],
    },
    "Footwork": {
        "actions": ["Acceleration", "Cut Step", "Angle Run", "Retreat Step"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Conditioning": {
        "actions": ["Sprint Work", "Agility", "Stick Drills", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Shinty": {
    "Striking": {
        "actions": ["Drive", "Flick", "Volley", "Ground Hit"],
        "modifiers": ["Basics", "Power", "Accuracy", "Timing"],
    },
    "Ball Control": {
        "actions": ["Dribble", "Lift", "Catch", "Tap Control"],
        "modifiers": ["Basics", "Control", "Speed", "Consistency"],
    },
    "Defense": {
        "actions": ["Block", "Tackle", "Interception", "Pressure"],
        "modifiers": ["Basics", "Timing", "Footwork", "Awareness"],
    },
    "Footwork": {
        "actions": ["Acceleration", "Cut Step", "Angle Run", "Retreat Step"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Conditioning": {
        "actions": ["Sprint Work", "Agility", "Stick Drills", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Bandy": {
    "Skating": {
        "actions": ["Forward Skate", "Backward Skate", "Crossover", "Stop"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Stick Handling": {
        "actions": ["Dribble", "Lift Pass", "Tap Control", "Quick Pass"],
        "modifiers": ["Basics", "Precision", "Speed", "Consistency"],
    },
    "Shooting": {
        "actions": ["Slap Shot", "Wrist Shot", "Backhand Shot", "One‑Timer"],
        "modifiers": ["Basics", "Power", "Accuracy", "Placement"],
    },
    "Defense": {
        "actions": ["Block", "Stick Lift", "Interception", "Body Position"],
        "modifiers": ["Basics", "Timing", "Awareness", "Footwork"],
    },
    "Conditioning": {
        "actions": ["Skating Intervals", "Agility", "Core Work", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Floorball": {
    "Stick Handling": {
        "actions": ["Dribble", "Toe Drag", "Lift Move", "Quick Pass"],
        "modifiers": ["Basics", "Speed", "Precision", "Control"],
    },
    "Shooting": {
        "actions": ["Wrist Shot", "Slap Shot", "Backhand Shot", "One‑Timer"],
        "modifiers": ["Basics", "Power", "Accuracy", "Placement"],
    },
    "Defense": {
        "actions": ["Block", "Stick Lift", "Interception", "Pressure"],
        "modifiers": ["Basics", "Timing", "Awareness", "Footwork"],
    },
    "Movement": {
        "actions": ["Acceleration", "Cut Step", "Angle Run", "Retreat Step"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Conditioning": {
        "actions": ["Sprint Work", "Agility", "Stick Drills", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Korfball": {
    "Passing": {
        "actions": ["Chest Pass", "Bounce Pass", "Overhead Pass", "Quick Pass"],
        "modifiers": ["Basics", "Accuracy", "Timing", "Speed"],
    },
    "Shooting": {
        "actions": ["Set Shot", "Running Shot", "Fade Shot", "Long Shot"],
        "modifiers": ["Basics", "Accuracy", "Balance", "Consistency"],
    },
    "Movement": {
        "actions": ["Cut", "Screen", "Acceleration", "Direction Change"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Defense": {
        "actions": ["Marking", "Interception", "Block", "Pressure"],
        "modifiers": ["Basics", "Timing", "Awareness", "Positioning"],
    },
    "Conditioning": {
        "actions": ["Agility", "Endurance", "Core Work", "Speed Drills"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Petanque": {
    "Throwing": {
        "actions": ["Pointing", "Lobbing", "Rolling Shot", "High Arc Shot"],
        "modifiers": ["Basics", "Accuracy", "Touch", "Control"],
    },
    "Shooting": {
        "actions": ["Direct Hit", "Soft Shot", "Power Shot", "Bounce Shot"],
        "modifiers": ["Basics", "Precision", "Timing", "Consistency"],
    },
    "Strategy": {
        "actions": ["Placement", "Blocking", "Opening Lines", "Endgame Play"],
        "modifiers": ["Basics", "Awareness", "Decision‑Making", "Execution"],
    },
    "Footwork": {
        "actions": ["Stable Stance", "Pivot", "Step Throw", "Balance Hold"],
        "modifiers": ["Basics", "Balance", "Control", "Consistency"],
    },
    "Conditioning": {
        "actions": ["Grip Work", "Core Stability", "Mobility", "Focus Drills"],
        "modifiers": ["Light", "Endurance", "Control", "Precision"],
    },
},
"Boccia": {
    "Throwing": {
        "actions": ["Underhand Throw", "Overhand Throw", "Bounce Throw", "Soft Placement"],
        "modifiers": ["Basics", "Accuracy", "Touch", "Control"],
    },
    "Strategy": {
        "actions": ["Blocking", "Jack Placement", "Angle Play", "Endgame Setup"],
        "modifiers": ["Basics", "Awareness", "Decision‑Making", "Execution"],
    },
    "Positioning": {
        "actions": ["Chair Alignment", "Angle Setup", "Distance Control", "Stability"],
        "modifiers": ["Basics", "Balance", "Control", "Consistency"],
    },
    "Defense": {
        "actions": ["Displacement Shot", "Counter Placement", "Pressure Shot", "Line Control"],
        "modifiers": ["Basics", "Timing", "Precision", "Awareness"],
    },
    "Conditioning": {
        "actions": ["Grip Strength", "Core Stability", "Mobility", "Focus Drills"],
        "modifiers": ["Light", "Endurance", "Control", "Precision"],
    },
},
"Tejo": {
    "Throwing": {
        "actions": ["Straight Throw", "High Arc Throw", "Spin Throw", "Power Throw"],
        "modifiers": ["Basics", "Accuracy", "Touch", "Control"],
    },
    "Targeting": {
        "actions": ["Mecha Hit", "Bocín Hit", "Block Shot", "Angle Shot"],
        "modifiers": ["Basics", "Precision", "Timing", "Consistency"],
    },
    "Strategy": {
        "actions": ["Placement", "Blocking", "Opening Lines", "Endgame Play"],
        "modifiers": ["Basics", "Awareness", "Decision‑Making", "Execution"],
    },
    "Footwork": {
        "actions": ["Stable Stance", "Step Throw", "Pivot", "Balance Hold"],
        "modifiers": ["Basics", "Balance", "Control", "Consistency"],
    },
    "Conditioning": {
        "actions": ["Grip Work", "Core Stability", "Mobility", "Focus Drills"],
        "modifiers": ["Light", "Endurance", "Control", "Precision"],
    },
},
"Australian Rules Football": {
    "Kicking": {
        "actions": ["Drop Punt", "Torpedo Punt", "Snap Kick", "Banana Kick"],
        "modifiers": ["Basics", "Accuracy", "Power", "Placement"],
    },
    "Handballing": {
        "actions": ["Standard Handball", "Quick Handball", "Under Pressure", "Long Handball"],
        "modifiers": ["Basics", "Timing", "Speed", "Control"],
    },
    "Marking": {
        "actions": ["Chest Mark", "Overhead Mark", "Contested Mark", "Specky"],
        "modifiers": ["Basics", "Timing", "Balance", "Reach"],
    },
    "Tackling": {
        "actions": ["Wrap Tackle", "Run‑Down Tackle", "Hip‑and‑Shoulder", "Smother"],
        "modifiers": ["Basics", "Power", "Timing", "Safety"],
    },
    "Conditioning": {
        "actions": ["Sprint Intervals", "Agility", "Endurance Runs", "Core Work"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Rugby League": {
    "Running": {
        "actions": ["Acceleration", "Cut Step", "Angle Run", "Line Break"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Passing": {
        "actions": ["Spin Pass", "Short Ball", "Cut‑Out Pass", "Offload"],
        "modifiers": ["Basics", "Accuracy", "Timing", "Distance"],
    },
    "Tackling": {
        "actions": ["Front‑On Tackle", "Side Tackle", "Wrestle Tackle", "Strip Attempt"],
        "modifiers": ["Basics", "Form", "Power", "Safety"],
    },
    "Kicking": {
        "actions": ["Grubber Kick", "Bomb Kick", "Chip Kick", "40/20 Kick"],
        "modifiers": ["Basics", "Placement", "Power", "Timing"],
    },
    "Conditioning": {
        "actions": ["Sprint Work", "Agility", "Strength Work", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Rugby Sevens": {
    "Running": {
        "actions": ["Acceleration", "Top Speed", "Cut Step", "Angle Run"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Passing": {
        "actions": ["Quick Pass", "Spin Pass", "Long Pass", "Offload"],
        "modifiers": ["Basics", "Accuracy", "Timing", "Speed"],
    },
    "Tackling": {
        "actions": ["Low Tackle", "Side Tackle", "Chase‑Down Tackle", "Cover Tackle"],
        "modifiers": ["Basics", "Form", "Power", "Safety"],
    },
    "Kicking": {
        "actions": ["Chip Kick", "Grubber Kick", "Restart Kick", "Punt"],
        "modifiers": ["Basics", "Placement", "Power", "Timing"],
    },
    "Conditioning": {
        "actions": ["Sprint Intervals", "Agility", "Strength Work", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Gaelic Hurling": {
    "Striking": {
        "actions": ["Ground Strike", "Air Strike", "Volley", "Flick"],
        "modifiers": ["Basics", "Power", "Accuracy", "Timing"],
    },
    "Ball Control": {
        "actions": ["Solo Run", "Lift", "Catch", "Hand Pass"],
        "modifiers": ["Basics", "Control", "Speed", "Consistency"],
    },
    "Defense": {
        "actions": ["Block", "Hook", "Interception", "Shoulder Challenge"],
        "modifiers": ["Basics", "Timing", "Footwork", "Awareness"],
    },
    "Footwork": {
        "actions": ["Acceleration", "Cut Step", "Angle Run", "Retreat Step"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Conditioning": {
        "actions": ["Sprint Work", "Agility", "Stick Drills", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Netball Fast5": {
    "Passing": {
        "actions": ["Quick Pass", "Bounce Pass", "Overhead Pass", "Fast Break Pass"],
        "modifiers": ["Basics", "Accuracy", "Timing", "Speed"],
    },
    "Shooting": {
        "actions": ["1‑Point Shot", "3‑Point Shot", "Long Shot", "Quick Release"],
        "modifiers": ["Basics", "Accuracy", "Balance", "Consistency"],
    },
    "Movement": {
        "actions": ["Cut", "Screen", "Acceleration", "Direction Change"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Defense": {
        "actions": ["Marking", "Intercept", "Deflection", "Pressure"],
        "modifiers": ["Basics", "Timing", "Awareness", "Positioning"],
    },
    "Conditioning": {
        "actions": ["Agility", "Endurance", "Core Work", "Speed Drills"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Canadian Football": {
    "Passing": {
        "actions": ["Quick Pass", "Deep Pass", "Rollout Pass", "Screen Pass"],
        "modifiers": ["Basics", "Accuracy", "Timing", "Power"],
    },
    "Running": {
        "actions": ["Inside Run", "Outside Run", "Cutback", "Sweep"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Defense": {
        "actions": ["Press Coverage", "Zone Coverage", "Blitz", "Interception"],
        "modifiers": ["Basics", "Timing", "Awareness", "Positioning"],
    },
    "Special Teams": {
        "actions": ["Kick Return", "Punt Return", "Field Goal", "Kickoff"],
        "modifiers": ["Basics", "Speed", "Power", "Accuracy"],
    },
    "Conditioning": {
        "actions": ["Sprint Work", "Agility", "Strength Work", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Box Lacrosse": {
    "Stick Handling": {
        "actions": ["Cradle", "Quick Stick", "Toe Drag", "Behind‑the‑Back"],
        "modifiers": ["Basics", "Speed", "Precision", "Control"],
    },
    "Shooting": {
        "actions": ["Overhand Shot", "Sidearm Shot", "Underhand Shot", "BTB Shot"],
        "modifiers": ["Basics", "Power", "Accuracy", "Placement"],
    },
    "Defense": {
        "actions": ["Cross‑Check", "Stick Lift", "Body Position", "Interception"],
        "modifiers": ["Basics", "Timing", "Awareness", "Footwork"],
    },
    "Movement": {
        "actions": ["Pick and Roll", "Cut", "Acceleration", "Direction Change"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Conditioning": {
        "actions": ["Sprint Work", "Agility", "Stick Drills", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
"Field Lacrosse": {
    "Stick Handling": {
        "actions": ["Cradle", "Quick Stick", "Toe Drag", "Split Dodge"],
        "modifiers": ["Basics", "Speed", "Precision", "Control"],
    },
    "Shooting": {
        "actions": ["Overhand Shot", "Sidearm Shot", "Underhand Shot", "Jump Shot"],
        "modifiers": ["Basics", "Power", "Accuracy", "Placement"],
    },
    "Defense": {
        "actions": ["Stick Check", "Body Position", "Slide", "Interception"],
        "modifiers": ["Basics", "Timing", "Awareness", "Footwork"],
    },
    "Movement": {
        "actions": ["Cut", "Roll Dodge", "Acceleration", "Direction Change"],
        "modifiers": ["Basics", "Speed", "Balance", "Control"],
    },
    "Conditioning": {
        "actions": ["Sprint Work", "Agility", "Stick Drills", "Endurance"],
        "modifiers": ["Light", "High‑Intensity", "Endurance", "Explosive"],
    },
},
# ---------------------------------------------------------


@router.get("/")
def get_sports(token: str = Depends(oauth2_scheme)):
    return {"sports": get_sport_list()}


@router.get("/{sport}/skills")
def get_skills(sport: str, token: str = Depends(oauth2_scheme)):
    if sport not in SPORTS:
        raise HTTPException(status_code=404, detail="Sport not found")
    return {"skills": list(SPORTS[sport].keys())}


@router.get("/{sport}/{category}/levels")
def get_levels(sport: str, category: str, token: str = Depends(oauth2_scheme)):
    if sport not in SPORTS:
        raise HTTPException(status_code=404, detail="Sport not found")
    if category not in SPORTS[sport]:
        raise HTTPException(status_code=404, detail="Category not found")

    # You don’t have levels in your generator, so we return a default
    return {"levels": ["Any"]}


@router.get("/{sport}/{category}/{level}/drills")
def get_drill(sport: str, category: str, level: str, token: str = Depends(oauth2_scheme)):
    if sport not in SPORTS:
        raise HTTPException(status_code=404, detail="Sport not found")
    if category not in SPORTS[sport]:
        raise HTTPException(status_code=404, detail="Category not found")

    drill = generate_drill(sport)
    return {"drill": drill}

# Timeline planner: turns the screenplay + measured dialogue durations into shots with absolute times,
# per-scene character staging (positions, moves, poses) and camera instructions.
import os, json, math, re
import config
from script_data import SCENES, CHARACTERS
from chars import BASE_POSES, POSES, expr_for

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL = config.EPISODE_DIR          # the episode (output) folder
DOCS = os.path.join(FINAL, "docs")
FPS = 24
LEAD = 0.12          # silence before a line starts inside its shot
FADE = 0.6           # fade in/out at scene boundaries
WALK_SPEED = 115.0   # cm / s
RIDE_SPEED = 230.0
SHOT_SCALE = 0.9     # non-dialogue shot durations are scaled by this
OFF_X = 1000.0


def load_manifest():
    p = os.path.join(FINAL, "audio", "dialogue", "manifest.json")
    if os.path.exists(p):
        return json.load(open(p))
    return {}


def est_dur(text):
    n = len(re.sub(r"[\s។៖!?.,…'\"“”—\-]", "", text))
    return max(0.8, n / 13.0)


class Stage:
    """Tracks every character's staging over absolute time."""
    def __init__(self):
        self.moves = {}      # ch -> [(t0, t1, (x0,d0), (x1,d1))]
        self.pos = {}
        self.visible = {}
        self.base = {}
        self.gest = {}
        self.busy_until = {}

    def _init(self, ch):
        for dct, v in ((self.moves, []), (self.gest, []), (self.visible, []), (self.base, [])):
            dct.setdefault(ch, list(v))
        self.busy_until.setdefault(ch, 0.0)

    def set(self, ch, t, xy=None, vis=None, base=None):
        self._init(ch)
        if xy is not None:
            self.pos[ch] = xy
            self.moves[ch].append((t, t, xy, xy))
        if vis is not None:
            self.visible[ch].append((t, vis))
        if base is not None:
            self.base[ch].append((t, base))

    def walk(self, ch, t, to, then_vis=None, base_after=None):
        self._init(ch)
        t = max(t, self.busy_until[ch])
        x0, d0 = self.pos.get(ch, (OFF_X, 0.1))
        x1, d1 = to
        cur_base = self.base_at(ch, t)[0]
        riding = cur_base == "cyclo"
        dist = math.hypot(x1 - x0, (d1 - d0) * 200)
        dur = min(4.0 if riding else 3.4, max(1.0, dist / (RIDE_SPEED if riding else WALK_SPEED)))
        self.moves[ch].append((t, t + dur, (x0, d0), (x1, d1)))
        self.pos[ch] = (x1, d1)
        if not riding:
            self.base[ch].append((t, "walk"))
        self.busy_until[ch] = t + dur
        if then_vis is not None:
            self.visible[ch].append((t + dur, then_vis))
        if not riding:
            self.base[ch].append((t + dur, base_after or "stand"))
        return t + dur

    # --- queries -------------------------------------------------------------------------------
    def at(self, ch, t):
        mv = self.moves.get(ch) or []
        x, d = OFF_X, 0.1
        moving = False
        for (t0, t1, a, b) in mv:
            if t >= t1:
                x, d = b
            elif t >= t0:
                u = (t - t0) / max(t1 - t0, 1e-6)
                u = u * u * (3 - 2 * u) * 0.25 + u * 0.75
                x, d = a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
                moving = True
                break
            else:
                break
        return x, d, moving

    def move_dir(self, ch, t):
        for (t0, t1, a, b) in self.moves.get(ch, []):
            if t0 <= t <= t1 and t1 > t0:
                return 1 if b[0] >= a[0] else -1
        return None

    def vis(self, ch, t):
        v = False
        for (tt, vv) in sorted(self.visible.get(ch, []), key=lambda e: e[0]):
            if t >= tt:
                v = vv
        return v

    def base_at(self, ch, t):
        b, tb, prev = "stand", -1e9, "stand"
        for (tt, bb) in sorted(self.base.get(ch, []), key=lambda e: e[0]):
            if t >= tt:
                prev, b, tb = b, bb, tt
        return b, prev, t - tb

    def gesture(self, ch, t):
        for (t0, t1, p) in self.gest.get(ch, []):
            if t0 - 0.05 <= t <= t1 + 0.5:
                return p, t - t0, t1 - t
        return None, 0, 0


def build(manifest=None):
    manifest = manifest if manifest is not None else load_manifest()
    st = Stage()
    shots = []
    t = 0.0
    lid = 0
    scenes_out = []
    for sc in SCENES:
        s_t0 = t
        items = sc["items"]
        sc_shots = []
        # staging reset at the scene start
        for ch in sc["cast"]:
            x, d, base, facing = sc["start"][ch]
            st.set(ch, t - 0.001, (x, d), True, base)
            st.busy_until[ch] = t
        for i, it in enumerate(items):
            sh = dict(scene=sc["n"], idx=len(sc_shots), t0=t, cam=it.get("cam"), type=it["type"],
                      loc=sc["loc"], tod=sc.get("tod", "day"), cast=sc["cast"], sfx=list(it.get("sfx", [])),
                      act=it.get("act", ""), desc=it.get("desc", ""), kind=it.get("kind"))
            if it["type"] == "line":
                lid += 1
                sh["lid"] = f"L{lid:03d}"
                m = manifest.get(sh["lid"])
                dur = m["dur"] if m else est_dur(it["tts"])
                sh["audio"] = m["file"] if m else None
                sh["speaker"] = it["sp"]
                sh["speech"] = (t + LEAD, t + LEAD + dur)
                sh["dur"] = LEAD + dur + max(0.3, it.get("pause", 0.25))
                sh["kh"], sh["en"], sh["emo"] = it["kh"], it["en"], it["emo"]
                sh["expr"] = expr_for(it["emo"])
                sh["to"] = None
                for j in list(range(i - 1, -1, -1)) + list(range(i + 1, len(items))):
                    o = items[j]
                    if o["type"] == "line" and o["sp"] not in (it["sp"], "narrator") and o["sp"] in sc["cast"]:
                        sh["to"] = o["sp"]
                        break
            else:
                sh["dur"] = it["dur"] * (1.0 if it["kind"] in ("establish", "ending") else SHOT_SCALE)
                sh["speaker"] = None
            t_act = t + 0.15
            end_t = t + sh["dur"]
            # moves
            for ch, mv in it.get("move", {}).items():
                if ch not in sc["cast"]:
                    continue
                x, d = st.pos.get(ch, (OFF_X, 0.1))
                # a speaker who leaves waits until the end of the line; everyone else moves at once
                t_mv = sh["speech"][1] + 0.05 if (it["type"] == "line" and mv.startswith("exit") and
                                                   ch == it["sp"]) else t_act
                if mv == "exit_right":
                    st.walk(ch, t_mv, (OFF_X + 150, d), then_vis=False)
                elif mv == "exit_left":
                    st.walk(ch, t_mv, (-OFF_X - 150, d), then_vis=False)
                elif mv.startswith("to:"):
                    a, b = mv[3:].split(",")
                    if not st.vis(ch, t_act):
                        st.set(ch, max(t_act, st.busy_until.get(ch, 0)), None, True)
                    st.walk(ch, t_act, (float(a), float(b)))
                elif mv.startswith("near:"):
                    o = mv[5:]
                    ox, od = st.pos[o]
                    side = 1 if x > ox else -1
                    st.walk(ch, t_act, (ox + side * 62, od + 0.03))
            # poses
            for ch, p in it.get("pose", {}).items():
                if ch not in sc["cast"]:
                    continue
                if p in BASE_POSES:
                    st.set(ch, max(t_act, min(st.busy_until.get(ch, 0), end_t - 0.3)), None, None, p)
                else:
                    end = sh["speech"][1] if sh.get("speech") else end_t
                    st.gest[ch].append((t_act, end, p))
            sh["t1"] = t + sh["dur"]
            sc_shots.append(sh)
            t += sh["dur"]
        scenes_out.append(dict(n=sc["n"], ch=sc["ch"], title_kh=sc["title_kh"], title_en=sc["title_en"],
                               source=sc["source"], t0=s_t0, t1=t, music=sc["music"], amb=sc["amb"],
                               loc=sc["loc"], tod=sc.get("tod", "day"), cast=sc["cast"], shots=sc_shots))
        shots.extend(sc_shots)
    return dict(shots=shots, scenes=scenes_out, stage=st, total=t)


if __name__ == "__main__":
    tl = build()
    print(f"{len(tl['shots'])} shots, total {tl['total']/60:.2f} min")
    for s in tl["scenes"]:
        print(s["n"], s["title_en"], f"{(s['t1']-s['t0']):.1f}s", len(s["shots"]), "shots")

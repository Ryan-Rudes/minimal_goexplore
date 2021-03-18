from collections import defaultdict
from threading import Thread
from time import sleep
import numpy as np
import cv2
import gym

def cellfn(frame):
    cell = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    cell = cv2.resize(cell, (11, 8), interpolation = cv2.INTER_AREA)
    cell = cell // 32
    return cell

def hashfn(cell):
    return hash(cell.tobytes())

class Weights:
    times_chosen = 0.1
    times_chosen_since_new = 0
    times_seen = 0.3

class Powers:
    times_chosen = 0.5
    times_chosen_since_new = 0.5
    times_seen = 0.5

class Cell(object):
    def __init__(self):
        self.times_chosen = 0
        self.times_chosen_since_new = 0
        self.times_seen = 0

    def cntscore(self, a):
        w = getattr(Weights, a)
        p = getattr(Powers, a)
        v = getattr(self, a)
        return w / (v + e1) ** p + e2

    def cellscore(self):
        return self.cntscore('times_chosen')           +\
               self.cntscore('times_chosen_since_new') +\
               self.cntscore('times_seen')             +\
               1

    def visit(self):
        first_visit = False
        if not self.times_seen:
            first_visit = True
            for cell in archive.values():
                cell.times_chosen_since_new = 0
                cell.score = cell.cellscore()

        self.times_seen += 1
        self.score = self.cellscore()
        return first_visit

    def choose(self):
        self.times_chosen += 1
        self.times_chosen_since_new += 1
        return self.ram, self.reward, self.trajectory

archive = defaultdict(lambda: Cell())
highscore = 0
frames = 0

e1 = 0.001
e2 = 0.00001

def explore():
    global highscore, frames, best_cell, new_cell, archive

env = gym.make("MontezumaRevengeNoFrameskip-v0")
frame = env.reset()
score = 0
action = 0
trajectory = []
iterations = 0

while True:
    found_new_cell = False

    for i in range(100):
        if np.random.random() > 0.95:
            action = env.action_space.sample()

        for i in range(4):
            frame, reward, terminal, info = env.step(action)
            if iterations % 100 == 0:
                env.render()
            score += reward
            terminal |= info['ale.lives'] < 6
            if terminal:
                break

        trajectory.append(action)
        frames += 4

        if score > highscore:
            highscore = score

        if terminal:
            break
        else:
            cell = cellfn(frame)
            cellhash = hashfn(cell)
            cell = archive[cellhash]
            first_visit = cell.visit()
            if first_visit or score > cell.reward or score == cell.reward and len(trajectory) < len(cell.trajectory):
                cell.ram = env.env.clone_full_state()
                cell.reward = score
                cell.trajectory = trajectory.copy()
                cell.times_chosen = 0
                cell.times_chosen_since_new = 0
                cell.score = cell.cellscore()
                if first_visit:
                    found_new_cell = True

    if found_new_cell and iterations > 0:
        restore_cell.times_chosen_since_new = 0
        restore_cell.score = restore_cell.cellscore()

    iterations += 1
    scores = np.array([cell.score for cell in archive.values()])
    hashes = [cellhash for cellhash in archive.keys()]
    probs = scores / scores.sum()
    restore = np.random.choice(hashes, p = probs)
    restore_cell = archive[restore]
    ram, score, trajectory = restore_cell.choose()
    env.reset()
    env.env.restore_full_state(ram)

    print ("Iterations: %d, Cells: %d, Frames: %d, Max Reward: %d" % (iterations, len(archive), frames, highscore))
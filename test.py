import pickle
import random

import main

task = main.AnnotationTask("data/en_train.csv", (0,), ["x", "y", "z"], 2)
while len(task.un_annotated) > 0:
    task.annotate(random.randint(0, 2))
task.save_state("test.ano")
task2 = pickle.load(open("test.ano", "rb"))
task2.write_file("data/test.csv")




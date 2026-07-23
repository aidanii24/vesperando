import random

# Based on the paper of Pavlos S. Efraimidis, and the blog showcasing it by Max Halford
# https://maxhalford.github.io/blog/weighted-sampling-without-replacement/
# https://arxiv.org/pdf/1012.0256

def choice_weighted_no_replacement(population, weights, k=1, rand=random) -> list:
    if not k: return []

    ks = [rand.random() ** (1/w) for w in weights]
    order = sorted(range(len(population)), key=lambda i: ks[i])
    return [population[i] for i in order[-k:]]
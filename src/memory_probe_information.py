"""Finite-distribution checks for a memory-only response channel.

Elementary information-theory diagnostics, not LLM measurements or a new theorem.
All entropy values are in bits. No sampling is used.
"""
from collections import defaultdict
import json
import math
from pathlib import Path


def entropy(probabilities):
    probabilities = list(probabilities)
    if any(p < 0 for p in probabilities):
        raise ValueError("Negative probability")
    if not math.isclose(sum(probabilities), 1.0, abs_tol=1e-12):
        raise ValueError("Probabilities must sum to one")
    return -sum(p * math.log2(p) for p in probabilities if p)


def marginal(joint, coordinates):
    result = defaultdict(float)
    for values, probability in joint.items():
        result[tuple(values[i] for i in coordinates)] += probability
    return dict(result)


def h(joint, coordinates):
    return entropy(marginal(joint, coordinates).values())


def conditional_mutual_information(joint, x, y, z):
    return h(joint, x + z) + h(joint, y + z) - h(joint, z) - h(joint, x + y + z)


def example(good_noise=0.1, erased_one_probability=0.01):
    """Joint over (state, regime, memory, response).

    A fair state bit is either retained exactly or erased, independently with
    probability one half. One fixed reader kernel sees memory, not the hidden
    state. On a retained bit it flips with good_noise; on erasure it emits 1
    with erased_one_probability. Its fresh draw is independent of the state.
    """
    if not 0 <= good_noise <= 1 or not 0 <= erased_one_probability <= 1:
        raise ValueError("Invalid channel probability")
    joint = {}
    for state in (0, 1):
        for regime in ("retained", "erased"):
            memory = str(state) if regime == "retained" else "?"
            probability_one = (
                (1 - good_noise if state else good_noise)
                if regime == "retained" else erased_one_probability
            )
            for response in (0, 1):
                p = probability_one if response else 1 - probability_one
                joint[(state, regime, memory, response)] = 0.25 * p
    return joint


def condition_regime(joint, regime):
    selected = {key: p for key, p in joint.items() if key[1] == regime}
    mass = sum(selected.values())
    return {key: p / mass for key, p in selected.items()}


def analyze(joint):
    result = {
        "state_response_mutual_information_bits": h(joint, (0,)) + h(joint, (3,)) - h(joint, (0, 3)),
        "state_response_conditional_mutual_information_given_memory_bits": conditional_mutual_information(joint, (0,), (3,), (2,)),
        "regimes": {},
    }
    for regime in ("retained", "erased"):
        j = condition_regime(joint, regime)
        result["regimes"][regime] = {
            "state_entropy_given_memory_bits": h(j, (0, 2)) - h(j, (2,)),
            "response_entropy_given_memory_bits": h(j, (3, 2)) - h(j, (2,)),
            "response_error_probability": sum(p for key, p in j.items() if key[0] != key[3]),
            "conditional_mutual_information_bits": conditional_mutual_information(j, (0,), (3,), (2,)),
        }
    return result


def main():
    report = {
        "status": "exact illustrative distributions; not empirical model results",
        "ranking_reversal": analyze(example()),
        "zero_entropy_tie": analyze(example(0.0, 0.0)),
        "posterior_sampling_positive_control": analyze(example(0.0, 0.5)),
        "assumptions": [
            "fixed reader kernel with access only to memory and a fixed query",
            "reader randomness independent of the hidden state conditional on its input",
            "no tools, source access, hidden KV state, or per-case weight updates",
        ],
    }
    path = Path(__file__).resolve().parents[1] / "results/memory-probe-information.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

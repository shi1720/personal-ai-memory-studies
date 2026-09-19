"""Exact estimand audit for propensity-weighted, gated memory.

This is elementary probability arithmetic, not a new estimator, a reproduction
of a released implementation, or a simulated measurement of real users.
"""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path


def population(mu=F(4, 5), reference=F(1, 2)):
    if not 0 < mu < 1 or not 0 <= reference <= 1:
        raise ValueError('Unsupported policy')
    rows = []
    for action, exposure, target, success in [('A', mu, reference, F(4, 5)),
                                               ('B', 1-mu, 1-reference, F(1, 5))]:
        for x in [0, 1]:
            conditional = success if x else 1-success
            rows.append(dict(action=action, x=F(x), observed=exposure*conditional,
                             target=target*conditional, weight=target/exposure))
    return rows


def audit(rows, gate):
    if sum(r['observed'] for r in rows) != 1 or sum(r['target'] for r in rows) != 1:
        raise ValueError('Invalid population')
    gates = [F(gate(r)) for r in rows]
    if any(not 0 <= g <= 1 for g in gates):
        raise ValueError('Invalid gate')
    target = sum(r['target']*r['x'] for r in rows)
    gate_mass = sum(r['target']*g for r, g in zip(rows, gates))
    if not gate_mass:
        raise ValueError('No retained target mass')
    gated_numerator = sum(r['observed']*r['weight']*g*r['x'] for r, g in zip(rows, gates))
    gated_denominator = sum(r['observed']*r['weight']*g for r, g in zip(rows, gates))
    ratio = gated_numerator/gated_denominator
    covariance = sum(r['target']*g*r['x'] for r, g in zip(rows, gates))-gate_mass*target
    return dict(observed_mean=sum(r['observed']*r['x'] for r in rows), target_mean=target,
                ungated_propensity_mean=sum(r['observed']*r['weight']*r['x'] for r in rows),
                gated_ratio=ratio, target_gate_mass=gate_mass,
                target_covariance=covariance, bias=ratio-target,
                covariance_identity=covariance/gate_mass)


def sequential_update(events):
    """Literal scalar gated ratio recursion at lambda=1, starting at W=0."""
    value, mass = F(0), F(0)
    for x, weight, gate in events:
        increment = weight*gate
        if increment < 0:
            raise ValueError('Negative weight')
        if mass + increment:
            value = (mass*value+increment*x)/(mass+increment)
        mass += increment
    if not mass:
        raise ValueError('No positive weight')
    return value, mass


def exact_cycle(rows, gate, size=100):
    events = []
    for r in rows:
        number = r['observed']*size
        if number.denominator != 1:
            raise ValueError('Cycle cannot realize these proportions exactly')
        events.extend([(r['x'], r['weight'], F(gate(r)))]*int(number))
    return events


GATES = {
    'constant': lambda r: F(1, 2),
    'action_dependent': lambda r: F(9, 10) if r['action'] == 'A' else F(1, 10),
    'outcome_dependent': lambda r: F(9, 10) if r['x'] else F(1, 10),
}


def main():
    rows = population()
    cases = {}
    for name, gate in GATES.items():
        result = audit(rows, gate)
        value, mass = sequential_update(exact_cycle(rows, gate))
        if value != result['gated_ratio']:
            raise AssertionError('Recursion and population ratio disagree')
        cases[name] = {k: {'fraction': str(v), 'decimal': float(v)} for k, v in result.items()}
        cases[name]['exact_100_event_recursion'] = {'value': str(value), 'weight_mass': str(mass)}
    report = {'status': 'exact constructed estimand check, not LLM or user experiments',
              'settings': {'logging_probability_A': '4/5', 'reference_probability_A': '1/2',
                           'success_A': '4/5', 'success_B': '1/5', 'decay': 1,
                           'propensities': 'known exactly; positive; unclipped'},
              'cases': cases, 'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    path = Path(__file__).resolve().parents[1] / 'results/gated-memory-estimand.json'
    path.write_text(json.dumps(report, indent=2)+'\n')
    for name, result in cases.items():
        print(name, 'target', result['target_mean']['fraction'], 'gated', result['gated_ratio']['fraction'],
              'bias', result['bias']['fraction'])


if __name__ == '__main__':
    main()

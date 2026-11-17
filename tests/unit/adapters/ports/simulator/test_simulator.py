import unittest

from rescue.adapters.ports import Simulator


class RecordingSimulator(Simulator):
    def __init__(self):
        self.calls = []

    def simulate(self, scenario, policy, simulation_id):
        self.calls.append((scenario, policy, simulation_id))
        return "snapshot"


class SimulatorPortTests(unittest.TestCase):
    def test_the_port_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            Simulator()

    def test_a_subclass_implementing_simulate_is_called(self):
        simulator = RecordingSimulator()

        result = simulator.simulate("scenario", "policy", "simulation-1")

        self.assertEqual(result, "snapshot")
        self.assertEqual(simulator.calls, [("scenario", "policy", "simulation-1")])

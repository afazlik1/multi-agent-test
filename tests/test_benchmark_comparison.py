import unittest
from supervisor.benchmark_improvements import summarize

class BenchmarkComparisonTests(unittest.TestCase):
    def test_retains_independent_best_and_counts_thresholds_across_phases(self):
        history=[]
        for phase,values,runtime in [('independent',[2.,19.5],.2),('collaborative',[1.,0.],.3)]:
            best=max(values)
            history.append({'worker':'fixture','phase':phase,'best_x':best,'best_y':0.,'best_value':best,'runtime':runtime,'trajectory':[{'value':v} for v in values]})
        result=summarize(history,'fixture')
        self.assertEqual(result['best_value'],19.5)
        self.assertEqual(result['evaluations'],4)
        self.assertEqual(result['first_19'],2)
        self.assertIsNone(result['first_19_99'])
        self.assertAlmostEqual(result['runtime'],.5)

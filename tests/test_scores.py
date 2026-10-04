# tests/test_scores.py -- High score system verification
import unittest
import os
import tempfile
import json
import shutil
import scores

class TestScores(unittest.TestCase):
    def setUp(self):
        # create temporary folder for testing
        self.test_dir = tempfile.mkdtemp()
        self.score_path = os.path.join(self.test_dir, "scores.json")
        # override the file path used in scores.py
        self.old_path = scores._score_path
        scores._score_path = lambda: self.score_path

    def tearDown(self):
        # remove all test files
        shutil.rmtree(self.test_dir)
        scores._score_path = self.old_path

    def test_new_score_file(self):
        # load when no file exists, should get empty dict
        data = scores.load_scores()
        self.assertEqual(data, {})

    def test_submit_score(self):
        # submit new score
        scores.submit("Level1", 100)
        data = scores.load_scores()
        self.assertEqual(data["Level1"], 100)

    def test_update_better_score(self):
        # submit lower score first
        scores.submit("Level1", 50)
        # submit higher score next
        new_record = scores.submit("Level1", 150)
        
        self.assertTrue(new_record)
        self.assertEqual(scores.load_scores()["Level1"], 150)

    def test_do_not_update_worse_score(self):
        scores.submit("Level1", 100)
        new_record = scores.submit("Level1", 50)
        
        self.assertFalse(new_record)
        self.assertEqual(scores.load_scores()["Level1"], 100)

    def test_multiple_levels(self):
        scores.submit("Level1", 100)
        scores.submit("Level2", 200)
        
        data = scores.load_scores()
        self.assertEqual(len(data), 2)
        self.assertEqual(data["Level1"], 100)
        self.assertEqual(data["Level2"], 200)

    def test_corrupt_file_handling(self):
        # write corrupt file (not json)
        with open(self.score_path, "w") as f:
            f.write("not a json")
        
        # expect the system to survive without crashing (should return empty or reset)
        data = scores.load_scores()
        self.assertEqual(data, {})

if __name__ == "__main__":
    unittest.main(verbosity=2)
# invitation-generator/test_create_rooms.py
import unittest
from create_rooms import provision, slug


class TestProvision(unittest.TestCase):
    def test_creates_then_reuses(self):
        invs = [{"title": "Trust, said plainly", "framing": "x"}, {"title": "The timezone problem", "framing": "y"}]
        calls = []

        def fake(base, inv):
            calls.append(inv["title"])
            return {"id": "id-" + slug(inv["title"]), "facilitatorToken": "tok"}

        mapping = provision(invs, "http://x", {"rooms": {}}, fake)
        self.assertEqual(calls, ["Trust, said plainly", "The timezone problem"])
        self.assertEqual(set(mapping["rooms"]), {slug(i["title"]) for i in invs})
        self.assertTrue(mapping["rooms"][slug("Trust, said plainly")]["room_url"].endswith("/room/id-trust-said-plainly"))

        calls.clear()
        again = provision(invs, "http://x", mapping, fake)
        self.assertEqual(calls, [])  # nothing recreated
        self.assertEqual(set(again["rooms"]), {slug(i["title"]) for i in invs})


if __name__ == "__main__":
    unittest.main()

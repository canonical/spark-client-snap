import logging
import unittest

from spark_client.services import parse_conf_overrides
from tests import TestCase


class TestServices(TestCase):
    def test_conf_expansion_cli(self):
        home_var = "/this/is/my/home"

        parsed_property = parse_conf_overrides(
            ["my-conf=$HOME/folder", "my-other-conf=/this/does/$NOT/change"],
            environ_vars={"HOME": home_var},
        )
        self.assertEqual(parsed_property.props["my-conf"], f"{home_var}/folder")
        self.assertEqual(
            parsed_property.props["my-other-conf"], "/this/does/$NOT/change"
        )


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level="DEBUG")
    unittest.main()

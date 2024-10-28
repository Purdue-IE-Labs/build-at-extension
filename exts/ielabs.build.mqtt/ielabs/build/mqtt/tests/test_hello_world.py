import omni.kit.test

# Extnsion for writing UI tests (simulate UI interaction)
import omni.kit.ui_test as ui_test

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
import ielabs.build.mqtt as ext

from parameterized import parameterized

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class Test(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        self.ext = ext.Paho_mqttExtension()

    # After running each test
    async def tearDown(self):
        pass

    @parameterized.expand([
        ("hello", ext.Type.STRING, "hello"),
        (12.34, ext.Type.INT, 12),
        (45.23, ext.Type.FLOAT, 45.23)
    ])
    async def test_decode(self, encoded_string: str, type: ext.Type, expected_value):
        self.assertEqual(self.ext.decode(encoded_string, type), expected_value)

    async def test_window_button(self):
        pass
        # # Find a label in our window
        # label = ui_test.find("My Window//Frame/**/Label[*]")

        # # Find buttons in our window
        # add_button = ui_test.find("My Window//Frame/**/Button[*].text=='Add'")
        # reset_button = ui_test.find("My Window//Frame/**/Button[*].text=='Reset'")

        # # Click reset button
        # await reset_button.click()
        # self.assertEqual(label.widget.text, "empty")

        # await add_button.click()
        # self.assertEqual(label.widget.text, "count: 1")

        # await add_button.click()
        # self.assertEqual(label.widget.text, "count: 2")

"""Actual browser scope flow; inherited brief journeys also guard navigation."""
import os
from pathlib import Path
import test_game_brief_browser as brief_browser_fixture


class ScopeBrowserTests(brief_browser_fixture.GameBriefBrowserTests):
    def open_scope(self, original='A small garden game.'):
        self.create(original); self.page.locator('#plan-first').click()
        self.page.locator('#workspace').wait_for(state='visible')
        self.page.locator('#create').click(); self.page.locator('#confirm-action').click()
        self.page.locator('#plan').wait_for(state='visible')

    def test_unsupported_engine_needs_explicit_alternative_and_reviewed_agreement(self):
        self.open_scope('An Unreal AAA multiplayer open-world game.')
        self.assertTrue(self.page.locator('#agree').is_disabled())
        self.assertIn('Godot', self.page.locator('#limitations').inner_text())
        self.page.locator('#engine').select_option('godot'); self.page.locator('#save').click()
        self.page.wait_for_function("document.querySelector('#version').textContent==='Plan version 2'")
        self.page.locator('#agree').click(); self.page.keyboard.press('Escape')
        self.assertIn('Draft', self.page.locator('#state').inner_text())
        self.page.locator('#agree').click(); self.page.locator('#confirm-action').click()
        self.page.wait_for_function("document.querySelector('#state').textContent.startsWith('Scope agreed')")
        self.page.reload(); self.page.locator('#plan').wait_for(state='visible')
        self.assertIn('development has not started', self.page.locator('#state').inner_text())

    def test_conflict_keeps_scope_edit_and_back_escape_does_not_navigate(self):
        self.open_scope(); other = self.context.new_page(); other.goto(self.page.url)
        other.locator('#plan').wait_for(state='visible')
        self.page.locator('#scope-goal').fill('Collect five seeds and reach the shed.')
        self.page.locator('#save').click(); self.page.wait_for_function("document.querySelector('#version').textContent==='Plan version 2'")
        other.locator('#scope-goal').fill('Keep this conflicting idea'); other.locator('#save').click()
        other.wait_for_function("document.querySelector('#status').textContent.includes('newer scope')")
        self.assertEqual(other.locator('#scope-goal').input_value(),'Keep this conflicting idea')
        other.locator('#back').click(); other.keyboard.press('Escape')
        self.assertIn('/first-playable',other.url)

    def test_plan_layout_and_estimate_are_visible_on_mobile(self):
        self.open_scope()
        self.assertEqual(self.page.locator('#tasks > li').count(),6)
        self.assertIn('31,200',self.page.locator('#budget').inner_text())
        for width,height,name in [(1280,1000,'desktop'),(390,844,'mobile')]:
            self.page.set_viewport_size({'width':width,'height':height})
            self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            if os.getenv('SCOPE_SCREENSHOT_DIR'):
                folder=Path(os.environ['SCOPE_SCREENSHOT_DIR']);folder.mkdir(parents=True,exist_ok=True)
                self.page.screenshot(path=str(folder/f'scope-{name}.png'),full_page=True)


if __name__ == '__main__':
    import unittest
    unittest.main()

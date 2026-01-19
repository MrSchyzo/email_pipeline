# Iren plugin

Since it uses selenium with chrome, it requires the chromedriver to be present in the path.
So, either make sure to run `brew install chromedriver` or `apt install -y chromium-chromedriver`.

Due to an invisible recaptcha, headless chrome does not work. This requires a GUI.
One way to achieve that might be to use `xvfb` (X virtual framebuffer) and prepend `xvfb-run` with the python command.
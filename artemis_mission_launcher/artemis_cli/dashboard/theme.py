# Copyright 2026 Jasmeet Singh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Central colour palette and panel styling for the dashboard.

Minimal cyan-on-black mission-control palette. Only the colours below are used
anywhere in the UI; widgets must reference these names rather than hard-coding
styles.
"""
from rich import box

# --- palette ---------------------------------------------------------------
PRIMARY = 'cyan'          # default content / values / clock
ACCENT = 'bright_cyan'    # emphasis (titles, big text, live highlights)
OK = 'green'              # nominal / good values
WARN = 'yellow'          # warnings / acceleration
ERR = 'red'               # errors
MUTED = 'grey70'          # labels and secondary text
FAINT = 'grey37'          # borders, axes, separators
WHITE = 'white'

# --- chrome ----------------------------------------------------------------
BOX = box.ROUNDED
BORDER = FAINT
TITLE = f'bold {ACCENT}'
LABEL = MUTED
VALUE = PRIMARY

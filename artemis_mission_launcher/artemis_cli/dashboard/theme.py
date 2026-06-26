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
"""Central neon-blue colour palette and panel styling for the dashboard."""
from rich import box

# --- palette (neon blue on a deep-blue black) ------------------------------
PRIMARY = '#2e9bff'       # default content / values / clock (neon blue)
ACCENT = '#6cc4ff'        # emphasis (titles, big text, live highlights)
OK = '#4ade80'            # nominal / good values
WARN = '#facc15'         # warnings / acceleration
ERR = '#f87171'           # errors
MUTED = '#8aa6c8'         # labels and secondary text (blue-grey)
FAINT = '#2b4a6f'         # borders, axes, grid, separators (dim blue)
WHITE = '#e6f0ff'

# --- chrome ----------------------------------------------------------------
BOX = box.ROUNDED
BORDER = FAINT
TITLE = f'bold {ACCENT}'
LABEL = MUTED
VALUE = PRIMARY

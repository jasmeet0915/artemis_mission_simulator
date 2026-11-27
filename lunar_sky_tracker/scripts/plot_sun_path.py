#!/usr/bin/env python3
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

"""
Plot the Sun's path over a known lunar site across one full lunar day.

Samples :func:`get_solar_system_body_position` over one lunar solar day (a
synodic month) and renders two views of the same track: the sky dome as seen
from the site, and elevation against time. Writes a PNG, and optionally the raw
samples as CSV so the numbers can be checked against an independent ephemeris.

Usage:
    python3 scripts/plot_sun_path.py --site tranquility_base
    python3 scripts/plot_sun_path.py --site shackleton_rim --theme light
"""

import argparse
import csv
from datetime import datetime, timedelta, timezone

from lunar_sky_tracker.spice.celestial_ephemeris import get_solar_system_body_position
from lunar_sky_tracker.spice.kernel_manager import KernelManager
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use('Agg')

# A lunar solar day: the Sun returns to the same place in the sky after one
# synodic month, not one sidereal month.
SYNODIC_MONTH_DAYS = 29.530588

# Well-known sites, as (display name, latitude deg, east longitude deg).
# The polar sites use the surveyed centres of the terrain models we ship
# (artemis_assets/models/<site>/metadata.yaml).
SITES = {
    'tranquility_base': ('Tranquility Base (Apollo 11)', 0.67408, 23.47297),
    'taurus_littrow': ('Taurus-Littrow (Apollo 17)', 20.1908, 30.7717),
    'shackleton_rim': (
        'Shackleton Rim', -89.76681145214992, -171.86989764584402),
    'de_gerlache': ('de Gerlache Crater', -88.5, -87.1),
}

# Slots from the validated categorical palette: yellow on the dark surface,
# orange on the light one (light-mode yellow sits below 3:1 contrast).
THEMES = {
    'dark': {
        'surface': '#1a1a19',
        'ink': '#ffffff',
        'ink_soft': '#c3c2b7',
        'grid': '#3a3a37',
        # A shaded band, kept just lighter than the surface so it reads as
        # "night" rather than a black hole punched in the panel.
        'night': '#26262a',
        'sun': '#c98500',
        'azimuth': '#3987e5',
    },
    'light': {
        'surface': '#ffffff',
        'ink': '#14161a',
        'ink_soft': '#5c6169',
        'grid': '#d6d9df',
        # A cool band on white, clearly a deliberate shade of night.
        'night': '#e9ecf1',
        'sun': '#eb6834',
        'azimuth': '#2a78d6',
    },
}


def sample_track(body, start_epoch, days, step_minutes, lat, lon):
    """Return (hours, azimuth_deg, elevation_deg, direction_enu) over the span."""
    step_seconds = step_minutes * 60.0
    count = int(round(days * 86400.0 / step_seconds)) + 1

    hours = np.empty(count)
    azimuth = np.empty(count)
    elevation = np.empty(count)
    direction = np.empty((count, 3))

    for index in range(count):
        offset = index * step_seconds
        position = get_solar_system_body_position(
            body, start_epoch + offset, lat, lon)
        hours[index] = offset / 3600.0
        azimuth[index] = position.azimuth_deg
        elevation[index] = position.elevation_deg
        direction[index] = position.direction_enu

    return hours, azimuth, elevation, direction


def break_on_wrap(values, threshold=180.0):
    """Return a copy with NaN at 0/360 seams, so the line is not drawn across."""
    broken = values.astype(float).copy()
    seams = np.flatnonzero(np.abs(np.diff(values)) > threshold)
    broken[seams] = np.nan
    return broken


def summarize(hours, elevation):
    """Return the daylight facts a reader (or a checker) wants: a dict."""
    above = elevation > 0.0
    peak = int(np.argmax(elevation))

    # Horizon crossings, as the sample index where the sign flips.
    crossings = np.flatnonzero(np.diff(above.astype(int)))
    sunrise = next((i + 1 for i in crossings if above[i + 1]), None)
    sunset = next((i for i in crossings if not above[i + 1]), None)

    return {
        'peak_index': peak,
        'max_elevation_deg': float(elevation[peak]),
        'max_elevation_hours': float(hours[peak]),
        'min_elevation_deg': float(np.min(elevation)),
        'sunlit_fraction': float(np.count_nonzero(above)) / above.size,
        'sunrise_index': sunrise,
        'sunset_index': sunset,
        'sunrise_hours': None if sunrise is None else float(hours[sunrise]),
        'sunset_hours': None if sunset is None else float(hours[sunset]),
    }


def plot_sky_dome(axes, hours, azimuth, elevation, facts, theme):
    """Draw the above-horizon track on a polar sky dome: N up, E clockwise."""
    above = elevation > 0.0
    axes.set_theta_zero_location('N')
    axes.set_theta_direction(-1)

    # Radius is the zenith angle, so the horizon is the outer rim.
    axes.plot(
        np.radians(azimuth[above]), 90.0 - elevation[above],
        color=theme['sun'], linewidth=2.0, solid_capstyle='round')

    # A dot per Earth-day gives the track a sense of pace; the labelled
    # anchors below are the only points that carry text.
    day_marks = above & (np.abs((hours + 1e-6) % 24.0) < 1e-3)
    axes.plot(
        np.radians(azimuth[day_marks]), 90.0 - elevation[day_marks],
        linestyle='none', marker='o', markersize=3.5,
        color=theme['sun'], alpha=0.75)

    anchors = [('peak', facts['peak_index'])]
    for label, key in (('rise', 'sunrise_index'), ('set', 'sunset_index')):
        if facts[key] is not None:
            anchors.append((label, facts[key]))

    for label, index in anchors:
        if not above[index]:
            continue
        theta = np.radians(azimuth[index])
        radius = 90.0 - elevation[index]
        axes.plot(
            theta, radius, marker='o', markersize=8, color=theme['sun'],
            markeredgecolor=theme['surface'], markeredgewidth=2.0, zorder=5)
        axes.annotate(
            label, xy=(theta, radius), xytext=(7, 6),
            textcoords='offset points', color=theme['ink'], fontsize=9,
            zorder=6)

    axes.set_rlim(0.0, 90.0)
    axes.set_rgrids(
        [30.0, 60.0, 90.0], labels=['60°', '30°', '0°'],
        color=theme['ink_soft'], fontsize=8)
    axes.set_thetagrids(
        [0, 90, 180, 270], labels=['N', 'E', 'S', 'W'],
        color=theme['ink_soft'], fontsize=10)
    axes.grid(color=theme['grid'], linewidth=0.6)
    axes.set_facecolor(theme['surface'])
    axes.spines['polar'].set_color(theme['grid'])
    axes.set_title(
        'Sky dome: looking up, one dot per Earth day',
        color=theme['ink'], fontsize=11, pad=22)


def _longest_run(mask):
    """Return (start, end) indices of the longest True run, or None."""
    best, best_len, index = None, 0, 0
    while index < mask.size:
        if mask[index]:
            end = index
            while end < mask.size and mask[end]:
                end += 1
            if end - index > best_len:
                best, best_len = (index, end - 1), end - index
            index = end
        else:
            index += 1
    return best


def label_horizon_regions(axes, days, elevation, theme):
    """Name the day and night stretches in place, so no legend is needed."""
    above = elevation > 0.0
    pos_ext, neg_ext = float(elevation.max()), float(-elevation.min())

    day = _longest_run(above)
    if day is not None and pos_ext > 0.0:
        mid = (day[0] + day[1]) // 2
        axes.text(
            days[mid], 0.10 * pos_ext, 'Sun above horizon',
            color=theme['sun'], fontsize=9, ha='center', va='bottom',
            weight='medium')

    night = _longest_run(~above)
    if night is not None and neg_ext > 0.0:
        mid = (night[0] + night[1]) // 2
        axes.text(
            days[mid], -0.12 * neg_ext, 'Sun below horizon',
            color=theme['ink_soft'], fontsize=9, ha='center', va='top',
            weight='medium')


def plot_elevation(axes, hours, elevation, facts, theme):
    """Draw elevation against time, with the sub-horizon span shaded."""
    days = hours / 24.0

    axes.fill_between(
        days, np.minimum(elevation, 0.0), 0.0,
        color=theme['night'], linewidth=0.0)
    axes.axhline(0.0, color=theme['grid'], linewidth=1.0, zorder=1)
    axes.plot(
        days, elevation, color=theme['sun'], linewidth=2.0,
        solid_capstyle='round', zorder=3)

    peak_day = facts['max_elevation_hours'] / 24.0
    peak_elevation = facts['max_elevation_deg']
    axes.plot(
        peak_day, peak_elevation, marker='o', markersize=8,
        color=theme['sun'], markeredgecolor=theme['surface'],
        markeredgewidth=2.0, zorder=4)
    axes.annotate(
        f'peak {peak_elevation:.1f}°',
        xy=(peak_day, peak_elevation),
        xytext=(6, -4), textcoords='offset points',
        color=theme['ink'], fontsize=9)

    axes.set_xlabel('Earth days from epoch', color=theme['ink_soft'], fontsize=9)
    axes.set_ylabel('Elevation (deg)', color=theme['ink_soft'], fontsize=9)
    axes.set_xlim(days[0], days[-1])
    axes.set_facecolor(theme['surface'])
    axes.grid(color=theme['grid'], linewidth=0.6, axis='y')
    axes.set_axisbelow(True)
    for side in ('top', 'right'):
        axes.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        axes.spines[side].set_color(theme['grid'])
    axes.tick_params(colors=theme['ink_soft'], labelsize=9)
    label_horizon_regions(axes, days, elevation, theme)
    axes.set_title(
        'Elevation over one lunar day',
        color=theme['ink'], fontsize=11, pad=12)


def style_time_axis(axes, theme, xlabel=None):
    """Apply the shared recessive axis treatment to a time-series panel."""
    axes.set_facecolor(theme['surface'])
    axes.grid(color=theme['grid'], linewidth=0.6, axis='y')
    axes.set_axisbelow(True)
    for side in ('top', 'right'):
        axes.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        axes.spines[side].set_color(theme['grid'])
    axes.tick_params(colors=theme['ink_soft'], labelsize=9)
    if xlabel:
        axes.set_xlabel(xlabel, color=theme['ink_soft'], fontsize=9)


def plot_angles(figure, grid, hours, azimuth, elevation, facts, theme):
    """Stack elevation and azimuth on a shared time axis, never a 2nd y-scale."""
    days = hours / 24.0

    top = figure.add_subplot(grid[0, 0])
    top.fill_between(
        days, np.minimum(elevation, 0.0), 0.0, color=theme['night'],
        linewidth=0.0)
    top.axhline(0.0, color=theme['grid'], linewidth=1.0, zorder=1)
    top.plot(
        days, elevation, color=theme['sun'], linewidth=2.0, zorder=3,
        solid_capstyle='round')
    top.plot(
        facts['max_elevation_hours'] / 24.0, facts['max_elevation_deg'],
        marker='o', markersize=8, color=theme['sun'],
        markeredgecolor=theme['surface'], markeredgewidth=2.0, zorder=4)
    top.annotate(
        f'peak {facts["max_elevation_deg"]:.1f}°',
        xy=(facts['max_elevation_hours'] / 24.0, facts['max_elevation_deg']),
        xytext=(7, -3), textcoords='offset points', color=theme['ink'],
        fontsize=9)
    top.set_ylabel('Elevation (deg)', color=theme['ink_soft'], fontsize=9)
    top.set_xlim(days[0], days[-1])
    top.tick_params(labelbottom=False)
    label_horizon_regions(top, days, elevation, theme)
    style_time_axis(top, theme)

    bottom = figure.add_subplot(grid[1, 0], sharex=top)
    # Shade the same nights the panel above shades, so the fast azimuth swing
    # is visibly something that happens with the Sun under the horizon.
    night = np.concatenate(([0], (elevation <= 0.0).astype(int), [0]))
    edges = np.diff(night)
    for start, end in zip(
            np.flatnonzero(edges == 1), np.flatnonzero(edges == -1) - 1):
        bottom.axvspan(
            days[start], days[end], color=theme['night'], linewidth=0.0)
    bottom.plot(
        days, break_on_wrap(azimuth), color=theme['azimuth'], linewidth=2.0,
        solid_capstyle='round')
    bottom.set_ylabel('Azimuth (deg)', color=theme['ink_soft'], fontsize=9)
    bottom.set_ylim(0.0, 360.0)
    bottom.set_yticks([0, 90, 180, 270, 360])
    bottom.set_yticklabels(['0 N', '90 E', '180 S', '270 W', '360 N'])
    style_time_axis(bottom, theme, xlabel='Earth days from epoch')

    top.set_title(
        'Elevation: angle above local horizon',
        color=theme['ink'], fontsize=11, pad=10, loc='left')
    bottom.set_title(
        'Azimuth: clockwise +ve from local north',
        color=theme['ink'], fontsize=11, pad=10, loc='left')


def plot_orbit_3d(axes, direction, elevation, theme):
    """Trace the direction vector on the unit sky sphere, in local ENU."""
    above = elevation > 0.0
    east, north, up = direction[:, 0], direction[:, 1], direction[:, 2]

    # The horizon: the unit circle the sky dome sits on.
    ring = np.linspace(0.0, 2.0 * np.pi, 361)
    axes.plot(
        np.cos(ring), np.sin(ring), np.zeros_like(ring),
        color=theme['grid'], linewidth=1.2)
    for east_at, north_at, label in (
            (1.18, 0.0, 'E'), (0.0, 1.18, 'N'),
            (-1.18, 0.0, 'W'), (0.0, -1.18, 'S')):
        axes.text(
            east_at, north_at, 0.0, label,
            color=theme['ink_soft'], fontsize=11, ha='center', va='center')

    # Below-horizon stretches are real but unobservable: draw them recessive.
    axes.plot(
        np.where(above, east, np.nan), np.where(above, north, np.nan),
        np.where(above, up, np.nan),
        color=theme['sun'], linewidth=2.4)
    axes.plot(
        np.where(above, np.nan, east), np.where(above, np.nan, north),
        np.where(above, np.nan, up),
        color=theme['sun'], linewidth=1.2, alpha=0.28)

    # The observer, and a spoke every few days for depth.
    axes.scatter([0.0], [0.0], [0.0], color=theme['ink_soft'], s=18)
    spokes = np.linspace(0, direction.shape[0] - 1, 13).astype(int)
    for index in spokes:
        if not above[index]:
            continue
        axes.plot(
            [east[index], east[index]], [north[index], north[index]],
            [0.0, up[index]], color=theme['sun'], linewidth=0.7, alpha=0.35)

    axes.set_xlim(-1.1, 1.1)
    axes.set_ylim(-1.1, 1.1)
    axes.set_zlim(-1.05, 1.05)
    axes.set_box_aspect((1.0, 1.0, 0.9))
    axes.view_init(elev=24, azim=-58)
    # The compass letters on the ring carry E/N/S/W, so the only axis that
    # needs naming is the vertical one.
    axes.set_xticks([])
    axes.set_yticks([])
    axes.set_zticks([-1.0, 0.0, 1.0])
    axes.set_zticklabels(['nadir (-1)', 'horizon (0)', 'zenith (+1)'])
    axes.tick_params(colors=theme['ink_soft'], labelsize=8)
    axes.set_facecolor(theme['surface'])
    for pane_axis in (axes.xaxis, axes.yaxis, axes.zaxis):
        pane_axis.set_pane_color((0.0, 0.0, 0.0, 0.0))
        pane_axis._axinfo['grid']['color'] = theme['grid']


def add_title_block(figure, site_name, lat, lon, start_utc, theme):
    """Put the title, a technical data line and provenance footer on a figure."""
    figure.suptitle(
        f'The Sun over {site_name}',
        color=theme['ink'], fontsize=18, x=0.5, y=0.975, weight='medium')
    hemi_ns = 'S' if lat < 0 else 'N'
    hemi_ew = 'W' if lon < 0 else 'E'
    figure.text(
        0.5, 0.918,
        f'{abs(lat):.4f}°{hemi_ns}  {abs(lon):.4f}°{hemi_ew}     '
        f'EPOCH {start_utc:%Y-%m-%dT%H:%MZ}     SPAN 1 LUNAR SOLAR DAY',
        color=theme['ink_soft'], fontsize=10, ha='center', family='monospace')
    figure.text(
        0.5, 0.02,
        'Computed from NASA SPICE kernels (DE440), MOON_ME frame  ·  '
        'lunar_sky_tracker  ·  artemis_mission_simulator',
        color=theme['ink_soft'], fontsize=8, ha='center', family='monospace')


def save(figure, theme, out_path):
    """Write the figure out on the theme surface."""
    figure.savefig(
        out_path, facecolor=theme['surface'], bbox_inches='tight',
        pad_inches=0.35)
    plt.close(figure)


def render_sky(track, theme, out_path):
    """Sky dome beside elevation over time."""
    figure = plt.figure(figsize=(13.0, 6.4), dpi=200)
    figure.patch.set_facecolor(theme['surface'])
    # Leave the top band to the title block so nothing collides with it.
    grid = figure.add_gridspec(
        1, 2, width_ratios=[1.0, 1.35], wspace=0.22, top=0.80, bottom=0.11)

    plot_sky_dome(
        figure.add_subplot(grid[0, 0], projection='polar'),
        track['hours'], track['azimuth'], track['elevation'], track['facts'],
        theme)
    plot_elevation(
        figure.add_subplot(grid[0, 1]), track['hours'], track['elevation'],
        track['facts'], theme)
    return figure


def render_angles(track, theme, out_path):
    """Elevation and azimuth stacked on one shared time axis."""
    figure = plt.figure(figsize=(12.0, 7.2), dpi=200)
    figure.patch.set_facecolor(theme['surface'])
    grid = figure.add_gridspec(
        2, 1, height_ratios=[1.0, 1.0], hspace=0.28, top=0.82, bottom=0.09,
        left=0.09, right=0.97)

    plot_angles(
        figure, grid, track['hours'], track['azimuth'], track['elevation'],
        track['facts'], theme)
    return figure


def render_orbit(track, theme, out_path):
    """Trace the direction vector on the unit sky sphere."""
    figure = plt.figure(figsize=(9.0, 7.6), dpi=200)
    figure.patch.set_facecolor(theme['surface'])
    axes = figure.add_subplot(projection='3d')
    figure.subplots_adjust(top=0.92, bottom=0.0, left=0.0, right=1.0)

    plot_orbit_3d(axes, track['direction'], track['elevation'], theme)
    return figure


def render_briefing(track, theme, out_path):
    """Compose the angle stack beside the 3D orbit as one figure."""
    figure = plt.figure(figsize=(17.0, 8.2), dpi=200)
    figure.patch.set_facecolor(theme['surface'])
    outer = figure.add_gridspec(
        1, 2, width_ratios=[1.18, 1.0], wspace=0.06,
        top=0.85, bottom=0.085, left=0.07, right=0.975)

    left = outer[0, 0].subgridspec(2, 1, hspace=0.30)
    plot_angles(
        figure, left, track['hours'], track['azimuth'], track['elevation'],
        track['facts'], theme)
    axes3d = figure.add_subplot(outer[0, 1], projection='3d')
    plot_orbit_3d(axes3d, track['direction'], track['elevation'], theme)
    return figure


FIGURES = {
    'sky': render_sky,
    'angles': render_angles,
    'orbit': render_orbit,
    'briefing': render_briefing,
}


def write_csv(path, start_utc, hours, azimuth, elevation):
    """Dump the raw samples so the track can be checked against another source."""
    with open(path, 'w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['utc', 'hours_from_epoch', 'azimuth_deg', 'elevation_deg'])
        for hour, az, el in zip(hours, azimuth, elevation):
            stamp = start_utc + timedelta(hours=float(hour))
            writer.writerow([
                stamp.strftime('%Y-%m-%dT%H:%M:%S'),
                f'{hour:.4f}', f'{az:.6f}', f'{el:.6f}'])


def parse_args():
    """Parse the command line."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument(
        '--site', choices=sorted(SITES), default='tranquility_base',
        help='Which known site to observe from (default: tranquility_base)')
    parser.add_argument(
        '--body', default='SUN',
        help='SPICE body to track (default: SUN)')
    parser.add_argument(
        '--start', default='2026-01-01T00:00:00',
        help='UTC epoch to start from, ISO 8601 (default: 2026-01-01T00:00:00)')
    parser.add_argument(
        '--days', type=float, default=SYNODIC_MONTH_DAYS,
        help=f'Span to plot in days (default: {SYNODIC_MONTH_DAYS}, one lunar day)')
    parser.add_argument(
        '--step-minutes', type=float, default=20.0,
        help='Sample interval in minutes (default: 20)')
    parser.add_argument(
        '--theme', choices=sorted(THEMES), default='light',
        help='Colour theme (default: light)')
    parser.add_argument(
        '--figure', choices=sorted(FIGURES) + ['all'], default='sky',
        help='sky dome + elevation, stacked angles, 3D orbit, the angle+orbit '
             'briefing composite, or all (default: sky)')
    parser.add_argument(
        '--out', default=None,
        help='PNG output path (default: sun_<figure>_<site>.png)')
    parser.add_argument(
        '--csv', default=None,
        help='Also write the raw samples to this CSV path')
    parser.add_argument(
        '--kernel-dir', default='/opt/spice_kernels',
        help='Directory holding the SPICE kernels (default: /opt/spice_kernels)')
    return parser.parse_args()


def main():
    """Sample the track, render the figure, report the facts."""
    args = parse_args()
    site_name, lat, lon = SITES[args.site]
    start_utc = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
    theme = THEMES[args.theme]
    wanted = sorted(FIGURES) if args.figure == 'all' else [args.figure]
    if args.out and len(wanted) > 1:
        raise SystemExit('--out takes a single --figure, not "all"')

    manager = KernelManager(args.kernel_dir)
    manager.furnish()
    try:
        hours, azimuth, elevation, direction = sample_track(
            args.body, start_utc.timestamp(), args.days, args.step_minutes,
            lat, lon)
    finally:
        manager.unload()

    facts = summarize(hours, elevation)
    track = {
        'hours': hours, 'azimuth': azimuth, 'elevation': elevation,
        'direction': direction, 'facts': facts,
    }

    written = []
    for name in wanted:
        out_path = args.out or f'sun_{name}_{args.site}.png'
        figure = FIGURES[name](track, theme, out_path)
        add_title_block(figure, site_name, lat, lon, start_utc, theme)
        save(figure, theme, out_path)
        written.append(out_path)

    print(f'{site_name}  ({lat:+.3f}, {lon:+.3f})')
    print(f'  samples          {hours.size} at {args.step_minutes:g} min')
    print(f'  peak elevation   {facts["max_elevation_deg"]:.3f} deg '
          f'at +{facts["max_elevation_hours"] / 24.0:.2f} d')
    print(f'  min elevation    {facts["min_elevation_deg"]:.3f} deg')
    print(f'  sunlit fraction  {facts["sunlit_fraction"] * 100:.1f}%')
    if facts['sunrise_hours'] is not None:
        print(f'  first sunrise    +{facts["sunrise_hours"] / 24.0:.2f} d')
    if facts['sunset_hours'] is not None:
        print(f'  first sunset     +{facts["sunset_hours"] / 24.0:.2f} d')
    for path in written:
        print(f'  wrote            {path}')

    if args.csv:
        write_csv(args.csv, start_utc, hours, azimuth, elevation)
        print(f'  wrote            {args.csv}')


if __name__ == '__main__':
    main()

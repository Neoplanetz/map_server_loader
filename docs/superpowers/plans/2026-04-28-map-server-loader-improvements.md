# map_server_loader Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Parameterize the launch file, clean up `setup.py` TODO metadata, silence the lifecycle bond shutdown warning, and refresh the README — without breaking the existing zero-argument run.

**Architecture:** Edits stay confined to three files (`setup.py`, `launch/load_map_server.launch.py`, `README.md`). The launch file gains four `DeclareLaunchArgument`s (`map`, `use_sim_time`, `autostart`, `log_level`) wired through `LaunchConfiguration` substitutions, plus `bond_timeout: 0.0` on the lifecycle manager. Defaults preserve current behavior, so a no-arg `ros2 launch` produces an identical result.

**Tech Stack:** ROS 2 (`ament_python`), `nav2_map_server`, `nav2_lifecycle_manager`, `launch`, `launch_ros`, `colcon`.

**Spec:** [docs/superpowers/specs/2026-04-28-map-server-loader-improvements-design.md](../specs/2026-04-28-map-server-loader-improvements-design.md)

---

## Prerequisites

Before starting, verify your environment:

- [ ] **Check ROS 2 environment is sourced**

Run: `printenv | grep ROS_DISTRO`
Expected: a line like `ROS_DISTRO=humble` (or `jazzy`, `iron`, etc.). If empty, source `/opt/ros/<distro>/setup.bash` first.

- [ ] **Confirm the package is reachable from a colcon workspace**

The package directory `/home/neoplanetz/Documents/github/map_server_loader` must be inside (or symlinked into) a colcon workspace's `src/`. If it isn't, create a symlink:

```bash
mkdir -p ~/colcon_ws/src
ln -s /home/neoplanetz/Documents/github/map_server_loader ~/colcon_ws/src/map_server_loader
```

All `colcon` commands below assume the workspace lives at `~/colcon_ws`. Substitute your own path if different.

---

## File Map

| File | Change | Tasks |
|---|---|---|
| [setup.py](../../../setup.py) | Replace two TODO strings | Task 1 |
| [launch/load_map_server.launch.py](../../../launch/load_map_server.launch.py) | Full rewrite to add 4 launch args + `bond_timeout: 0.0` | Task 2 |
| [README.md](../../../README.md) | Expand "구조" section, add launch arguments table + examples, add note about `image` relative path | Task 3 |

No new files. No deletions.

---

## Task 1: Fix setup.py Metadata

**Files:**
- Modify: `setup.py:25-26`

- [ ] **Step 1: Read current setup.py**

Run: `cat setup.py`
Expected: lines 25-26 contain `description='TODO: Package description',` and `license='TODO: License declaration',`.

- [ ] **Step 2: Replace the description field**

In `setup.py`, change:

```python
    description='TODO: Package description',
```

to:

```python
    description='Nav2 map_server launcher with bundled occupancy grid map',
```

- [ ] **Step 3: Replace the license field**

In `setup.py`, change:

```python
    license='TODO: License declaration',
```

to:

```python
    license='Apache-2.0',
```

- [ ] **Step 4: Verify both fields**

Run: `grep -n "description\|license" setup.py`
Expected output (line numbers may vary):

```
25:    description='Nav2 map_server launcher with bundled occupancy grid map',
26:    license='Apache-2.0',
```

No remaining `TODO` substrings on those lines.

- [ ] **Step 5: Commit**

```bash
git add setup.py
git commit -m "Fix setup.py metadata: replace TODO description and license"
```

---

## Task 2: Parameterize Launch File + Disable Bond

**Files:**
- Modify: `launch/load_map_server.launch.py` (full rewrite)

- [ ] **Step 1: Read current launch file**

Run: `cat launch/load_map_server.launch.py`
Expected: 35-line file with hardcoded `yaml_filename`, `use_sim_time=False`, `autostart=True`, no `bond_timeout`.

- [ ] **Step 2: Replace the entire launch file with the parameterized version**

Overwrite `launch/load_map_server.launch.py` with this exact content:

```python
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_dir = get_package_share_directory('map_server_loader')
    default_map_path = os.path.join(package_dir, 'maps', 'map.yaml')

    declare_map = DeclareLaunchArgument(
        'map',
        default_value=default_map_path,
        description='Full path to the map YAML file to load.',
    )
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true.',
    )
    declare_autostart = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically transition the lifecycle node to active on startup.',
    )
    declare_log_level = DeclareLaunchArgument(
        'log_level',
        default_value='info',
        description='Logging level (debug, info, warn, error, fatal).',
    )

    map_yaml = LaunchConfiguration('map')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    log_level = LaunchConfiguration('log_level')

    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{
            'yaml_filename': map_yaml,
            'use_sim_time': use_sim_time,
        }],
        arguments=['--ros-args', '--log-level', log_level],
    )

    lifecycle_manager_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_map_server',
        output='screen',
        parameters=[{
            'autostart': autostart,
            'node_names': ['map_server'],
            'use_sim_time': use_sim_time,
            'bond_timeout': 0.0,
        }],
        arguments=['--ros-args', '--log-level', log_level],
    )

    return LaunchDescription([
        declare_map,
        declare_use_sim_time,
        declare_autostart,
        declare_log_level,
        map_server_node,
        lifecycle_manager_node,
    ])
```

- [ ] **Step 3: Build the package**

Run:

```bash
cd ~/colcon_ws && colcon build --packages-select map_server_loader --symlink-install
```

Expected: `Summary: 1 package finished` with no errors. (`--symlink-install` lets later README/launch edits take effect without rebuilding.)

- [ ] **Step 4: Source the workspace**

Run: `source ~/colcon_ws/install/setup.bash`
Expected: no output, no errors.

- [ ] **Step 5: Verify all 4 launch arguments are exposed**

Run: `ros2 launch map_server_loader load_map_server.launch.py --show-args`
Expected: output lists exactly four arguments — `map`, `use_sim_time`, `autostart`, `log_level` — each with the default and description from Step 2. Example excerpt:

```
Arguments (pass arguments as '<name>:=<value>'):

    'map':
        Full path to the map YAML file to load.
        (default: '<...>/install/map_server_loader/share/map_server_loader/maps/map.yaml')

    'use_sim_time':
        Use simulation (Gazebo) clock if true.
        (default: 'false')
    ...
```

- [ ] **Step 6: Verify default (no-arg) run still publishes /map**

In one terminal, run:

```bash
ros2 launch map_server_loader load_map_server.launch.py
```

Expected console output includes: `[map_server]: ... yaml_filename:` followed by the bundled map path, then `[lifecycle_manager_map_server]: Managed nodes are active`.

In a second terminal:

```bash
source ~/colcon_ws/install/setup.bash
ros2 topic list | grep -E '^/map$'
ros2 topic echo /map --once --field info
```

Expected: `/map` appears in the topic list, and the `--once` echo prints map metadata (`width`, `height`, `resolution: 0.05`, `origin.position.x: -15.09`, etc.) matching [maps/map.yaml](../../../maps/map.yaml). Then Ctrl+C the launch terminal.

- [ ] **Step 7: Verify Ctrl+C does NOT print "Bond connection lost"**

Re-run the launch as in Step 6, wait for `Managed nodes are active`, then press Ctrl+C. Watch the shutdown output.

Expected: no line containing `Bond connection lost`. (Other shutdown logs from `map_server` and `lifecycle_manager` are fine.)

If a `Bond connection lost` line still appears, recheck that `'bond_timeout': 0.0` is present in the `lifecycle_manager_node` parameters dict.

- [ ] **Step 8: Verify the `map` argument can override the bundled map**

Create a temporary alternate map by copying the bundled one:

```bash
mkdir -p /tmp/altmap
cp ~/colcon_ws/install/map_server_loader/share/map_server_loader/maps/map.pgm /tmp/altmap/altmap.pgm
cat > /tmp/altmap/altmap.yaml <<'YAML'
image: altmap.pgm
mode: trinary
resolution: 0.050
origin: [0.0, 0.0, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
YAML
```

Then run:

```bash
ros2 launch map_server_loader load_map_server.launch.py map:=/tmp/altmap/altmap.yaml
```

Expected: `[map_server]: ... yaml_filename: /tmp/altmap/altmap.yaml` in the log, lifecycle reaches active, and in another terminal `ros2 topic echo /map --once --field info.origin.position.x` prints `0.0` (the alternate origin), confirming the override took effect. Ctrl+C to stop.

- [ ] **Step 9: Commit**

```bash
git add launch/load_map_server.launch.py
git commit -m "Parameterize launch file and disable lifecycle bond timeout

Expose map, use_sim_time, autostart, and log_level as DeclareLaunchArgument
so the same launch can serve different maps and environments without code
changes. Set bond_timeout: 0.0 on the lifecycle manager to remove the
'Bond connection lost' warning at shutdown — the bond's failure-detection
value is negligible for a single static map_server."
```

---

## Task 3: Update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read current README**

Run: `cat README.md`

Confirm the current "구조" section (lines 8-20), "실행" section (around lines 35-46), and "맵 설정" section (around lines 48-61) match the spec's description of the existing content.

- [ ] **Step 2: Replace the "구조" section**

Find the existing fenced block that starts with `map_server_loader/` and replace it with this expanded version (preserve the surrounding `## 구조` heading and surrounding blank lines):

````markdown
```
map_server_loader/
├── launch/
│   └── load_map_server.launch.py   # 런치 파일
├── map_server_loader/
│   └── __init__.py
├── maps/
│   ├── map.pgm                     # 점유 격자 맵 이미지
│   └── map.yaml                    # 맵 메타데이터
├── resource/
│   └── map_server_loader           # ament resource index 마커
├── test/                           # ament 린트 테스트 (flake8/pep257/copyright)
├── package.xml
├── setup.cfg
└── setup.py
```
````

- [ ] **Step 3: Replace the "실행" section**

Find the existing `## 실행` section (the part that runs from `## 실행` through the table ending with the `lifecycle_manager_map_server` row) and replace it with this expanded version:

````markdown
## 실행

```bash
ros2 launch map_server_loader load_map_server.launch.py
```

실행 시 다음 두 노드가 함께 시작됩니다:

| 노드 | 패키지 | 역할 |
|------|--------|------|
| `map_server` | nav2_map_server | 맵 YAML/PGM을 로드하여 맵 토픽 발행 |
| `lifecycle_manager_map_server` | nav2_lifecycle_manager | map_server의 라이프사이클 자동 관리 |

### 런치 인자

| 인자 | 기본값 | 설명 |
|------|--------|------|
| `map` | 패키지 동봉 [maps/map.yaml](maps/map.yaml) | 로드할 맵 YAML 파일의 절대경로 |
| `use_sim_time` | `false` | 시뮬레이터 시계 사용 여부 |
| `autostart` | `true` | 라이프사이클 자동 활성화 여부 |
| `log_level` | `info` | 양 노드의 로그 레벨 (`debug`/`info`/`warn`/`error`/`fatal`) |

#### 사용 예시

```bash
# 다른 맵 로드 (같은 디렉토리에 .yaml과 .pgm을 함께 두면 됨)
ros2 launch map_server_loader load_map_server.launch.py map:=/path/to/other.yaml

# 시뮬레이터 환경
ros2 launch map_server_loader load_map_server.launch.py use_sim_time:=true

# 라이프사이클 수동 제어 + 디버그 로그
ros2 launch map_server_loader load_map_server.launch.py autostart:=false log_level:=debug
```
````

- [ ] **Step 4: Add a note to the "맵 설정" section**

In the `## 맵 설정` section, immediately after the existing parameter table (after the `mode` row) and before the line `맵을 교체하려면 ...`, insert this paragraph:

```markdown
> `image` 필드는 YAML 파일이 위치한 디렉토리 기준 상대경로로 해석됩니다. 따라서 `map:=` 인자로 다른 YAML을 지정하면 같은 디렉토리의 `.pgm` 파일이 자동으로 로드됩니다.
```

- [ ] **Step 5: Verify the README renders correctly**

Run: `cat README.md`

Expected: the file now contains the expanded 구조 block, the new "런치 인자" subsection with 4 rows, the three usage examples, and the new note paragraph in 맵 설정. No duplicated headings.

Optional sanity check:

```bash
grep -c "^## " README.md
```
Expected: same heading count as before (the changes only edit existing sections, none added or removed).

- [ ] **Step 6: Commit**

```bash
git add README.md
git commit -m "Document launch arguments and refresh structure section in README"
```

---

## Task 4: Final Build + Lint Verification

**Files:** none (verification only)

- [ ] **Step 1: Clean build**

Run:

```bash
cd ~/colcon_ws && colcon build --packages-select map_server_loader
```

Expected: `Summary: 1 package finished` with 0 errors, 0 warnings related to `map_server_loader`.

- [ ] **Step 2: Run ament lint tests**

Run:

```bash
cd ~/colcon_ws && colcon test --packages-select map_server_loader
colcon test-result --verbose --test-result-base build/map_server_loader
```

Expected: all `flake8`, `pep257`, and `copyright` (skipped) tests pass. `Summary: 0 tests failed`.

If `flake8` complains about line length in the new launch file, fix the offending line and re-run from Step 1.

- [ ] **Step 3: Final smoke test**

Run:

```bash
source ~/colcon_ws/install/setup.bash
ros2 launch map_server_loader load_map_server.launch.py
```

Expected: identical default behavior to before this work — `/map` published, lifecycle becomes active, no `Bond connection lost` on Ctrl+C.

- [ ] **Step 4: Confirm clean git state**

Run: `git status`
Expected: `nothing to commit, working tree clean`. Three commits should appear in `git log --oneline -3`:

```
<hash> Document launch arguments and refresh structure section in README
<hash> Parameterize launch file and disable lifecycle bond timeout
<hash> Fix setup.py metadata: replace TODO description and license
```

---

## Done When

All of the following are true:

- `setup.py` no longer contains the string `TODO`.
- `ros2 launch map_server_loader load_map_server.launch.py --show-args` lists exactly `map`, `use_sim_time`, `autostart`, `log_level`.
- No-arg `ros2 launch ...` publishes `/map` with the bundled map's metadata (origin `[-15.09, -25.17, 0]`).
- `map:=/tmp/altmap/altmap.yaml` override is honored (origin becomes `[0, 0, 0]`).
- Ctrl+C shutdown does NOT print `Bond connection lost`.
- `colcon build` and `colcon test` both pass cleanly.
- README's "구조" section lists `resource/`, `setup.cfg`, `test/`. README has a new "런치 인자" subsection with 4 rows and 3 usage examples. README's "맵 설정" section notes the `image` relative-path behavior.

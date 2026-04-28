# map_server_loader 패키지 개선 설계

**날짜:** 2026-04-28
**대상 패키지:** `map_server_loader`
**범위:** 메타데이터 정리, launch 인자화, 라이프사이클 매니저 안정화, 문서 갱신

## 배경

`map_server_loader`는 Nav2의 `map_server`와 `lifecycle_manager`를 묶어 사전 제작된 점유 격자 맵을 즉시 서빙하는 얇은 런처 패키지다. 현재 동작에는 문제가 없으나 다음 4가지 개선 여지가 있어 한 번에 정리한다.

1. [setup.py](../../../setup.py)의 `description`/`license` 필드가 `'TODO: ...'`로 남아 [package.xml](../../../package.xml)과 불일치
2. [launch/load_map_server.launch.py](../../../launch/load_map_server.launch.py)의 모든 파라미터가 하드코딩되어 다른 맵/시뮬레이터 환경 재사용 불가
3. `lifecycle_manager`의 `bond_timeout` 미지정으로 종료 시 `Bond connection lost` 경고 발생
4. [README.md](../../../README.md)의 "구조" 섹션이 일부 디렉토리(`resource/`, `setup.cfg`, `test/`)를 누락하고, 새로 도입할 launch 인자 사용법이 문서화되지 않음

## 비목표 (Non-Goals)

- 새로운 노드/실행 파일 추가 없음
- 의존성 패키지 변경 없음
- `launch_testing` 기반 통합 테스트 추가는 본 작업 범위 외 (별도 향후 과제)
- 멀티로봇 네임스페이스, 외부 `params_file` 오버라이드 등 고급 기능은 YAGNI로 제외

## 변경사항

### A. setup.py 메타데이터 정리

**파일:** [setup.py](../../../setup.py)

| 필드 | 변경 전 | 변경 후 |
|------|---------|---------|
| `description` | `'TODO: Package description'` | `'Nav2 map_server launcher with bundled occupancy grid map'` |
| `license` | `'TODO: License declaration'` | `'Apache-2.0'` |

[package.xml](../../../package.xml)의 기존 값과 일치시킨다.

### B. Launch 파일 인자화

**파일:** [launch/load_map_server.launch.py](../../../launch/load_map_server.launch.py)

`DeclareLaunchArgument`로 4개 인자를 노출한다:

| 인자 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `map` | string (path) | `<share>/maps/map.yaml` (패키지 동봉 맵) | 로드할 맵 YAML 파일의 절대경로 |
| `use_sim_time` | bool | `false` | 시뮬레이터 시계 사용 여부 |
| `autostart` | bool | `true` | 라이프사이클 자동 활성화 여부 |
| `log_level` | string | `info` | 양 노드의 로그 레벨 (`debug`/`info`/`warn`/`error`/`fatal`) |

**파라미터 주입 방식:**
- `map` → `map_server`의 `yaml_filename` 파라미터
- `use_sim_time` → 양 노드 모두에 주입
- `autostart` → `lifecycle_manager`의 `autostart` 파라미터
- `log_level` → 양 노드의 `arguments=['--ros-args', '--log-level', LaunchConfiguration('log_level')]`로 전달

**하위호환성:** 무인자 실행 (`ros2 launch map_server_loader load_map_server.launch.py`) 시 동작은 변경 전과 동일하다.

**맵 교체 동작 참고:** `nav2_map_server`는 YAML의 `image` 필드를 YAML 파일이 위치한 디렉토리 기준 상대경로로 해석한다. 따라서 `map:=/path/to/foo.yaml`만 지정하면 같은 디렉토리의 `foo.pgm`이 자동으로 로드된다.

### C. bond_timeout 비활성화

**파일:** [launch/load_map_server.launch.py](../../../launch/load_map_server.launch.py)

`lifecycle_manager`의 파라미터 dict에 `'bond_timeout': 0.0`을 추가하여 bond 메커니즘을 비활성화한다.

**근거:** 본 패키지는 단일 `map_server`만 관리하며 자동 복구 로직이 없으므로 bond 알림의 실용 가치가 낮다. 종료 시 노이즈 제거가 더 큰 가치를 가진다.

### D. README 갱신

**파일:** [README.md](../../../README.md)

1. **"구조" 섹션** — 누락된 항목 추가:
   ```
   ├── resource/
   │   └── map_server_loader        # ament resource index 마커
   ├── setup.cfg
   └── test/                        # ament 린트 테스트 (flake8/pep257/copyright)
   ```

2. **"실행" 섹션 확장** — 런치 인자 표 + 사용 예시 추가:
   - 인자 4개의 이름/기본값/설명 표
   - 다른 맵 로드 예시: `map:=/path/to/other.yaml`
   - 시뮬레이터 환경 예시: `use_sim_time:=true`
   - 디버깅 예시: `autostart:=false log_level:=debug`

3. **"맵 설정" 섹션** — YAML 내 `image` 필드의 상대경로 동작에 대한 한 줄 메모 추가 (다른 맵 교체 시 혼동 방지).

## 검증 기준

작업 완료 시 다음 모두 충족해야 한다:

1. **빌드:** `colcon build --packages-select map_server_loader` 성공
2. **린트:** 기존 ament 린트 테스트 (`flake8`, `pep257`) 통과
3. **무인자 실행 동작 보존:** `ros2 launch map_server_loader load_map_server.launch.py` 실행 시 `/map` 토픽이 latched로 발행됨
4. **인자 동작:** `ros2 launch map_server_loader load_map_server.launch.py --show-args`로 4개 인자가 노출되는지 확인
5. **종료 시 경고 제거:** Ctrl+C 종료 시 `Bond connection lost` 경고가 더 이상 출력되지 않음

## 변경되지 않는 것

- 패키지 디렉토리 구조 (디렉토리 추가/제거 없음)
- 의존성 (`package.xml` 변경 없음)
- 동봉 맵 파일 ([maps/map.yaml](../../../maps/map.yaml), [maps/map.pgm](../../../maps/map.pgm))
- 테스트 파일 ([test/](../../../test/))
- 노드 이름 (`map_server`, `lifecycle_manager_map_server`)

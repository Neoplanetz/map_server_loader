# ROS2 Map Server Loader

Nav2 map_server를 lifecycle manager와 함께 실행하는 ROS2 패키지입니다.
사전 구성된 맵 파일(PGM + YAML)을 번들로 포함하고 있어, 별도 설정 없이 바로 맵 서버를 띄울 수 있습니다.

## 구조

```
map_server_loader/
├── launch/
│   └── load_map_server.launch.py   # 런치 파일
├── map_server_loader/
│   └── __init__.py
├── maps/
│   ├── map.pgm                     # 점유 격자 맵 이미지
│   └── map.yaml                    # 맵 메타데이터
├── package.xml
├── setup.py
└── setup.cfg
```

## 의존성

- `nav2_map_server`
- `nav2_lifecycle_manager`

## 빌드

```bash
cd ~/colcon_ws
colcon build --packages-select map_server_loader
source install/setup.bash
```

## 실행

```bash
ros2 launch map_server_loader load_map_server.launch.py
```

실행 시 다음 두 노드가 함께 시작됩니다:

| 노드 | 패키지 | 역할 |
|------|--------|------|
| `map_server` | nav2_map_server | 맵 YAML/PGM을 로드하여 맵 토픽 발행 |
| `lifecycle_manager_map_server` | nav2_lifecycle_manager | map_server의 라이프사이클 자동 관리 |

## 맵 설정

[maps/map.yaml](maps/map.yaml) 파일에서 맵 파라미터를 확인/수정할 수 있습니다.

| 파라미터 | 값 | 설명 |
|---------|-----|------|
| `image` | map.pgm | 점유 격자 이미지 파일 |
| `resolution` | 0.05 | 셀당 해상도 (m/pixel) |
| `origin` | [-15.09, -25.172, 0] | 맵 원점 좌표 (x, y, yaw) |
| `occupied_thresh` | 0.65 | 점유 판정 임계값 |
| `free_thresh` | 0.196 | 자유 공간 판정 임계값 |
| `mode` | trinary | 점유/자유/미지 3값 모드 |

맵을 교체하려면 `maps/` 디렉토리의 `.pgm`과 `.yaml` 파일을 교체하면 됩니다.

## 라이선스

Apache-2.0

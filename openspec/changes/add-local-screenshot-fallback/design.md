# 本地截图文件备用方案设计文档

## 问题分析

### 当前数据流
```
任务报告页面 → 调用API → get_step_report_data() → 查询数据库 → 返回截图数据
                                    ↓
                            如果数据库为空 → 返回空结果
```

### 问题定位
1. **数据库断层**：`task_steps`表中`screenshot_path`和`screenshot_url`字段为空
2. **step_screenshots表**：完全为空，无任何数据
3. **本地资源浪费**：269个截图文件存在但未被利用
4. **数据获取失败**：前端显示"暂无执行截图"

### 文件命名规律分析
通过分析本地截图文件名：
```
screenshot_20251214_222529_098_9fa22334.png
screenshot_20251215_121943_558_7fb3612d.png
screenshot_20251215_153713_657_ea64311d.png
```

格式解析：`screenshot_YYYYMMDD_HHMMSS_milliseconds_hash.png`

## 技术架构设计

### 1. 整体架构

#### 1.1 数据获取层次
```
Level 1: step_screenshots表（结构化数据）
Level 2: task_steps表的screenshot_path/screenshot_url字段
Level 3: 本地文件系统扫描（备用方案）
```

#### 1.2 核心组件
```
LocalFileScanner     - 本地文件扫描器
ScreenshotMatcher    - 智能匹配算法
PathConverter        - 路径转换器
DataAggregator       - 数据聚合器
```

### 2. LocalFileScanner 设计

#### 2.1 文件扫描策略
```python
class LocalFileScanner:
    def __init__(self, screenshots_dir: str = "static/screenshots"):
        self.screenshots_dir = screenshots_dir
        self.file_cache = {}  # 缓存扫描结果

    def scan_screenshots(self) -> List[FileInfo]:
        """扫描本地截图文件"""
        files = []
        for file_path in Path(self.screenshots_dir).glob("screenshot_*.png"):
            file_info = self.parse_filename(file_path)
            if file_info:
                files.append(file_info)
        return sorted(files, key=lambda x: x.timestamp)

    def parse_filename(self, file_path: Path) -> Optional[FileInfo]:
        """解析文件名提取时间戳信息"""
        # screenshot_20251214_222529_098_9fa22334.png
        pattern = r"screenshot_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})_(\d{3})_"
        match = re.search(pattern, file_path.name)
        if match:
            year, month, day, hour, minute, second, millisecond = map(int, match.groups())
            timestamp = datetime(year, month, day, hour, minute, second, millisecond * 1000)
            return FileInfo(
                path=str(file_path),
                timestamp=timestamp,
                size=file_path.stat().st_size,
                name=file_path.name
            )
        return None
```

#### 2.2 数据结构
```python
@dataclass
class FileInfo:
    path: str           # 本地文件路径
    timestamp: datetime # 文件创建时间
    size: int          # 文件大小
    name: str          # 文件名
    url: Optional[str] = None  # Web可访问URL
```

### 3. ScreenshotMatcher 设计

#### 3.1 匹配算法
```python
class ScreenshotMatcher:
    def __init__(self, time_window_minutes: int = 10):
        self.time_window = timedelta(minutes=time_window_minutes)

    def match_screenshots_to_task(self,
                                task_info: dict,
                                local_files: List[FileInfo]) -> List[FileInfo]:
        """将本地截图文件匹配到任务"""
        task_created = task_info.get('created_at')
        task_completed = task_info.get('completed_at')

        if not task_created:
            return []

        # 计算任务执行时间范围
        start_time = self._parse_datetime(task_created)
        end_time = self._parse_datetime(task_completed) or datetime.now()

        # 扩展时间窗口以包含相关的截图
        extended_start = start_time - self.time_window
        extended_end = end_time + self.time_window

        # 匹配在时间范围内的截图
        matched_files = []
        for file_info in local_files:
            if extended_start <= file_info.timestamp <= extended_end:
                file_info.match_score = self._calculate_match_score(
                    file_info.timestamp, start_time, end_time
                )
                matched_files.append(file_info)

        return sorted(matched_files, key=lambda x: x.match_score, reverse=True)
```

#### 3.2 匹配评分算法
```python
def _calculate_match_score(self, file_timestamp: datetime,
                          task_start: datetime, task_end: datetime) -> float:
    """计算文件与任务的匹配度"""
    if task_start <= file_timestamp <= task_end:
        return 1.0  # 完美匹配：在任务执行期间

    # 计算到任务时间范围的距离
    if file_timestamp < task_start:
        distance = (task_start - file_timestamp).total_seconds()
    else:
        distance = (file_timestamp - task_end).total_seconds()

    # 距离越近分数越高
    max_distance = self.time_window.total_seconds()
    score = max(0, 1 - (distance / max_distance))

    return score
```

### 4. PathConverter 设计

#### 4.1 路径转换逻辑
```python
class PathConverter:
    def __init__(self, base_url: str = "/static/screenshots"):
        self.base_url = base_url.rstrip('/')

    def convert_to_web_url(self, local_path: str) -> str:
        """将本地文件路径转换为Web URL"""
        # /Users/.../web/static/screenshots/screenshot.png
        # → /static/screenshots/screenshot.png

        filename = Path(local_path).name
        return f"{self.base_url}/{filename}"

    def validate_file_exists(self, local_path: str) -> bool:
        """验证文件是否存在且可访问"""
        return Path(local_path).exists() and Path(local_path).is_file()
```

### 5. DataAggregator 设计

#### 5.1 数据聚合策略
```python
class DataAggregator:
    def aggregate_screenshot_data(self,
                                task_id: str,
                                db_screenshots: List[dict],
                                task_steps: List[dict],
                                local_files: List[dict]) -> List[dict]:
        """聚合来自不同源的截图数据"""

        # 1. 收集所有截图数据
        all_screenshots = []

        # 来源1: step_screenshots表
        for screenshot in db_screenshots:
            all_screenshots.append({
                'screenshot_path': screenshot.get('screenshot_path'),
                'screenshot_url': screenshot.get('screenshot_url'),
                'source': 'database_table',
                'priority': 1,
                **screenshot
            })

        # 来源2: task_steps中的截图路径
        for step in task_steps:
            if step.get('screenshot_path') or step.get('screenshot_url'):
                all_screenshots.append({
                    'screenshot_path': step.get('screenshot_path'),
                    'screenshot_url': step.get('screenshot_url'),
                    'source': 'task_steps',
                    'priority': 2,
                    'step_number': step.get('step_number'),
                    **step
                })

        # 来源3: 本地文件扫描
        for file_info in local_files:
            all_screenshots.append({
                'screenshot_path': file_info.get('local_path'),
                'screenshot_url': file_info.get('web_url'),
                'source': 'local_file',
                'priority': 3,
                'file_size': file_info.get('size'),
                'match_score': file_info.get('match_score', 0),
                'created_at': file_info.get('timestamp').isoformat(),
            })

        # 2. 去重处理
        unique_screenshots = self._deduplicate_screenshots(all_screenshots)

        # 3. 排序（按优先级和时间）
        sorted_screenshots = sorted(
            unique_screenshots,
            key=lambda x: (x['priority'], x.get('created_at', '')),
            reverse=False
        )

        return sorted_screenshots
```

#### 5.2 去重算法
```python
def _deduplicate_screenshots(self, screenshots: List[dict]) -> List[dict]:
    """去除重复的截图数据"""
    seen = set()
    unique_screenshots = []

    for screenshot in screenshots:
        # 使用文件路径或URL作为去重标识
        identifier = (
            screenshot.get('screenshot_path') or
            screenshot.get('screenshot_url') or
            ''
        )

        if identifier and identifier not in seen:
            seen.add(identifier)
            unique_screenshots.append(screenshot)
        elif not identifier:  # 没有路径信息，保留
            unique_screenshots.append(screenshot)

    return unique_screenshots
```

### 6. 集成到现有系统

#### 6.1 修改 get_step_report_data 函数
```python
def get_step_report_data(self, task_id: str) -> Dict[str, Any]:
    """增强的任务报告数据获取，支持本地文件回退"""
    try:
        # 现有的数据库查询逻辑...

        # 新增：本地文件扫描和匹配
        if not all_screenshots:  # 只有当数据库无数据时才扫描本地文件
            local_screenshots = self._get_local_screenshots_fallback(task_id, task_data)
            if local_screenshots:
                all_screenshots.extend(local_screenshots)
                logger.info(f"[DataExtraction] 本地文件回退: {len(local_screenshots)} 张截图")

        return {
            'task': task_data,
            'steps': steps_result.data if steps_result.data else [],
            'screenshots': all_screenshots
        }

    except Exception as e:
        # 现有的错误处理逻辑...

def _get_local_screenshots_fallback(self, task_id: str, task_info: dict) -> List[dict]:
    """本地文件回退获取截图"""
    if not task_info:
        return []

    # 1. 扫描本地文件
    scanner = LocalFileScanner()
    local_files = scanner.scan_screenshots()

    # 2. 匹配到任务
    matcher = ScreenshotMatcher()
    matched_files = matcher.match_screenshots_to_task(task_info, local_files)

    # 3. 转换路径和格式
    converter = PathConverter()
    result = []

    for file_info in matched_files[:50]:  # 限制最多50张截图
        if converter.validate_file_exists(file_info.path):
            screenshot_data = {
                'local_path': file_info.path,
                'web_url': converter.convert_to_web_url(file_info.path),
                'created_at': file_info.timestamp.isoformat(),
                'file_size': file_info.size,
                'match_score': file_info.match_score,
                'source': 'local_fallback'
            }
            result.append(screenshot_data)

    return result
```

### 7. 性能优化考虑

#### 7.1 缓存机制
```python
@functools.lru_cache(maxsize=100)
def get_cached_local_files(self, cache_key: str) -> List[FileInfo]:
    """缓存本地文件扫描结果"""
    # cache_key可以基于目录修改时间
    scanner = LocalFileScanner()
    return scanner.scan_screenshots()
```

#### 7.2 异步加载
```python
async def get_local_screenshots_async(self, task_id: str) -> List[dict]:
    """异步获取本地截图，避免阻塞主流程"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, self._get_local_screenshots_fallback, task_id)
```

#### 7.3 分页支持
```python
def get_local_screenshots_paginated(self, task_id: str, page: int = 1, per_page: int = 20):
    """分页获取本地截图"""
    all_screenshots = self._get_local_screenshots_fallback(task_id)
    start = (page - 1) * per_page
    end = start + per_page
    return all_screenshots[start:end]
```

### 8. 错误处理和日志

#### 8.1 错误处理
```python
def _handle_local_file_errors(self, error: Exception, context: str):
    """处理本地文件相关错误"""
    if isinstance(error, FileNotFoundError):
        logger.warning(f"[LocalFile] 目录不存在: {context}")
    elif isinstance(error, PermissionError):
        logger.error(f"[LocalFile] 权限不足: {context}")
    else:
        logger.error(f"[LocalFile] 未知错误: {context} - {error}")
```

#### 8.2 详细日志
```python
def _log_matching_results(self, task_id: str, matched_count: int, total_files: int):
    """记录匹配结果统计"""
    logger.info(f"[LocalFile] 任务 {task_id[:8]} 截图匹配结果:")
    logger.info(f"  - 本地文件总数: {total_files}")
    logger.info(f"  - 匹配文件数量: {matched_count}")
    logger.info(f"  - 匹配率: {matched_count/total_files*100:.1f}%" if total_files > 0 else "  - 匹配率: 0%")
```

这个设计方案提供了完整的本地文件回退机制，确保即使数据库中没有截图数据，用户也能看到相关的执行截图。
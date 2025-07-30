"""
MCP Server Template

이 템플릿은 Model Context Protocol (MCP) 서버를 빠르게 개발하기 위한 기본 구조를 제공합니다.

사용법:
1. SERVER_NAME을 원하는 서버 이름으로 변경
2. 필요한 상수들을 Constants 섹션에 추가
3. 유틸리티 함수들을 Helper Functions 섹션에 구현
4. @mcp.tool() 데코레이터를 사용해서 도구들을 추가

예시:
- 외부 데이터가 필요한 경우: fetch_external_data 함수 참고
- 데이터 포맷팅이 필요한 경우: format_data 함수 참고
"""

from typing import Any, List
from mcp.server.fastmcp import FastMCP
# TODO: 필요한 라이브러리들을 여기에 추가하세요
# 예시:
# import httpx          # HTTP 요청
# import sqlite3        # SQLite 데이터베이스
# import json           # JSON 처리
import os             # 파일 시스템

# =============================================================================
# 서버 초기화
# =============================================================================
# TODO: "your-server-name"을 실제 서버 이름으로 변경하세요
mcp = FastMCP("mcp-linux-filesystem")

# =============================================================================
# 상수 (Constants)
# =============================================================================
# TODO: 필요한 상수들을 여기에 추가하세요
# 예시:
# API_BASE_URL = "https://api.example.com"
# USER_AGENT = "your-app/1.0"
# DEFAULT_TIMEOUT = 30.0

# =============================================================================
# 헬퍼 함수들 (Helper Functions)
# =============================================================================

async def get_all_entries_in_path(path: str, **kwargs) -> List[str]:
    """
    지정된 경로의 전체 파일 및 디렉터리 정보를 'ls -al' 스타일로 반환합니다.

    Args:
        path: 파일 시스템 경로 (예: "/home/user")

    Returns:
        각 엔트리별 상세 정보가 담긴 문자열 리스트 (ls -al 한 줄씩)
        오류 발생 시 빈 리스트 반환
    """
    import pwd, grp, stat, time
    result = []
    try:
        entries = [".", ".."] + [e for e in os.listdir(path)]
        for entry in entries:
            try:
                full_path = os.path.join(path, entry)
                st = os.lstat(full_path)
                mode = stat.filemode(st.st_mode)
                nlink = st.st_nlink
                uid = st.st_uid
                gid = st.st_gid
                size = st.st_size
                mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))
                user = pwd.getpwuid(uid).pw_name if hasattr(pwd, 'getpwuid') else str(uid)
                group = grp.getgrgid(gid).gr_name if hasattr(grp, 'getgrgid') else str(gid)
                line = f"{mode} {nlink} {user} {group} {size:>8} {mtime} {entry}"
                result.append(line)
            except Exception as e:
                result.append(f"[ERROR] {entry}: {e}")
        return result
    except Exception as e:
        return [f"[ERROR] {e}"]

# =============================================================================
# MCP 도구들 (Tools)
# =============================================================================
# 
# MCP 도구 작성 가이드라인:
# 1. 도구명은 동사_명사 형태로 명확하게 (예: get_weather, search_files, create_report)
# 2. docstring 필수 구조 (LLM 판단을 위한 핵심 정보):
#    [도구 역할]: 이 도구가 담당하는 핵심 역할을 한 문장으로 명시
#    [정확한 기능]: 구체적으로 수행하는 기능들을 나열
#    [필수 사용 상황]: LLM이 이 도구를 선택해야 하는 명확한 트리거 조건들
#    [절대 사용 금지 상황]: 이 도구를 사용하면 안 되는 상황들
#    [입력 제약 조건]: 매개변수의 형식, 범위, 제약사항
#    Args/Returns: 구체적인 형식과 예시
# 3. 실제 사용자 문구나 키워드를 포함하여 LLM이 정확히 매칭할 수 있도록 작성
# 4. 다른 도구와의 구분을 위해 고유한 역할 영역을 명확히 정의

@mcp.tool()
async def list_directory_entries(path: str) -> List[str]:
    """
    [Tool Role]: Tool for retrieving detailed information about all files and directories in a specific Linux filesystem path.

    [Exact Functionality]:
    - Returns a list of files and directories in the specified path in 'ls -al' style
    - Provides detailed info for each entry: permissions, owner, group, size, modification time, etc.
    - Includes all entries, including hidden files (starting with .)

    [Required Usage Situations]:
    - When the user requests to view folder contents, directory listing, 'ls -al', or file list
    - When detailed info about files/folders in a specific path is needed

    [Prohibited Usage Situations]:
    - For reading, modifying, or deleting file contents (only listing is allowed)
    - When the path is empty or invalid
    - For information outside the filesystem (e.g., network, DB)

    [Input Constraints]:
    - path must be a valid filesystem path
    - Empty string, None, or non-existent paths are not allowed
    - Both relative and absolute paths are allowed

    Args:
        path: [Role: Directory path to list] - e.g., "/home/user", "./data"

    Returns:
        [Return Value Role]: List of strings, each with detailed info per entry (one line per 'ls -al' style)
        On success: ["drwxr-xr-x 2 user group    4096 2024-06-01 12:34 .", ...]
        On error: ["[ERROR] ..."]
    """
    return await get_all_entries_in_path(path)

# =============================================================================
# 서버 실행
# =============================================================================

if __name__ == "__main__":
    """
    서버를 시작합니다.
    
    사용법:
    1. 개발 중에는 stdio 전송을 사용: mcp.run(transport='stdio')
    2. 프로덕션에서는 필요에 따라 다른 전송 방식 사용
    
    주의: 실제 배포 전에 모든 TODO 항목들을 완료하세요!
    """
    mcp.run(transport='stdio')

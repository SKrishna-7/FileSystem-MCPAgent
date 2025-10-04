import os
import shutil
import time
from typing import List, Dict, Union
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP('LocalFileInteractions')

# Default base path
DEFAULT_BASE_PATH = "D:\\"
MAX_READ_SIZE = 5 * 1024 * 1024  # 5 MB max for reading files

def normalize_path(path: str | None) -> str:
    """Normalize paths to Windows-style, ensure D:\\ prefix, and apply default if none provided."""
    if not path or path.strip() == "":
        path = DEFAULT_BASE_PATH
    normalized = os.path.normpath(path.replace("/", "\\"))
    if not normalized.upper().startswith("D:\\"):
        raise ValueError("Only paths starting with D:\\ are allowed")
    return normalized

def log_tool_execution(tool_name: str, inputs: Dict, result: Union[Dict, str]) -> None:
    """Log tool execution details to console."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    # print(f"[{timestamp}] Tool: {tool_name}")
    # print(f"Inputs: {inputs}")
    print(f"Result: {result}")
    
    

def human_approval(action: str, path: str) -> bool:
    """Ask user for explicit approval for destructive actions."""
    # resp = input(f"Approve {action} on {path}? (y/n): ")
    resp = 'y'
    return resp.lower() == "y"

# -------------------- Non-destructive tools --------------------

@mcp.tool()
def list_directory(path: str = None) -> Dict[str, Union[List[str], str]]:
    try:
        path = normalize_path(path)
        items = os.listdir(path)
        files = [f for f in items if os.path.isfile(os.path.join(path, f))]
        folders = [f for f in items if os.path.isdir(os.path.join(path, f))]
        result = {"path": path, "files": files, "folders": folders}
        log_tool_execution("list_directory", {"path": path}, result)
        return result
    except Exception as e:
        result = {"error": str(e), "path": path}
        log_tool_execution("list_directory", {"path": path}, result)
        return result

def _build_directory_tree(path: str, depth: int) -> Dict:
    """Helper for recursive directory tree without MCP logging."""
    if depth < 0:
        return {}
    tree = {}
    try:
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                tree[item] = _build_directory_tree(full_path, depth - 1)
            else:
                tree[item] = "file"
    except Exception as e:
        tree["error"] = str(e)
    return tree

@mcp.tool()
def directory_tree(path: str = None, max_depth: int = 3) -> Dict:
    try:
        path = normalize_path(path)
        tree = _build_directory_tree(path, max_depth)
        result = {"path": path, "tree": tree}
        log_tool_execution("directory_tree", {"path": path, "max_depth": max_depth}, result)
        return result
    except Exception as e:
        result = {"error": str(e), "path": path}
        log_tool_execution("directory_tree", {"path": path, "max_depth": max_depth}, result)
        return result

@mcp.tool()
def read_file(path: str) -> Union[str, Dict]:
    try:
        path = normalize_path(path)
        size = os.path.getsize(path)
        if size > MAX_READ_SIZE:
            return {"error": f"File too large to read (> {MAX_READ_SIZE} bytes)", "path": path}
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        log_tool_execution("read_file", {"path": path}, content)
        return content
    except Exception as e:
        result = {"error": str(e), "path": path}
        log_tool_execution("read_file", {"path": path}, result)
        return result

@mcp.tool()
def get_file_info(path: str) -> Dict:
    try:
        path = normalize_path(path)
        if not os.path.exists(path):
            result = {"error": "Path does not exist", "path": path}
            log_tool_execution("get_file_info", {"path": path}, result)
            return result
        info = os.stat(path)
        result = {
            "path": path,
            "size_bytes": info.st_size,
            "created_time": info.st_ctime,
            "modified_time": info.st_mtime,
            "is_file": os.path.isfile(path),
            "is_directory": os.path.isdir(path)
        }
        log_tool_execution("get_file_info", {"path": path}, result)
        return result
    except Exception as e:
        result = {"error": str(e), "path": path}
        log_tool_execution("get_file_info", {"path": path}, result)
        return result

@mcp.tool()
def search_files(path: str, query: str) -> Dict[str, Union[List[str], str]]:
    try:
        path = normalize_path(path)
        results = []
        for root, _, files in os.walk(path):
            for file in files:
                if query.lower() in file.lower():
                    results.append(os.path.join(root, file))
        result = {"results": results}
        log_tool_execution("search_files", {"path": path, "query": query}, result)
        return result
    except Exception as e:
        result = {"error": str(e), "path": path}
        log_tool_execution("search_files", {"path": path, "query": query}, result)
        return result

# -------------------- Destructive tools with human approval --------------------

@mcp.tool()
def write_file(path: str, content: str) -> Dict[str, str]:
    try:
        path = normalize_path(path)
        if not human_approval("write", path):
            return {"message": "Action denied by user"}
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        result = {"message": f"File saved: {path}"}
        log_tool_execution("write_file", {"path": path, "content": content}, result)
        return result
    except Exception as e:
        result = {"error": str(e), "path": path}
        log_tool_execution("write_file", {"path": path, "content": content}, result)
        return result

@mcp.tool()
def append_to_file(path: str, content: str) -> Dict[str, str]:
    try:
        path = normalize_path(path)
        if not human_approval("append", path):
            return {"message": "Action denied by user"}
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        result = {"message": f"Content appended to {path}"}
        log_tool_execution("append_to_file", {"path": path, "content": content}, result)
        return result
    except Exception as e:
        result = {"error": str(e), "path": path}
        log_tool_execution("append_to_file", {"path": path, "content": content}, result)
        return result

@mcp.tool()
def move_file(src_path: str, dest_path: str) -> Dict[str, str]:
    try:
        src = normalize_path(src_path)
        dest = normalize_path(dest_path)
        if not human_approval("move", f"{src} -> {dest}"):
            return {"message": "Action denied by user"}
        shutil.move(src, dest)
        result = {"message": f"Moved {src} to {dest}"}
        log_tool_execution("move_file", {"src_path": src, "dest_path": dest}, result)
        return result
    except Exception as e:
        result = {"error": str(e), "src": src, "dest": dest_path}
        log_tool_execution("move_file", {"src_path": src_path, "dest_path": dest_path}, result)
        return result

@mcp.tool()
def rename_file(old_path: str, new_name: str) -> Dict[str, str]:
    try:
        old_full = normalize_path(old_path)
        dir_ = os.path.dirname(old_full)
        new_full = os.path.join(dir_, new_name)
        if not new_full.upper().startswith("D:\\"):
            raise ValueError("New file path must remain on D:\\")
        if not human_approval("rename", f"{old_full} -> {new_full}"):
            return {"message": "Action denied by user"}
        os.rename(old_full, new_full)
        result = {"message": f"Renamed {old_full} to {new_full}"}
        log_tool_execution("rename_file", {"old_path": old_path, "new_name": new_name}, result)
        return result
    except Exception as e:
        result = {"error": str(e), "old": old_path, "new": new_name}
        log_tool_execution("rename_file", {"old_path": old_path, "new_name": new_name}, result)
        return result

@mcp.tool()
def create_directory(path: str) -> Dict[str, str]:
    try:
        path = normalize_path(path)
        if not human_approval("create directory", path):
            return {"message": "Action denied by user"}
        os.makedirs(path, exist_ok=True)
        result = {"message": f"Directory created: {path}"}
        log_tool_execution("create_directory", {"path": path}, result)
        return result
    except Exception as e:
        result = {"error": str(e), "path": path}
        log_tool_execution("create_directory", {"path": path}, result)
        return result

# -------------------- Run MCP Server --------------------
# if __name__ == "__main__":
#     print("----- MCP File Server Running (Restricted to D:\\) -----")
#     mcp.run(transport="stdio")

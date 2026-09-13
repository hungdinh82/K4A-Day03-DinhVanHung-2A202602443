"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
"""

import json
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Tra cứu tiêu chí tuyển dụng theo vị trí
    {
        "name": "job_criteria_query",
        "description": "Tra cứu tiêu chí tuyển dụng chính thức cho một vị trí đang mở.",
        "parameters": {
            "type": "object",
            "properties": {
                "position_title": {
                    "type": "string",
                    "description": "Tên vị trí tuyển dụng cần tra cứu (ví dụ: 'Data Analyst')"
                }
            },
            "required": ["position_title"]
        }
    },

    # Tool 2: Gửi thông báo lịch phỏng vấn cho ứng viên đạt yêu cầu
    {
        "name": "send_interview_notification",
        "description": "Gửi thông báo mời phỏng vấn cho ứng viên đã được sàng lọc đạt yêu cầu.",
        "parameters": {
            "type": "object",
            "properties": {
                "candidate_name": {
                    "type": "string",
                    "description": "Họ và tên ứng viên"
                },
                "email": {
                    "type": "string",
                    "description": "Email nhận thông báo phỏng vấn"
                },
                "position_title": {
                    "type": "string",
                    "description": "Vị trí ứng tuyển"
                },
                "datetime_str": {
                    "type": "string",
                    "description": "Thời gian phỏng vấn (ví dụ: '14:00 15/09/2026')"
                },
                "interviewer_name": {
                    "type": "string",
                    "description": "Họ tên người phỏng vấn"
                }
            },
            "required": [
                "candidate_name",
                "email",
                "position_title",
                "datetime_str",
                "interviewer_name"
            ]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_DATABASE = {
    "Data Analyst": {
        "minimum_experience_years": 1,
        "required_skills": ["SQL", "Python", "Power BI"],
        "preferred_skills": ["Statistics", "Tableau"],
        "education": "Đại học chuyên ngành phù hợp hoặc kinh nghiệm tương đương",
        "summary": "Phân tích dữ liệu, xây dựng dashboard và trình bày insight cho các bên liên quan."
    },
    "AI Engineer": {
        "minimum_experience_years": 2,
        "required_skills": ["Python", "Machine Learning", "Docker"],
        "preferred_skills": ["MLOps", "Cloud"],
        "education": "Đại học chuyên ngành CNTT, AI hoặc tương đương",
        "summary": "Xây dựng, triển khai và vận hành các hệ thống AI/ML."
    }
}


def execute_job_criteria_query(position_title: str) -> str:
    """Tra cứu tiêu chí tuyển dụng theo tên vị trí, không phân biệt hoa thường."""
    normalized_title = position_title.strip().casefold()
    matched_title = next(
        (title for title in MOCK_DATABASE if title.casefold() == normalized_title),
        None,
    )
    if matched_title:
        return json.dumps({
            "status": "SUCCESS",
            "position_title": matched_title,
            "data": MOCK_DATABASE[matched_title]
        }, ensure_ascii=False)
    return json.dumps({
        "status": "NOT_FOUND",
        "message": f"Không tìm thấy tiêu chí tuyển dụng cho vị trí '{position_title}'"
    }, ensure_ascii=False)


def execute_send_interview_notification(
    candidate_name: str,
    email: str,
    position_title: str,
    datetime_str: str,
    interviewer_name: str,
) -> str:
    """Mô phỏng gửi thư mời phỏng vấn sau khi Agent đã sàng lọc CV."""
    notification_id = f"INT-{candidate_name.replace(' ', '').upper()}-01"
    return json.dumps({
        "status": "SUCCESS",
        "notification_id": notification_id,
        "candidate_name": candidate_name,
        "email": email,
        "position_title": position_title,
        "datetime": datetime_str,
        "interviewer_name": interviewer_name,
        "message": (
            f"Đã gửi thư mời phỏng vấn vị trí {position_title} cho {candidate_name} "
            f"({email}) vào lúc {datetime_str} với {interviewer_name}."
        )
    }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "job_criteria_query": execute_job_criteria_query,
    "send_interview_notification": execute_send_interview_notification
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)

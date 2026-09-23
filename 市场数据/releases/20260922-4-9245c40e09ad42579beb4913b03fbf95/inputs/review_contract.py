"""Shared contracts for legacy v4 review artifacts.

Keep this module dependency-free: review_publish, review_pages and review_learning
all consume the same schema/version gate instead of carrying drifting copies.
"""

SCHEMA_VERSION = 1

TOTAL_AUDIT_KEYS = (
    "日期", "date", "路", "来源", "结论", "五路裁决", "总裁决",
    "检查四项", "发布门禁", "推演指派", "分歧裁决", "分歧点", "综合深挖",
    "认知迭代", "线索跟踪", "指派清单", "schema_version", "昨日战绩验收",
    "环境加权依据", "页面合同",
)

ROUTE_AUDIT_KEYS = (
    "日期", "date", "路", "来源", "判断", "荐票", "认知迭代",
    "认知迭代_条目", "深挖", "schema_version",
)


def validate_schema_version(obj, label="artifact"):
    """Return an error string, or None. Missing version remains legacy-compatible."""
    if "schema_version" in obj and (
        type(obj["schema_version"]) is not int or obj["schema_version"] != SCHEMA_VERSION
    ):
        return f"{label} schema_version unsupported"
    return None
